# -*- coding: utf-8 -*-
"""Unit tests for person."""
import unittest
import unittest.mock as mock
from datetime import date

from runeberg.person import Person


class TestName(unittest.TestCase):
    """Test the name() method."""

    def test_name_wo_first_name(self):
        """Test person without a first name."""
        person = Person(1, 'Mac TestFace')
        self.assertEqual(person.name(), 'Mac TestFace')

    def test_name_w_first_name(self):
        """Test person with a first name."""
        person = Person(1, 'Mac TestFace', 'Test')
        self.assertEqual(person.name(), 'Test Mac TestFace')


class TestIsPd(unittest.TestCase):
    """Test the is_pd() method."""

    def setUp(self):
        """Set up person class and mocks."""
        self.person = Person(1, 'McTestFace')

        # mocking the builtin datetime
        patcher = mock.patch('runeberg.person.datetime')
        self.mock_datetime = patcher.start()
        self.mock_datetime.now.return_value = date(2020, 6, 1)
        self.addCleanup(patcher.stop)

    def test_is_pd_no_date(self):
        """Test person without a death date."""
        self.person.death_year = None
        self.assertFalse(self.person.is_pd())

    def test_is_pd_with_non_pd_year(self):
        """Test person with a non-pd death year."""
        self.person.death_year = 2000
        self.assertFalse(self.person.is_pd())

    def test_is_pd_with_exact_pd_year(self):
        """Test person with a death year exactly 70 years ago."""
        self.person.death_year = (2020 - 70)
        self.assertFalse(self.person.is_pd())

    def test_is_pd_with_pd_year(self):
        """Test person with a non-pd death year."""
        self.person.death_year = 1900
        self.assertTrue(self.person.is_pd())

    def test_is_pd_with_set_year_non_pd(self):
        """Test person with a non-pd death year for a overridden timespan."""
        self.person.death_year = 1900
        self.assertFalse(self.person.is_pd(150))

    def test_is_pd_with_set_year_pd(self):
        """Test person with a pd death year for a overridden timespan."""
        self.person.death_year = 2000
        self.assertTrue(self.person.is_pd(10))
