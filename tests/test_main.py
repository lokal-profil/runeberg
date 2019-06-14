# -*- coding: utf-8 -*-
"""Unit tests for __main__."""
import unittest
import unittest.mock as mock

from runeberg.__main__ import pager


class TestPager(unittest.TestCase):

    """Test the pager() method."""

    def setUp(self):

        patcher = mock.patch('runeberg.__main__.prompt_choice')
        self.mock_prompt_choice = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_to_string = mock.Mock()
        self.mock_to_string.return_value = ''

        self.results = []

        def generator(**kargs):
            print('hello')
            for r in self.results:
                print('hello %s' % r)
                yield r

        self.per_page = 3
        self.input_bundle = (
            generator,
            {},
            self.mock_to_string,
            'some action',
            self.per_page
        )

    def test_pager_no_entries(self):
        with self.assertRaises(SystemExit) as cm:
            pager(*self.input_bundle)

        self.mock_to_string.assert_not_called()
        self.mock_prompt_choice.assert_not_called()
        self.assertEqual(cm.exception.code, 0)

    def test_pager_one_entry(self):
        self.results = ['one']
        self.mock_prompt_choice.return_value = 1

        pager(*self.input_bundle)
        self.mock_to_string.assert_called_once()
        self.mock_prompt_choice.assert_called_once()

    def test_pager_two_entries(self):
        self.results = ['one', 'two']
        self.mock_prompt_choice.return_value = 1

        result = pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 2)
        self.mock_prompt_choice.assert_called_once()
        self.assertEqual(result, 'one')

    def test_pager_exactly_per_page_entries(self):
        self.results = ['one', 'two', 'three']
        self.mock_prompt_choice.return_value = 1

        result = pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 3)
        self.mock_prompt_choice.assert_called_once()
        self.assertEqual(result, 'one')

    def test_pager_exactly_per_page_entries_request_next(self):
        self.results = ['one', 'two', 'three']
        self.mock_prompt_choice.side_effect = [None, 1]

        result = pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 3)
        self.assertEqual(self.mock_prompt_choice.call_count, 2)
        self.assertEqual(result, 'one')

    def test_pager_more_than_per_page_entries(self):
        self.results = ['one', 'two', 'three', 'four']
        self.mock_prompt_choice.side_effect = [None, 4]

        result = pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 4)
        self.assertEqual(self.mock_prompt_choice.call_count, 2)
        self.assertEqual(result, 'four')

    def test_pager_more_than_per_page_entries_select_on_first_prompt(self):
        self.results = ['one', 'two', 'three', 'four']
        self.mock_prompt_choice.side_effect = [1, 2]

        result = pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 3)
        self.assertEqual(self.mock_prompt_choice.call_count, 1)
        self.assertEqual(result, 'one')

    # you only reach
    def test_pager_more_than_per_page_entries_select_on_first_prompt(self):
        self.results = ['one', 'two', 'three', 'four']
        self.mock_prompt_choice.side_effect = [1, 2]

        result = pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 3)
        self.assertEqual(self.mock_prompt_choice.call_count, 1)
        self.assertEqual(result, 'one')
