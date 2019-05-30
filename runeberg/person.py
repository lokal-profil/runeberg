#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A runeberg.org person from the author file.

These people are normally authors, translators or co-authors/editors.

The columns in the author file are:
* birth,
* death,
* surname,
* first_name,
* nationalities,
* notes,
* uid.
"""
from datetime import datetime

import runeberg.download as downloader
from runeberg.lst_file import LstFile


class Person(object):
    """An object representing a runeberg.org person."""

    def __init__(self, uid, last_name, first_name='', birth_year=None,
                 death_year=None, nationalities=None, notes=None):
        """
        Initialise a Person.

        @param uid: unique person identifier on runeberg.org
        @param last_name: surname or primary sorting name people before circa
            year 1500 are listed by first name
        @param first_name: firstname or secondary sorting name,
        @param birth_year: year of birth, four digits or blank
        @param death_year: year of death, four digits or blank
        @param nationalities: list of two-letter ISO nationality codes or ??
            for unknown
        @param notes: notes, including:
            * alternative names e.g. before/after marriage
            * profession, e.g. writer, journalist,
            * pseudonyms, e.g. (pseud. Maria Lang),
            * signatures, e.g. (sign. S.L-d),
            * sources, e.g. (source: SVFF).
        """
        self.uid = uid
        self.last_name = last_name
        self.first_name = first_name
        self.birth_year = birth_year or None
        self.death_year = death_year or None
        self.nationalities = nationalities or []
        self.notes = notes

        try:
            self.birth_year = int(birth_year)
        except (TypeError, ValueError):
            pass
        try:
            self.death_year = int(death_year)
        except (TypeError, ValueError):
            pass

    def name(self):
        """Return the composite name of the person."""
        return '{0} {1}'.format(self.first_name, self.last_name).strip()

    def is_pd(self, years=70):
        """
        If copyrights by this person have expired.

        Note that the copyright expires on the first day of the following year.

        @params year: years after death at which copyright expires. Defaults to
            70.
        """
        print(datetime.now().year)
        if self.death_year and (datetime.now().year - self.death_year) > years:
            return True
        return False

    @classmethod
    def load_people(cls, data_dir=None):
        """Download and parse runeberg.org author file."""
        file_path = downloader.download_author_file(data_dir)
        return cls.people_from_file(file_path)

    # @TODO: Notes should be parsed further
    @classmethod
    def people_from_file(cls, file_path):
        """Parse runeberg.org author file."""
        lst_file = LstFile.from_file(file_path)
        people = {}
        for data in lst_file.data:
            birth, death, surname, first_name, nationalities, notes, uid = data
            people[uid] = cls(uid, surname, first_name, birth, death,
                              nationalities.split(','), notes)
        return people
