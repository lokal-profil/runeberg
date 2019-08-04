# -*- coding: utf-8 -*-
"""Unit tests for article."""
import unittest
import unittest.mock as mock

from runeberg.article import Article
from runeberg.page import Page
from runeberg.page_range import PageRange


class TestIsTocHeader(unittest.TestCase):

    """Test the is_toc_header() method."""

    def setUp(self):
        page = Page('001')
        self.article = Article('Chapter 1', [page])

    def test_is_toc_header_false(self):
        self.assertEqual(self.article.is_toc_header(), False)

    def test_is_toc_header_true(self):
        self.article.pages = []
        self.assertEqual(self.article.is_toc_header(), True)


class TestCleanTitle(unittest.TestCase):

    """Test the clean_title() method."""

    def test_clean_title_no_html(self):
        article = Article('Genesis')
        self.assertEqual(article.clean_title, 'Genesis')

    def test_clean_title_with_html(self):
        article = Article('<a name="toca" ></a><b>A.</b>')
        self.assertEqual(article.clean_title, 'A.')


class TestUid(unittest.TestCase):

    """Test the is_toc_header() method."""

    def setUp(self):
        self.article = Article('Genesis')
        self.article.disambig = None

    def test_uid_no_disambig(self):
        self.assertEqual(self.article.uid, 'Genesis')

    def test_uid_with_disambig(self):
        self.article.disambig = 2
        self.assertEqual(self.article.uid, 'Genesis (2)')


class TestText(unittest.TestCase):

    def setUp(self):
        self.article = Article('Genesis')
        # cannot get instance attribute mocking to work for page
        self.page = Page('page_1', text='This is the page text.')
        self.page_range = PageRange([])

        patcher = mock.patch('runeberg.page_range.PageRange.text',
                             new_callable=mock.PropertyMock)
        self.mock_page_range_text = patcher.start()
        self.mock_page_range_text.return_value = 'This is the page_range text.'
        self.addCleanup(patcher.stop)

    def test_text_no_pages(self):
        self.assertEqual(self.article.text, '')

    def test_text_page(self):
        self.article.pages = [self.page]
        self.assertEqual(self.article.text, 'This is the page text.')

    def test_text_page_range(self):
        self.article.pages = [self.page_range]
        self.assertEqual(self.article.text, 'This is the page_range text.')

    def test_text_multiple_pages(self):
        self.article.pages = [self.page, self.page_range]
        self.assertEqual(
            self.article.text,
            'This is the page text.\nThis is the page_range text.')
