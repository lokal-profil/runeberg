# -*- coding: utf-8 -*-
"""Unit tests for __main__."""
import unittest
import unittest.mock as mock

from runeberg.__main__ import pager, prompt_choice


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

        self.input_bundle = (
            generator,
            {},  # filters
            self.mock_to_string,
            'some action',
            3  # per_page
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


class TestPromptChoice(unittest.TestCase):

    """Test the prompt_choice() method."""

    def setUp(self):

        patcher = mock.patch('builtins.input')
        self.mock_input = patcher.start()
        self.addCleanup(patcher.stop)

        self.input_bundle = (4, 'some action', 3)

    def test_prompt_choice_q(self):
        self.mock_input.return_value = 'q'
        with self.assertRaises(SystemExit) as cm:
            prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(cm.exception.code, 0)

    def test_prompt_choice_upper_q(self):
        self.mock_input.return_value = 'Q'
        with self.assertRaises(SystemExit) as cm:
            prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(cm.exception.code, 0)

    def test_prompt_choice_n(self):
        self.mock_input.return_value = 'n'
        result = prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertIsNone(result)

    def test_prompt_choice_upper_n(self):
        self.mock_input.return_value = 'N'
        result = prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertIsNone(result)

    def test_prompt_choice_n_not_allowed(self):
        self.mock_input.side_effect = ['n', 'N', '1']
        result = prompt_choice(4, 'some action', 0)

        self.assertEqual(self.mock_input.call_count, 3)
        self.assertEqual(result, 1)

    def test_prompt_choice_invalid(self):
        self.mock_input.side_effect = ['foo', 'f', 'n']
        result = prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 3)
        self.assertIsNone(result)

    def test_prompt_choice_invalid_int_zero(self):
        self.mock_input.side_effect = ['0', 'n']
        result = prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 2)
        self.assertIsNone(result)

    def test_prompt_choice_invalid_int_negative(self):
        self.mock_input.side_effect = ['-2', 'n']
        result = prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 2)
        self.assertIsNone(result)

    def test_prompt_choice_invalid_int_too_large(self):
        self.mock_input.side_effect = ['5', 'n']
        result = prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 2)
        self.assertIsNone(result)

    def test_prompt_choice_min_int(self):
        self.mock_input.return_value = '1'
        result = prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(result, 1)

    def test_prompt_choice_max_int(self):
        self.mock_input.return_value = '4'
        result = prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(result, 4)

    def test_prompt_choice_inbetween_int(self):
        self.mock_input.return_value = '3'
        result = prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(result, 3)
