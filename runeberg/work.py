#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A runeberg.org work represents a digitised book.

This most often corresponds to an edition in e.g. Wikidata terminology.

@TODO: load some key metadata as attributes, e.g. title and (co)author
    (which requires a lookup of the key so parsing of a.lst)
"""
import os
from collections import Counter, OrderedDict
from itertools import takewhile
from shlex import quote
from shutil import which  # used for djvu conversion
from subprocess import DEVNULL, run  # used for djvu conversion

from tqdm import tqdm

from runeberg.article import Article
from runeberg.download import DATA_DIR, IMG_DIR, SITE, UNZIP_SUBDIR
from runeberg.lst_file import LstFile
from runeberg.page import Page
from runeberg.page_range import PageRange
from runeberg.person import Person

IMAGE_TYPES = ('.tif', '.jpg')


class Work(object):
    """An object representing a runeberg.org work."""

    # @TODO: consider adding more params
    def __init__(self, uid):
        """
        Initialise a Work.

        @param uid: unique work identifier on runeberg.org
        """
        self.uid = uid  # work identifier on runeberg.org
        self.pages = PageRange()  # the included pages
        self.articles = OrderedDict()  # the included articles
        self.metadata = {}  # a verbatim copy of the runeberg.org metadata
        self.identifiers = {}  # identifiers for the work in external sources
        self.people = {}  # people involved with the work
        self.djvu = None  # djvu file of the whole work
        self.image_type = None  # the default file extension of the image files

        # @TODO: something recording the date when runeberg was downloaded

    @staticmethod
    def from_files(uid, base_path=None, known_people=None, img_dir=None):
        """
        Create an Work from the downloaded, unzipped files.

        @param base_path: path to the directory containing the unzipped files.
            Overrides the default {cwd}/DATA_DIR/{uid}/UNZIP_SUBDIR
        @param known_people: dict of Person objects from which author, editor
            and translator roles are matched.
        @param img_dir: the name given to the image sub-directory. Defaults to
            IMG_DIR.
        """
        work = Work(uid)
        base_path = base_path or os.path.join(
            os.getcwd(), DATA_DIR, uid, UNZIP_SUBDIR)
        img_dir = img_dir or IMG_DIR
        work.determine_image_file_type(base_path, img_dir)
        chapters = work.load_pages(base_path)
        work.load_articles(base_path, chapters)
        work.load_metadata(base_path)
        work.identifiers = work.parse_marc()
        work.parse_people(known_people)
        return work

    def runeberg_url(self):
        """Return the base url on runeberg.org."""
        return '{0}/{1}/'.format(SITE, self.uid)

    def determine_image_file_type(self, base_path, img_dir):
        """
        Determine the file type of the images of the scanned pages.

        Will stop after encountering the first recognised image file type.

        @raises NoImagesError: if no files are encountered
        @raises UnrecognisedImageTypeError: if no recognised image file types
            are encountered.
        @param base_path: The path to the unzipped directory.
        @param img_dir: the image subdirectory
        """
        found_types = set()
        img_dir_path = os.path.join(base_path, img_dir)
        with os.scandir(img_dir_path) as it:
            for entry in it:
                if not entry.name.startswith('.') and entry.is_file():
                    ext = os.path.splitext(entry)[1]
                    if ext in IMAGE_TYPES:
                        self.image_type = ext
                        return
                    found_types.add(ext)
        if not found_types:
            raise NoImagesError(img_dir_path)
        raise UnrecognisedImageTypeError(found_types)

    def load_pages(self, base_path):
        """
        Populate self.pages.

        This is done using the Pages.lst file and the contents of the Pages
        and Images directories.

        @param base_path: The path to the unzipped directory.
        @return: Counter of all chapter names
        """
        pages = LstFile.from_file(os.path.join(base_path, 'Pages.lst'))
        whole_page_ok = LstFile.from_file(
            os.path.join(base_path, 'Pages', 'whole-page-ok.lst'))
        ok_pages = [i[0] for i in whole_page_ok.data]

        chapters = Counter()
        for uid, label in pages.data:
            page = Page.from_path(
                base_path, uid, self.image_type, label, uid in ok_pages)
            chapters.update(page.get_chapters())
            self.pages[uid] = page
        return chapters

    @staticmethod
    def setup_disambiguation_counter(chapters):
        """Create a Counter of non-unique chapter titles."""
        return Counter(
            [key for key, count in
             takewhile(lambda key_count: key_count[1] > 1,
                       chapters.most_common())])

    # @TODO: Implement require_unique_titles=False
    #   note that without requiring uniqueness self.articles must be a list...
    #   not necessarilly a problem though since we don't seem to use the index
    def load_articles(self, base_path, chapters, require_unique_titles=True,
                      reconcile_chapter_tags=True):
        """
        Populate self.articles.

        This is done using the Articles.lst file.

        This method allows the enforcement of two features which are not native
        to Runeberg.org.

        With `require_unique_titles=True` every article/chapter must have a
        unique name/title. When needed disambiguators will be added to article
        names. When disambiguators cannot be added an error is raised.

        With `reconcile_chapter_tags=True` every chapter tag, encountered when
        loading the pages, must correspond to an entry in Articles.lst. Entries
        in Articles.lst are still allowed to not have a counterpart in the
        chapter tags.

        @param base_path: The path to the unzipped directory.
        @param chapters: Counter of chapter tags encountered when loading the
            pages.
        @param require_unique_titles: Forces chapter titles to be unique.
        @param reconcile_chapter_tags: Forces reconciliation of article titles
            and encountered chapter tags.
        @return: self.articles
        """
        if require_unique_titles is False:
            raise NotImplementedError(
                'Sorry uniqueness is not optional for now')

        articles = LstFile.from_file(os.path.join(base_path, 'Articles.lst'))
        disambiguation_counter = Work.setup_disambiguation_counter(chapters)
        for html_name, title, page_range in articles.data:
            page_list = self.parse_range(page_range)
            if title in self.articles:
                raise DisambiguationError(title)
            if title in disambiguation_counter:
                article = Article(title, page_list, html_name,
                                  disambiguation_counter[title])
                page = article.first_page()
                page.rename_chapter(title, article.uid)
                disambiguation_counter[title] += 1
            else:
                article = Article(title, page_list, html_name)

            if not article.is_toc_header():
                if title not in article.first_page().get_chapters():
                    article.no_chapter_tag = True
                else:
                    chapters[title] -= 1
            self.articles[article.uid] = article

        # Do a reconciliation checks
        if reconcile_chapter_tags:
            if any(counter != 0 for counter in chapters.values()):
                raise ReconciliationError(chapters, self.articles)

        return self.articles

    # @TODO: move to staticmethod in article.py?
    def parse_range(self, page_range):
        """Parse the range of pages provided in Articles.lst."""
        page_list = []
        for entry in page_range.split(' '):
            if not entry.strip():
                continue
            if '-' in entry:
                first, _, last = entry.partition('-')
                page_list.append(self.pages.get_range(first, last))
            else:
                page_list.append(self.pages.get(entry))
        return page_list

    @staticmethod
    def read_metadata(base_path):
        """
        Read the metadata file and returns the lines.

        @param base_path: The path to the unzipped directory.
        @return: list of lines (incl. comments)
        """
        file_path = os.path.join(base_path, 'Metadata')
        with open(file_path) as f:
            return f.read().split('\n')  # unlike readlines() this trims the \n

    # @TODO: consider triggering parse_marc here
    def load_metadata(self, base_path):
        """
        Load the metadata, overwriting any previous value of that attribute.

        All the metadata is loaded into the metadata attribute, additionally
        some metadata fields are further processed.

        @param base_path: The path to the unzipped directory.
        @return: dict of metadata entries
        """
        metadata = {}
        data = Work.read_metadata(base_path)

        for line in data:
            if not line or line.startswith('#'):
                continue
            field, _, value = line.partition(':')
            if field in metadata.keys():
                raise NotImplementedError('Need to handle non-unique metadata')
            if not _:
                raise ValueError(
                    'The following metadata line is invalid: {}'.format(line))
            metadata[field] = value.lstrip()

        # sanity checks
        if metadata.get('CHARSET') != 'utf-8':
            raise NotImplementedError(
                'Need to handle handle non-utf8 works. Found {0}'.format(
                    metadata.get('CHARSET')))
        if metadata.get('TITLEKEY') != self.uid:
            raise ValueError(  # @TODO: appropriate Exception type?
                'Metadata work identifier does not match the provided '
                'identifier (provided: "{0}", found: "{1}")'.format(
                    self.uid, metadata.get('TITLEKEY')))
        self.metadata = metadata
        return metadata

    def parse_marc(self):
        """
        Parse the multivalued MARC metadata entry.

        @return dict of identifiers
        """
        data = self.metadata.get('MARC')
        identifiers = {}
        if data:
            for entry in data.split(' '):
                field, _, value = entry.partition(':')
                if field in identifiers.keys():
                    raise NotImplementedError(
                        'Need to handle non-unique identifiers')
                identifiers[field] = value
        return identifiers

    def parse_people(self, known_people=None):
        """
        Look up persons mentioned in metadata in the author file.

        If not provided the author file will be downloaded.
        """
        if not known_people:
            known_people = Person.load_people(DATA_DIR)
        people_fields = ('author', 'coauthor', 'translator')
        for field in people_fields:
            key = '{0}KEY'.format(field.upper())
            if self.metadata.get(key):
                uids = self.metadata.get(key)
                self.people[field] = [known_people[uid]
                                      for uid in uids.split(' ')]

    def to_djvu(self, silent=True):
        """
        Convert all images to a single DjVu file.

        Assumes only black-white pages and requires DjVuLibre.

        @param silent: silence the very chatty stderr output
        @type silent: Bool
        @return: path to djvu file
        """
        if self.djvu is not None:
            # checks if already converted
            # @TODO: notify the user somehow
            return self.djvu
        if not Work.can_djvu():
            # @TODO: should find a more suitable exception
            raise Exception('Need DjVuLibre to convert to djvu')
        base_path = None
        book_djvu = None
        tmp_djvu = 'tmp.djvu'
        stderr = DEVNULL if silent else None
        for i, page in tqdm(enumerate(self.pages.values(), 1),
                            total=len(self.pages)):
            in_file = quote(page.image)

            # @TODO: can try "capture_output=True" if python is bumped to 3.7
            # use page file type in case original image has been replaced
            if page.image_file_type == '.tif':
                # cjb2 to convert single tif to djvu
                run(['cjb2', '-clean', in_file, tmp_djvu],
                    check=True, stderr=stderr)
            elif page.image_file_type == '.jpg':
                run(['c44', '-crcbfull', in_file, tmp_djvu],
                    check=True, stderr=stderr)
            else:
                raise NotImplementedError(
                    'At the moment only .tif and .jpg images can be converted '
                    'to DjVu')

            if i == 1:
                base_path = os.path.dirname(page.image)
                book_djvu = os.path.join(base_path, 'book.djvu')
                # djvm to create multi-page file from first page
                run(['djvm', '-c', book_djvu, tmp_djvu],
                    check=True, stderr=stderr)
            else:
                # djvm to insert page at end of multi-page file
                run(['djvm', '-i', book_djvu, tmp_djvu],
                    check=True, stderr=stderr)
            # remove is kept inside the loop to ensure cjb2 failure doesn't
            # result in a duplicated page
            os.remove(tmp_djvu)
            page.image_no = i
        self.djvu = book_djvu
        return book_djvu

    # @TODO: possibly move to utils or outside Work class
    @staticmethod
    def can_djvu():
        """
        Check if DjVu files can be created.

        Check whether DjVuLibre is installed, on PATH and marked as
        executable.
        """
        return (which('djvm') is not None and which('cjb2') is not None)


class NoImagesError(Exception):
    """Error when no images were found for the pages of the work."""

    def __init__(self, img_dir_path):
        """Initialise a NoImagesError."""
        msg = (
            'Could not detect any images for this work. Are you sure you '
            'provided the correct image subdirectory ({}) and that this is '
            'not a volumed work?'.format(img_dir_path))
        super().__init__(msg)


class UnrecognisedImageTypeError(Exception):
    """Error in trying to determine the image file type."""

    def __init__(self, encountered):
        """Initialise a UnrecognisedImageTypeError."""
        encountered = sorted(list(encountered))  # make deterministic
        msg = (
            'The encountered images do not seem to be of a recognised image '
            'file type.\n'
            'Recognised image file types are: {0}\n'
            'Encountered file types: {1}'.format(
                ', '.join(IMAGE_TYPES), ', '.join(encountered)))
        super().__init__(msg)


class DisambiguationError(Exception):
    """Error in disambiguating non-unique article titles."""

    def __init__(self, title):
        """Initialise a DisambiguationError."""
        msg = (
            'Encountered a duplicate article name ("{0}") which could '
            'not be automatically disambiguated. This is likely due '
            'to an error in the Articles.lst file which must be '
            'manually fixed. Encountered duplicates:\n'.format(
                '\n'.join(title)))
        super().__init__(msg)


class ReconciliationError(Exception):
    """Error in matching on-page chapter tags to articles in Articles.lst."""

    def __init__(self, chapters, articles):
        """Initialise a ReconciliationError."""
        self.unclaimed_chapters = ['{0}: {1} time(s)'.format(key, count)
                                   for key, count in chapters.most_common()
                                   if count != 0]
        self.no_tag_articles = ['{0}: page(s) {1}'.format(article.clean_title,
                                                          article.pages[0])
                                for article in articles.values()
                                if article.no_chapter_tag]

        msg = (
            'Encountered article names in the ocr:ed text which could not '
            'be found in Articles.lst. This is most often caused by typos '
            'or slight variations. These need to be manually reconciled '
            'before going forward. Note that not all articles need a '
            'corresponding chapter tag, but all chapter tags should '
            'correspond to an article.\n\n'
            '==Unclaimed chapter tags==\n'
            '{0}\n\n'
            '==Articles without chapter tags==\n'
            '{1}\n'.format('\n'.join(self.unclaimed_chapters),
                           '\n'.join(self.no_tag_articles)))
        super().__init__(msg)
