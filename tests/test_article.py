# -*- coding: utf-8 -*-
"""Unit tests for article."""
import unittest

from runeberg.article import Article
from runeberg.page import Page


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
