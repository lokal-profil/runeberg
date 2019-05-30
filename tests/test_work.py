# -*- coding: utf-8 -*-
"""Unit tests for work."""
import unittest
import unittest.mock as mock
from collections import Counter, OrderedDict

from runeberg.article import Article
from runeberg.page import Page
from runeberg.page_range import PageRange
from runeberg.work import DisambiguationError, ReconciliationError, Work


class TestParseRange(unittest.TestCase):

    """Unit tests for parse_range."""

    def setUp(self):
        self.work = Work('test')
        self.work.pages = PageRange([
            ('one', 3),
            ('two', 2),
            ('three', 1),
            ('four', 0)])

    def test_parse_range_empty(self):
        range = ''
        self.assertEqual(self.work.parse_range(range), [])

    def test_parse_range_single_page(self):
        range = 'two'
        self.assertEqual(self.work.parse_range(range), [2])

    def test_parse_range_single_range(self):
        range = 'one-three'
        self.assertEqual(
            self.work.parse_range(range),
            [PageRange([
                ('one', 3),
                ('two', 2),
                ('three', 1)])])

    def test_parse_range_multiple_mixed(self):
        range = 'one three-four'
        self.assertEqual(
            self.work.parse_range(range),
            [
                3,
                PageRange([
                    ('three', 1),
                    ('four', 0)])
            ])


class TestLoadMetadata(unittest.TestCase):

    """Unit tests for load_metadata."""

    def setUp(self):
        self.work = Work('test')
        # cannot autospec due to https://bugs.python.org/issue23078
        patcher = mock.patch('runeberg.work.Work.read_metadata')
        self.mock_read_metadata = patcher.start()
        self.mock_read_metadata.return_value = [
            'CHARSET: utf-8',
            'TITLEKEY: test',
            'FOO: bar'
        ]
        self.expected = {
            'CHARSET': 'utf-8',
            'TITLEKEY': 'test',
            'FOO': 'bar'
        }
        self.addCleanup(patcher.stop)

    def test_load_metadata_empty(self):
        self.mock_read_metadata.return_value = []
        with self.assertRaises(NotImplementedError):  # unsupported charset
            self.work.load_metadata('path')

    def test_load_metadata_set_and_overwritten_attribute(self):
        self.work.metadata = {'TEST': 'test'}

        self.assertEqual(self.work.load_metadata('path'), self.expected)
        self.assertEqual(self.work.metadata, self.expected)
        self.mock_read_metadata.assert_called_once_with('path')

    def test_load_metadata_ignore_comments(self):
        self.mock_read_metadata.return_value.append('# a comment')
        self.assertEqual(self.work.load_metadata('path'), self.expected)

    def test_load_metadata_detect_invalid_line(self):
        self.mock_read_metadata.return_value.append('an invalid line')
        with self.assertRaises(ValueError) as e:
            self.work.load_metadata('path')
            self.assertEqual(
                e.exception,
                'The following metadata line is invalid: an invalid line')

    def test_load_metadata_detect_invalid_identifier(self):
        self.mock_read_metadata.return_value = [
            'CHARSET: utf-8',
            'TITLEKEY: other_id'
        ]
        with self.assertRaises(ValueError) as e:
            self.work.load_metadata('path')
            self.assertEqual(
                e.exception,
                'Metadata work identifier does not match the provided '
                'identifier (provided: "test", found: "other_id")')


class TestParseMarc(unittest.TestCase):

    """Unit tests for parse_marc."""

    def setUp(self):
        self.work = Work('test')
        self.work.metadata = {'MARC': ''}

    def test_parse_marc_empty(self):
        del self.work.metadata['MARC']
        self.assertEqual(self.work.parse_marc(), {})

    def test_parse_marc_single(self):
        self.work.metadata['MARC'] = 'libris:1285211'
        self.assertEqual(self.work.parse_marc(), {'libris': '1285211'})

    def test_parse_marc_multiple(self):
        self.work.metadata['MARC'] = 'bibsys:123 rex:456'
        self.assertEqual(
            self.work.parse_marc(),
            {'bibsys': '123', 'rex': '456'})


class TestSetupDisambiguationCounter(unittest.TestCase):

    """Unit tests for setup_disambiguation_counter."""

    def test_setup_disambiguation_counter_empty(self):
        chapters = Counter()
        self.assertEqual(
            Work.setup_disambiguation_counter(chapters),
            Counter())

    def test_setup_disambiguation_counter_no_duplicates(self):
        chapters = Counter(['a', 'b', 'c'])
        self.assertEqual(
            Work.setup_disambiguation_counter(chapters),
            Counter())

    def test_setup_disambiguation_counter_duplicates(self):
        chapters = Counter(['a', 'b', 'c', 'b', 'b', 'c'])
        self.assertEqual(
            Work.setup_disambiguation_counter(chapters),
            Counter({'b': 1, 'c': 1}))


class TestLoadArticle(unittest.TestCase):

    def setUp(self):
        self.work = Work('Foo')
        self.base_path = 'bar'

        # mock both the object creation and the `data` attribute
        patcher = mock.patch('runeberg.lst_file.LstFile.from_file')
        self.mock_lst_file = patcher.start()
        self.mock_lst_file_data = mock.PropertyMock()
        self.mock_lst_file.return_value = mock.MagicMock()
        type(self.mock_lst_file.return_value).data = self.mock_lst_file_data
        self.addCleanup(patcher.stop)

        patcher = mock.patch('runeberg.work.Work.parse_range')
        self.mock_parse_range = patcher.start()
        self.mock_parse_range.return_value = [Page('0001', ocr='abc')]
        self.addCleanup(patcher.stop)

        patcher = mock.patch('runeberg.page.Page.rename_chapter')
        self.mock_rename_chapter = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('runeberg.page.Page.get_chapters')
        self.mock_get_chapters = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch('runeberg.work.Work.setup_disambiguation_counter')
        self.mock_disambiguation_counter = patcher.start()
        self.addCleanup(patcher.stop)

    def test_load_articles_empty(self):
        self.mock_lst_file_data.return_value = []
        self.work.load_articles(self.base_path, 'chapter_counter',
                                reconcile_chapter_tags=False)

        self.assertEqual(self.work.articles, OrderedDict())
        self.mock_parse_range.assert_not_called()
        self.mock_get_chapters.assert_not_called()
        self.mock_rename_chapter.assert_not_called()

        # don't test these further
        self.mock_lst_file.assert_called_once_with('bar/Articles.lst')
        self.mock_disambiguation_counter.assert_called_once_with(
            'chapter_counter')

    def test_load_articles_one_to_one_article_chapter_tags(self):
        self.mock_lst_file_data.return_value = [('foo', 'A', '0001')]
        self.mock_disambiguation_counter.return_value = Counter()
        self.mock_get_chapters.return_value = ['A']

        expected = Article(
            'A', pages=self.mock_parse_range.return_value, html_name='foo')
        expected.uid  # triggers self._clean_title
        self.work.load_articles(self.base_path, Counter({'A': 1}))

        self.assertEqual(
            self.work.articles,
            OrderedDict([('A', expected)]))
        self.mock_parse_range.assert_called_once_with('0001')
        self.mock_rename_chapter.assert_not_called()

    def test_load_articles_one_to_one_article_chapter_tags_dupe(self):
        self.mock_lst_file_data.return_value = [('foo', 'A', '0001')]
        self.mock_disambiguation_counter.return_value = Counter({'A': 1})
        self.mock_get_chapters.return_value = ['A']

        expected = Article(
            'A', pages=self.mock_parse_range.return_value, html_name='foo',
            disambig=1)
        expected.uid  # triggers self._clean_title
        self.work.load_articles(self.base_path, Counter(),
                                reconcile_chapter_tags=False)

        self.assertEqual(
            self.work.articles,
            OrderedDict([('A (1)', expected)]))
        self.mock_parse_range.assert_called_once_with('0001')
        self.mock_rename_chapter.assert_called_once_with('A', 'A (1)')

    def test_load_articles_no_chapter_no_dupe(self):
        self.mock_lst_file_data.return_value = [('foo', 'A', '0001')]
        self.mock_disambiguation_counter.return_value = Counter()
        self.mock_get_chapters.return_value = ['B']

        expected = Article(
            'A', pages=self.mock_parse_range.return_value, html_name='foo')
        expected.no_chapter_tag = True
        expected.uid  # triggers self._clean_title
        self.work.load_articles(self.base_path, Counter(),
                                reconcile_chapter_tags=True)

        self.assertEqual(
            self.work.articles,
            OrderedDict([('A', expected)]))
        self.mock_parse_range.assert_called_once_with('0001')
        self.mock_rename_chapter.assert_not_called()

    def test_load_articles_no_chapter_no_dupe_toc(self):
        self.mock_lst_file_data.return_value = [('foo', 'A', '')]
        self.mock_disambiguation_counter.return_value = Counter()
        self.mock_parse_range.return_value = []

        expected = Article(
            'A', pages=self.mock_parse_range.return_value, html_name='foo')
        expected.no_chapter_tag = None
        expected.uid  # triggers self._clean_title
        self.work.load_articles(self.base_path, Counter(),
                                reconcile_chapter_tags=True)

        self.assertEqual(
            self.work.articles,
            OrderedDict([('A', expected)]))
        self.mock_parse_range.assert_called_once_with('')
        self.mock_rename_chapter.assert_not_called()

    def test_load_articles_no_chapter_with_dupe_raise_error(self):
        self.mock_lst_file_data.return_value = [('foo', 'A', '0001'),
                                                ('bar', 'A', '')]
        self.mock_disambiguation_counter.return_value = Counter()
        self.mock_get_chapters.return_value = []

        with self.assertRaises(DisambiguationError):
            self.work.load_articles(self.base_path, Counter(),
                                    reconcile_chapter_tags=True)

    def test_load_articles_chapter_without_article(self):
        self.mock_lst_file_data.return_value = [('foo', 'A', '0001')]
        chapters = Counter({'B': 1})
        self.mock_disambiguation_counter.return_value = Counter()
        self.mock_get_chapters.return_value = []

        with self.assertRaises(ReconciliationError):
            self.work.load_articles(self.base_path, chapters,
                                    reconcile_chapter_tags=True)

    def test_load_articles_more_dupes_than_expected(self):
        self.mock_lst_file_data.return_value = [('foo', 'A', '0001'),
                                                ('bar', 'A', '0002'),
                                                ('foobar', 'A', '0003')]
        chapters = Counter({'A': 2})
        self.mock_disambiguation_counter.return_value = Counter({'A': 1})
        self.mock_get_chapters.return_value = ['A']
        self.mock_parse_range.return_value = [
            Page('0001', ocr='abc'),
            Page('0002', ocr='abc'),
            Page('0003', ocr='abc')]

        with self.assertRaises(ReconciliationError):
            self.work.load_articles(self.base_path, chapters,
                                    reconcile_chapter_tags=True)


# @TODO: Mock Page (and Article?)
class TestReconciliationError(unittest.TestCase):

    """Tests for list construction in ReconciliationError."""

    def test_reconciliation_error_empty(self):
        e = ReconciliationError(Counter(), OrderedDict())
        self.assertEqual(e.unclaimed_chapters, [])
        self.assertEqual(e.no_tag_articles, [])

    def test_reconciliation_error_non_zero_chapter_count(self):
        chapters = Counter({'a': 10, 'b': 0, 'c': 1})
        e = ReconciliationError(chapters, OrderedDict())
        self.assertEqual(e.unclaimed_chapters, [
            'a: 10 time(s)',
            'c: 1 time(s)'])
        self.assertEqual(e.no_tag_articles, [])

    def test_reconciliation_error_negative_chapter_count(self):
        chapters = Counter({'c': 0, 'd': -1})
        e = ReconciliationError(chapters, OrderedDict())
        self.assertEqual(e.unclaimed_chapters, ['d: -1 time(s)'])
        self.assertEqual(e.no_tag_articles, [])

    def test_reconciliation_error_articles(self):
        a = Article('a', pages=[Page('001')])
        b = Article('b', pages=[Page('002')])
        b.no_chapter_tag = True
        c = Article('c')
        articles = OrderedDict([('a', a), ('b', b), ('c', c)])
        e = ReconciliationError(Counter(), articles)
        self.assertEqual(e.unclaimed_chapters, [])
        self.assertEqual(e.no_tag_articles, [
            'b: page(s) 002'
        ])
