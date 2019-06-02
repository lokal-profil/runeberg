#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A runeberg.org article is a chapter, article or poem.

Per http://runeberg.org/admin/19990511.html#Indexing_Articles:
'Project Runeberg's text editions present each chapter of a novel as an HTML
file of its own. Poetry book are made up of poems, while journals and
dictionaries have articles rather than chapters. The word article has been
chosen as the common term for the parts of any electronic edition.'

An article might span several pages, and one page can contain several articles.
The sequence of pages of an article need not be continuous as e.g.
advertisement might interrupt it.

Note that some entries in Articles.lst are only used as Table of Content
headers, as such they should not be treated as proper articles.
"""
from bs4 import BeautifulSoup

from runeberg.page_range import PageRange


class Article(object):
    """An object representing a runeberg.org article."""

    # quick sketch
    def __init__(self, title, pages=None, html_name=None, disambig=None):
        """
        Initialise an Article.

        @param title: the article title
        @param pages: list of Pages or PageRanges which make up the article
        @param html_name: html file name used in runeberg.org
        @param disambig: disambiguator for none work-unique title
        """
        self.title = title  # the title, also used in headings on page
        self.pages = pages or []  # list of Pages or PageRanges
        self.html_name = html_name  # html file name used in runeberg.org
        self.disambig = disambig  # disambiguator for none work-unique title
        self.no_chapter_tag = None  # there is no matching chapter tag

    def first_page(self):
        """Return the first Page in the Article."""
        page = self.pages[0]
        if isinstance(page, PageRange):
            return page.first()
        return page

    def last_page(self):
        """Return the last Page in the Article."""
        page = self.pages[-1]
        if isinstance(page, PageRange):
            return page.last()
        return page

    def has_chapter_tag(self):
        """First page in the article has a matching chapter tag."""
        if self.is_toc_header() or self.no_chapter_tag:
            return False
        return True

    def is_toc_header(self):
        """
        Entry should only appear in the ToC.

        Some 'articles' are merely placeholders meant to inject an extra
        heading in a Table of Contents. E.g. 'B' indicating a change of letter
        in an alphabetic list of articles.
        """
        return not self.pages

    @property
    def clean_title(self):
        """
        Clean any html tags from the title.

        For Table of Contents purposes the name may include either empty
        <a> tags or various simpler formatting.
        """
        if not hasattr(self, '_clean_title'):
            soup = BeautifulSoup(self.title, features='html5lib')
            text = soup.get_text()
            self._clean_title = text.strip()
        return self._clean_title

    @property
    def uid(self):
        """Work-unique title/id for the article."""
        if self.disambig:
            return '{0} ({1})'.format(self.clean_title, self.disambig)
        else:
            return self.clean_title

    def __eq__(self, other):
        """Implement equality comparison."""
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented
