#!/usr/bin/python
# -*- coding: utf-8 -*-
"""A runeberg.org page is a single digitized page of a work."""
import os
import warnings

from bs4 import BeautifulSoup

from runeberg.download import IMG_DIR


class Page(object):
    """An object representing a runeberg.org page."""

    BLANK_LABELS = ('blank', '(blank)')  # labels known to indicate blank page
    DEFAULT_BLANK = '<blank>'  # default label to use for blank pages

    def __init__(self, uid, label=None, image=None, ocr=None, proofread=None):
        """
        Initialise a Page.

        @param uid: the identifier of the page, ordinarily the zero-padded
            ordinal number of the page.
        @param label: the real printable label of the page, ordinarily the page
            number.
        @param image: path to the image of the page
        @param ocr: ocr:ed (and potentially proofread) text of the page
        @param proofread: whether the page has been fully proofread.
        """
        self.uid = uid  # unique identifier of the page (often a padded number)
        self.label = label or ''  # what the numbering on the actual page is
        self.image = image or ''  # path to the image
        self.image_no = None  # page in djvu file on which the image appears
        self.ocr = ocr or ''  # ocr:ed text of the page
        self.is_proofread = proofread  # bool or None in the case of blank page
        self.set_blank()

    def __str__(self):
        """Represent the Page as a string."""
        return self.uid

    @property
    def image_file_type(self):
        """Return the file extension of the image file."""
        if not self.image:
            return None
        return os.path.splitext(self.image)[1]

    def set_blank(self, default_label=None):
        """
        Set the blank proofread status based on page label.

        Also changes the page label to a default_label.

        @param default_label: the default label to use for blank pages.
        """
        default_label = default_label or self.DEFAULT_BLANK
        if self.label in self.BLANK_LABELS:
            self.is_proofread = None
            self.label = default_label

    def check_blank(self):
        """Sanity check blank pages and blank page candidates."""
        if self.is_proofread is None and self.ocr.strip() != '':
            warnings.warn(
                '{0} ({1}) was labelled "blank" but ocr is not empty. Either '
                'clear out the ocr text or set `is_proofread=False`'.format(
                    self.uid, self.label),
                UserWarning)
        elif self.is_proofread and self.ocr.strip() == '':
            warnings.warn(
                '{0} ({1}) was labelled as proofread but is blank. Either '
                're-add the ocr text or set `is_proofread=None`'.format(
                    self.uid, self.label),
                UserWarning)
        elif self.is_proofread == False and self.ocr.strip() == '':
            warnings.warn(
                '{0} ({1}) might be blank. Check the image and if truly blank '
                'set `is_proofread=None`'.format(
                    self.uid, self.label),
                UserWarning)

    @staticmethod
    def from_path(base_path, uid, image_type, label, whole_page_ok):
        """
        Create a page from the path to the unzipped files and a uid.

        @param base_path: the file path to the directory containing the
            unzipped files.
        @param uid: the identifier of the page, ordinarily the zero-padded
            ordinal number of the page.
        @param image_type: the expected file extension of the scanned image.
        @param label: the real printable label of the page, ordinarily the page
            number.
        @param whole_page_ok: whether the whole page has been proofread
        """
        img_path = os.path.join(
            base_path, IMG_DIR, '{0}{1}'.format(uid, image_type))
        if not os.path.isfile(img_path):
            raise ValueError(
                '{} was provided as the image for "{}" but no such image '
                'exists'.format(img_path, uid))
        text_path = os.path.join(base_path, 'Pages', '{}.txt'.format(uid))
        with open(text_path) as f:
            text = f.read()
        page = Page(uid, label, img_path, text, whole_page_ok)
        page.check_blank()
        return page

    # @TODO: might change to @property, and rename self.chapters
    def get_chapters(self):
        """Extract all chapter names on page."""
        if not hasattr(self, '_chapters'):
            soup = BeautifulSoup(self.ocr, features='html5lib')
            self._chapters = [chapter.get('name')
                              for chapter in soup.find_all('chapter')]
            if any(not chapter for chapter in self._chapters):
                raise ValueError(
                    'Encountered a blank/missing chapter name on page '
                    '{0} ({1})'.format(self.uid, self.label))
        return self._chapters

    def rename_chapter(self, old_name, new_name):
        """Rename the first occurrence of a chapter."""
        base_str = '<chapter name="{}">'
        self.ocr = self.ocr.replace(
            base_str.format(old_name),
            base_str.format(new_name),
            1)
