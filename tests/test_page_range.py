# -*- coding: utf-8 -*-
"""Unit tests for page_range."""
import unittest

from runeberg.page_range import PageRange


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.pages = PageRange([
            ('one', 3),
            ('two', 2),
            ('three', 1)])


class TestIndex(BaseTest):

    """Test the index() method."""

    def test_index_empty(self):
        with self.assertRaises(ValueError):
            self.pages.index()

    def test_index_single(self):
        self.assertEqual(self.pages.index('two'), 1)

    def test_index_single_missing(self):
        with self.assertRaises(ValueError):
            self.pages.index('four')

    def test_index_multiple(self):
        self.assertEqual(self.pages.index('three', 'two'), [2, 1])

    def test_index_multiplr_missing(self):
        with self.assertRaises(ValueError):
            self.pages.index('two', 'four')


class TestStr(BaseTest):

    """Test the __str__() method."""

    def test_str_range(self):
        self.assertEqual(str(self.pages), 'one-three')

    def test_str_pair(self):
        del self.pages['three']
        self.assertEqual(str(self.pages), 'one-two')

    def test_str_single(self):
        del self.pages['three']
        del self.pages['two']
        self.assertEqual(str(self.pages), 'one')

    def test_str_empty(self):
        self.pages = PageRange([])
        self.assertEqual(str(self.pages), '')


class TestSlice(BaseTest):

    """Test the slice() method."""

    def test_slice_empty(self):
        self.assertEqual(self.pages.slice(), self.pages)

    def test_slice_start_stop(self):
        self.assertEqual(
            self.pages.slice(1, 2),
            PageRange([('two', 2)]))

    def test_slice_no_start(self):
        self.assertEqual(
            self.pages.slice(None, 2),
            PageRange([
                ('one', 3),
                ('two', 2)]))

    def test_slice_no_stop(self):
        self.assertEqual(
            self.pages.slice(1, ),
            PageRange([
                ('two', 2),
                ('three', 1)]))

    def test_slice_step(self):
        self.assertEqual(
            self.pages.slice(None, None, 2),
            PageRange([
                ('one', 3),
                ('three', 1)]))


class TestFirst(BaseTest):

    """Test the first() method."""

    def test_first_empty(self):
        self.pages = PageRange([])
        self.assertEqual(self.pages.first(), None)

    def test_first(self):
        self.assertEqual(self.pages.first(), 3)


class TestLast(BaseTest):

    """Test the last() method."""

    def test_last_empty(self):
        self.pages = PageRange([])
        self.assertEqual(self.pages.last(), None)

    def test_last(self):
        self.assertEqual(self.pages.last(), 1)
