# -*- coding: utf-8 -*-
"""Unit tests for __main__."""
import argparse
import unittest
import unittest.mock as mock
from collections import Sized, namedtuple

import runeberg.__main__ as main


class BaseTestCase(unittest.TestCase):
    """Add custom assert to TestCase."""

    # from pywikibot.tests.aspects
    def assert_length(self, seq, other, msg=None):
        """Verify that a sequence expr has the length of other."""
        # the other parameter may be given as a sequence too
        self.assertIsInstance(
            seq, Sized, 'seq argument is not a Sized class containing __len__')
        first_len = len(seq)
        try:
            second_len = len(other)
        except TypeError:
            second_len = other

        if first_len != second_len:
            msg = self._formatMessage(
                msg, 'len(%s) != %s' % (repr(seq), second_len))
            self.fail(msg)


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
            main.pager(*self.input_bundle)

        self.mock_to_string.assert_not_called()
        self.mock_prompt_choice.assert_not_called()
        self.assertEqual(cm.exception.code, 0)

    def test_pager_one_entry(self):
        self.results = ['one']
        self.mock_prompt_choice.return_value = 1

        result = main.pager(*self.input_bundle)
        self.mock_to_string.assert_called_once()
        self.mock_prompt_choice.assert_called_once()
        self.assertEqual(result, 'one')

    def test_pager_two_entries(self):
        self.results = ['one', 'two']
        self.mock_prompt_choice.return_value = 1

        result = main.pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 2)
        self.mock_prompt_choice.assert_called_once()
        self.assertEqual(result, 'one')

    def test_pager_exactly_per_page_entries(self):
        self.results = ['one', 'two', 'three']
        self.mock_prompt_choice.return_value = 1

        result = main.pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 3)
        self.mock_prompt_choice.assert_called_once()
        self.assertEqual(result, 'one')

    def test_pager_exactly_per_page_entries_request_next(self):
        self.results = ['one', 'two', 'three']
        self.mock_prompt_choice.side_effect = [None, 1]

        result = main.pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 3)
        self.assertEqual(self.mock_prompt_choice.call_count, 2)
        self.assertEqual(result, 'one')

    def test_pager_more_than_per_page_entries(self):
        self.results = ['one', 'two', 'three', 'four']
        self.mock_prompt_choice.side_effect = [None, 4]

        result = main.pager(*self.input_bundle)
        self.assertEqual(self.mock_to_string.call_count, 4)
        self.assertEqual(self.mock_prompt_choice.call_count, 2)
        self.assertEqual(result, 'four')

    def test_pager_more_than_per_page_entries_select_on_first_prompt(self):
        self.results = ['one', 'two', 'three', 'four']
        self.mock_prompt_choice.side_effect = [1, 2]

        result = main.pager(*self.input_bundle)
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
            main.prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(cm.exception.code, 0)

    def test_prompt_choice_upper_q(self):
        self.mock_input.return_value = 'Q'
        with self.assertRaises(SystemExit) as cm:
            main.prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(cm.exception.code, 0)

    def test_prompt_choice_n(self):
        self.mock_input.return_value = 'n'
        result = main.prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertIsNone(result)

    def test_prompt_choice_upper_n(self):
        self.mock_input.return_value = 'N'
        result = main.prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertIsNone(result)

    def test_prompt_choice_n_not_allowed(self):
        self.mock_input.side_effect = ['n', 'N', '1']
        result = main.prompt_choice(4, 'some action', 0)

        self.assertEqual(self.mock_input.call_count, 3)
        self.assertEqual(result, 1)

    def test_prompt_choice_invalid(self):
        self.mock_input.side_effect = ['foo', 'f', 'n']
        result = main.prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 3)
        self.assertIsNone(result)

    def test_prompt_choice_invalid_int_zero(self):
        self.mock_input.side_effect = ['0', 'n']
        result = main.prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 2)
        self.assertIsNone(result)

    def test_prompt_choice_invalid_int_negative(self):
        self.mock_input.side_effect = ['-2', 'n']
        result = main.prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 2)
        self.assertIsNone(result)

    def test_prompt_choice_invalid_int_too_large(self):
        self.mock_input.side_effect = ['5', 'n']
        result = main.prompt_choice(*self.input_bundle)

        self.assertEqual(self.mock_input.call_count, 2)
        self.assertIsNone(result)

    def test_prompt_choice_min_int(self):
        self.mock_input.return_value = '1'
        result = main.prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(result, 1)

    def test_prompt_choice_max_int(self):
        self.mock_input.return_value = '4'
        result = main.prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(result, 4)

    def test_prompt_choice_inbetween_int(self):
        self.mock_input.return_value = '3'
        result = main.prompt_choice(*self.input_bundle)

        self.mock_input.assert_called_once()
        self.assertEqual(result, 3)


class TestYearRange(unittest.TestCase):
    """Test the year_range() method."""

    def test_year_range_empty(self):
        result = main.year_range('', '')
        self.assertEqual(result, '')

    def test_year_range_both(self):
        result = main.year_range('123', '456')
        self.assertEqual(result, '123–456')

    def test_year_range_start_only(self):
        result = main.year_range('123', '')
        self.assertEqual(result, '123')

    def test_year_range_end_only(self):
        result = main.year_range('', '456')
        self.assertEqual(result, '–456')


class TestFilteredAuthorGenerator(BaseTestCase):
    """Test the filtered_author_generator() method."""

    def setUp(self):
        Author = namedtuple('Author', 'uid nationalities')
        main.all_authors = {
            1: Author('none', ''),
            2: Author('one_se', 'se'),
            3: Author('one_en', 'en'),
            4: Author('two', 'en se'),
        }

    def test_filtered_author_generator_no_filter(self):
        results = [a.uid for a in main.filtered_author_generator()]
        self.assert_length(results, 4)

    def test_filtered_author_generator_non_applicable_filter_present(self):
        results = [a.uid for a in main.filtered_author_generator(foo='bar')]
        self.assert_length(results, 4)

    def test_filtered_author_generator_uid_filter_present(self):
        results = [a.uid for a in main.filtered_author_generator(uid='two')]
        self.assert_length(results, 1)
        self.assertEqual(results[0], 'two')

    def test_filtered_author_generator_uid_filter_not_present(self):
        results = [a.uid for a in main.filtered_author_generator(uid='foo')]
        self.assert_length(results, 0)

    def test_filtered_author_generator_nationality_filter_present(self):
        results = [a.uid for a in
                   main.filtered_author_generator(nationality='se')]
        self.assert_length(results, 2)
        self.assertEqual(results, ['one_se', 'two'])

    def test_filtered_author_generator_nationality_filter_not_present(self):
        results = [a.uid for a in
                   main.filtered_author_generator(nationality='foo')]
        self.assert_length(results, 0)

    def test_filtered_author_generator_multiple_filters_present(self):
        results = [a.uid for a in
                   main.filtered_author_generator(nationality='se', uid='two')]
        self.assert_length(results, 1)
        self.assertEqual(results[0], 'two')

    def test_filtered_author_generator_multiple_filters_mixed_presence(self):
        results = [a.uid for a in
                   main.filtered_author_generator(nationality='se',
                                                  uid='one_en')]
        self.assert_length(results, 0)


class TestFilteredWorkGenerator(BaseTestCase):
    """Test the filtered_work_generator() method."""

    def setUp(self):
        Work = namedtuple('Work', 'uid author_uids coauthor_uids language')
        main.all_works = {
            1: Work('none', '', '', ''),
            2: Work('one_sv', 'foo', '', 'sv'),
            3: Work('one_en', 'bar foo foobar', '', 'en'),
            4: Work('two', 'auth', 'coauth', 'en sv'),
            5: Work('coauthor', '', 'foo bar', ''),
        }

    def test_filtered_work_generator_no_filter(self):
        results = [w.uid for w in main.filtered_work_generator()]
        self.assert_length(results, 5)

    def test_filtered_work_generator_non_applicable_filter_present(self):
        results = [w.uid for w in main.filtered_work_generator(foo='bar')]
        self.assert_length(results, 5)

    # uid filters
    def test_filtered_work_generator_uid_filter_present(self):
        results = [w.uid for w in main.filtered_work_generator(uid='two')]
        self.assert_length(results, 1)
        self.assertEqual(results[0], 'two')

    def test_filtered_work_generator_uid_filter_not_present(self):
        results = [w.uid for w in main.filtered_work_generator(uid='foo')]
        self.assert_length(results, 0)

    # language filters
    def test_filtered_work_generator_language_filter_present(self):
        results = [w.uid for w in main.filtered_work_generator(language='sv')]
        self.assert_length(results, 2)
        self.assertEqual(results, ['one_sv', 'two'])

    def test_filtered_work_generator_language_filter_not_present(self):
        results = [w.uid for w in main.filtered_work_generator(language='foo')]
        self.assert_length(results, 0)

    # author/coauthor filters
    def test_filtered_work_generator_author_filter_present(self):
        # present in both author and coauthor
        results = [w.uid for w in main.filtered_work_generator(author='bar')]
        self.assert_length(results, 2)
        self.assertEqual(results, ['one_en', 'coauthor'])

    def test_filtered_work_generator_author_filter_not_present(self):
        results = [w.uid for w in
                   main.filtered_work_generator(author='barfoo')]
        self.assert_length(results, 0)

    def test_filtered_work_generator_mixed_filter_present(self):
        results = [w.uid for w in
                   main.filtered_work_generator(language='sv', author='foo')]
        self.assert_length(results, 1)
        self.assertEqual(results[0], 'one_sv')

    def test_filtered_work_generator_mixed_filter_no_join(self):
        results = [w.uid for w in
                   main.filtered_work_generator(language='sv',
                                                author='foobar')]
        self.assert_length(results, 0)


class TestUpdateFilters(BaseTestCase):
    """Test the UpdateFilters argparse action."""

    def setUp(self):
        self.parser = argparse.ArgumentParser()
        self.parser.set_defaults(filters={})

    def test_update_filters(self):
        self.parser.add_argument(
            '--uid', action=main.UpdateFilters, default=argparse.SUPPRESS)
        args = self.parser.parse_args(['--uid', 'FOO'])
        self.assertEqual(vars(args), {'filters': {'uid': 'FOO'}})

    def test_update_filters_with_dest(self):
        self.parser.add_argument(
            '--lang', dest='language', action=main.UpdateFilters,
            default=argparse.SUPPRESS)
        args = self.parser.parse_args(['--lang', 'FOO'])
        self.assertEqual(vars(args), {'filters': {'language': 'FOO'}})

    def test_update_filters_non_update_filter(self):
        self.parser.add_argument(
            '--lang', dest='language', action=main.UpdateFilters,
            default=argparse.SUPPRESS)
        self.parser.add_argument('--dir', action='store')
        args = self.parser.parse_args(['--dir', 'FOO'])
        self.assertEqual(vars(args), {'dir': 'FOO', 'filters': {}})


class TestHandleArgs(unittest.TestCase):
    """Test the handle_args() method."""

    def test_handle_args_defaults(self):
        argv = []
        args = main.handle_args(argv)
        self.assertEquals(
            vars(args),
            {
                'dir': None,
                'display_entries': main.display_works,
                'dry': False,
                'filters': {},
                'per_page': 25,
                'update': False
            })

    def test_handle_args_handle_all_long_args(self):
        argv = ['--list_authors', '--update', '--dry',
                '--per_page', '5',
                '--dir', 'something/foo/',
                '--lang', 'sv',
                '--nationality', 'se',
                '--uid', 'foo']
        args = main.handle_args(argv)
        self.assertEquals(
            vars(args),
            {
                'dir': 'something/foo/',
                'display_entries': main.display_authors,
                'dry': True,
                'filters': {
                    'language': 'sv',
                    'nationality': 'se',
                    'uid': 'foo'},
                'per_page': 5,
                'update': True
            })

    def test_handle_args_handle_all_short_args(self):
        argv = ['-a',
                '-n', '5']
        args = main.handle_args(argv)
        self.assertEquals(
            vars(args),
            {
                'dir': None,
                'display_entries': main.display_authors,
                'dry': False,
                'filters': {},
                'per_page': 5,
                'update': False
            })
