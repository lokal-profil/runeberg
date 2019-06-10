# -*- coding: utf-8 -*-
"""Unit tests for page."""
import unittest

from runeberg.page import Page


class TestStr(unittest.TestCase):

    """Test the __str__() method."""

    def setUp(self):
        self.page = Page('0001')

    def test_str_range(self):
        self.assertEqual(str(self.page), '0001')


class TestGetChapters(unittest.TestCase):

    """Test the get_chapters() method."""

    def setUp(self):
        self.page = Page('0001')

    def test_get_chapters_empty(self):
        self.page.ocr = ''
        self.assertEqual(self.page.get_chapters(), [])

    def test_get_chapters_no_chapters(self):
        self.page.ocr = (
            'row 1\n'
            'row 2\n'
            'row3'
        )
        self.assertEqual(self.page.get_chapters(), [])

    def test_get_chapters_unique_chapters(self):
        self.page.ocr = (
            'row 1\n'
            'pre<chapter name="chp1">post\n'
            'row 2\n'
            'Pre<chapter name="chp2">Post\n'
            'row3'
        )
        expected = ['chp1', 'chp2']
        self.assertEqual(self.page.get_chapters(), expected)

    def test_get_chapters_non_unique_chapters(self):
        self.page.ocr = (
            'row 1\n'
            'pre<chapter name="chp1">post\n'
            'row 2\n'
            'Pre<chapter name="chp2">Post\n'
            'row3\n'
            'pre<chapter name="chp1">post\n'
        )
        expected = ['chp1', 'chp2', 'chp1']
        self.assertEqual(self.page.get_chapters(), expected)

    def test_get_chapters_missing_attribute(self):
        self.page.ocr = (
            'row 1\n'
            'pre<chapter>post\n'
            'row 2\n'
            'Pre<chapter name="chp2">Post\n'
        )
        with self.assertRaises(ValueError):
            self.page.get_chapters()


class TestRenameChapter(unittest.TestCase):

    """Test the rename_chapter() method."""

    def setUp(self):
        text = (
            'row 1\n'
            'row 2\n'
            'row3'
        )
        self.page = Page('0001', ocr=text)

    def test_rename_chapter_no_chapter(self):
        self.page.ocr = (
            'row 1\n'
            'row 2\n'
            'row3'
        )
        expected = (
            'row 1\n'
            'row 2\n'
            'row3'
        )
        self.page.rename_chapter('chp1', 'foo')
        self.assertEqual(self.page.ocr, expected)

    def test_rename_chapter_single_match(self):
        self.page.ocr = (
            'row 1\n'
            'pre<chapter name="chp1">post\n'
            'row 2\n'
            'Pre<chapter name="chp2">Post\n'
            'row3'
        )
        expected = (
            'row 1\n'
            'pre<chapter name="chp1">post\n'
            'row 2\n'
            'Pre<chapter name="foo">Post\n'
            'row3'
        )
        self.page.rename_chapter('chp2', 'foo')
        self.assertEqual(self.page.ocr, expected)

    def test_rename_chapter_multiple_matches(self):
        self.page.ocr = (
            'row 1\n'
            'pre<chapter name="chp1">post\n'
            'row 2\n'
            'Pre<chapter name="chp2">Post\n'
            'row3\n'
            'pre<chapter name="chp1">post\n'
        )
        expected = (
            'row 1\n'
            'pre<chapter name="foo">post\n'
            'row 2\n'
            'Pre<chapter name="chp2">Post\n'
            'row3\n'
            'pre<chapter name="chp1">post\n'
        )
        self.page.rename_chapter('chp1', 'foo')
        self.assertEqual(self.page.ocr, expected)


class TestCheckBlank(unittest.TestCase):

    """Test the check_blank() method."""

    def setUp(self):
        text = (
            'row 1\n'
            'row 2\n'
            'row3'
        )
        self.page = Page('0001', ocr=text)

    @unittest.expectedFailure  # hack to assert not Warns
    def test_check_blank_empty_and_blank(self):
        self.page.ocr = ''
        self.page.is_proofread = None
        with self.assertWarnsRegex(UserWarning, r'is blank'):
            self.page.check_blank()

    def test_check_blank_empty_and_proofread(self):
        self.page.ocr = ''
        self.page.is_proofread = True
        with self.assertWarnsRegex(UserWarning, r'is blank'):
            self.page.check_blank()

    def test_check_blank_empty_and_not_proofread(self):
        self.page.ocr = ''
        self.page.is_proofread = False
        with self.assertWarnsRegex(UserWarning, r'might be blank'):
            self.page.check_blank()

    def test_check_blank_not_empty_and_blank(self):
        self.page.is_proofread = None
        with self.assertWarnsRegex(UserWarning, r'is not empty'):
            self.page.check_blank()

    @unittest.expectedFailure
    def test_check_blank_not_empty_and_proofread(self):
        # How to assert not Warned
        self.page.is_proofread = True
        with self.assertWarnsRegex(UserWarning, r'is not empty'):
            self.page.check_blank()

    @unittest.expectedFailure
    def test_check_blank_not_empty_and_not_proofread(self):
        # How to assert not Warned
        self.page.is_proofread = False
        with self.assertWarnsRegex(UserWarning, r'is not empty'):
            self.page.check_blank()
