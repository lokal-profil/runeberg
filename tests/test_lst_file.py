# -*- coding: utf-8 -*-
"""Unit tests for lst file."""
import unittest
import unittest.mock as mock
from collections import namedtuple

from runeberg.lst_file import LstFile


class LstTestCase(unittest.TestCase):
    """Shared set-up for tests."""

    def setUp(self):
        """Set up a lst_file instance."""
        self.lst_file = LstFile()


class TestLen(LstTestCase):
    """Test the __len__() method."""

    def test_len_no_data(self):
        """Test length of LstFile without data."""
        self.lst_file.data = []
        self.assertEquals(len(self.lst_file), 0)

    def test_len_no_data_but_comments(self):
        """Test length of LstFile without data but with comments."""
        self.lst_file.data = []
        self.lst_file.comments = ['a comment']
        self.assertEquals(len(self.lst_file), 0)

    def test_len_with_data(self):
        """Test length of LstFile with data."""
        self.lst_file.data = [i for i in range(10)]
        self.lst_file.comments = ['a comment']
        self.assertEquals(len(self.lst_file), 10)


class TestColumns(LstTestCase):
    """Test the columns method."""

    def test_columns_no_data(self):
        """Test columns of LstFile without data."""
        self.lst_file.data = []
        with self.assertRaises(ValueError):
            self.lst_file.columns

    def test_columns_single_entry(self):
        """Test columns of LstFile with a single data entry."""
        self.lst_file.data = [(1, 2, 3)]
        self.assertEquals(self.lst_file.columns, 3)

    def test_columns_multiple_entries(self):
        """Test columns of LstFile with a data entries of various lengths."""
        self.lst_file.data = [
            (1, 2, 3),
            (1, 2, 3, 4),
            (1, 2)
        ]
        self.assertEquals(self.lst_file.columns, 4)

    def test_columns_func_with_len(self):
        """Test columns of LstFile with _func method specifying length."""
        Test = namedtuple('Test', 'a b c d')
        self.lst_file._func = Test
        self.lst_file.data = [Test(1, 2, 3, 4)]
        self.assertEquals(self.lst_file.columns, 4)

    def test_columns_func_without_len(self):
        """Test columns of LstFile with _func method not specifying length."""
        Test = print  # noqa
        self.lst_file._func = Test
        self.lst_file.data = [Test(1, 2, 3, 4)]
        with self.assertRaises(NotImplementedError):
            self.lst_file.columns


class TestParseLine(LstTestCase):
    """Test the parse_line() method."""

    def assert_line(self, line, data, comments):
        """Combine asserts for both data and comments."""
        self.lst_file.parse_line(line)
        self.assertEquals(
            self.lst_file.data, data)
        self.assertEquals(
            self.lst_file.comments, comments)

    # likely not the desired result
    def test_parse_line_no_data(self):
        """Test parsing an empty line."""
        line = ''
        self.assert_line(line, [], [])

    def test_parse_line_data_line(self):
        """Test parsing a line with data."""
        line = '1858|1915|Aalberg||#|aalbeida\n'
        self.assert_line(
            line,
            [('1858', '1915', 'Aalberg', '', '#', 'aalbeida')],
            [])

    def test_parse_line_comment_line(self):
        """Test parsing a line with comment."""
        line = '# authors/a.lst http://runeberg.org/authors/\n'
        self.assert_line(
            line,
            [],
            ['authors/a.lst http://runeberg.org/authors/'])

    def test_parse_line_empty_comment_line(self):
        """Test parsing a line with an empty comment."""
        line = '# \n'
        self.assert_line(line, [], [])


class TestParseLineFunc(unittest.TestCase):
    """Test the parse_line() method with _func."""

    def setUp(self):
        """Set up a lst_file instance."""
        self.func = namedtuple('Test', 'a b c d e f')
        self.lst_file = LstFile(self.func)

    def assert_line(self, line, data, comments):
        """Combine asserts for both data and comments."""
        self.lst_file.parse_line(line)
        self.assertEquals(
            self.lst_file.data, data)
        self.assertEquals(
            self.lst_file.comments, comments)

    # likely not the desired result
    def test_parse_line_no_data(self):
        """Test parsing an empty line."""
        line = ''
        self.assert_line(line, [], [])

    def test_parse_line_data_line(self):
        """Test parsing a line with data."""
        line = '1858|1915|Aalberg||#|aalbeida\n'
        self.assert_line(
            line,
            [self.func('1858', '1915', 'Aalberg', '', '#', 'aalbeida')],
            [])

    def test_parse_line_comment_line(self):
        """Test parsing a line with comment."""
        line = '# authors/a.lst http://runeberg.org/authors/\n'
        self.assert_line(
            line,
            [],
            ['authors/a.lst http://runeberg.org/authors/'])

    def test_parse_line_empty_comment_line(self):
        """Test parsing a line with an empty comment."""
        line = '# \n'
        self.assert_line(line, [], [])

    def test_parse_line_with_invalid_data(self):
        """Test parsing a line with the wrong number of columns."""
        line = '1858|1915|Aalberg||#\n'
        with self.assertRaises(TypeError):
            self.lst_file.parse_line(line)


class TestFromStream(unittest.TestCase):
    """Test from_stream() method."""

    def setUp(self):
        self.text = (
            'a line|some values\n'
            '# a comment\n'
            'another line|some more values'
        )
        self.file_name = 'foo.lst'

        patcher = mock.patch('runeberg.lst_file.LstFile.parse_line')
        self.mock_parse_line = patcher.start()
        self.addCleanup(patcher.stop)

    def test_from_file_non_empty_file(self):
        result = LstFile.from_stream(self.text, self.file_name)
        self.assertEqual(result.name, 'foo.lst')
        self.assertEqual(self.mock_parse_line.call_count, 3)

    def test_from_file_non_empty_file_no_filename(self):
        result = LstFile.from_stream(self.text)
        self.assertEqual(result.name, '')
        self.assertEqual(self.mock_parse_line.call_count, 3)

    def test_from_file_non_empty_file_w_func(self):
        result = LstFile.from_stream(self.text, self.file_name, func=dict)
        self.assertEqual(result.name, 'foo.lst')
        self.assertEqual(result._func, dict)
        self.assertEqual(self.mock_parse_line.call_count, 3)
