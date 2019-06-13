#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Entry point for navigating the works at Runeberg.org."""
# @ TODO: store string representations in all_authors
from collections import namedtuple

import runeberg.download as downloader
from runeberg.lst_file import LstFile

all_authors = None
all_works = None


def load_authors():
    """Load the authors file."""
    global all_authors
    if not all_authors:
        stream = downloader.download_author_file(save=False)
        Author = namedtuple('Author', 'birth death surname first_name '
                                      'nationalities notes uid')
        lst_authors = LstFile.from_stream(stream, func=Author)
        all_authors = {author.uid: author for author in lst_authors.data}


def load_works():
    """Load the works file."""
    global all_works
    if not all_works:
        stream = downloader.download_works_file(save=False)
        Work = namedtuple('Work', 'title uid author_uids language year_start '
                          'year_end coauthor_uids translator_uids '
                          'original_language')
        lst_works = LstFile.from_stream(stream, func=Work)
        all_works = {work.uid: work for work in lst_works.data}


def filtered_work_generator(author=None, language=None):
    """
    Generate works matching the provided filter.

    @param author: author to filter on
    @param language: language to filter on
    @yield work
    """
    # @TODO: year based filters
    for work in all_works.values():
        if author and author not in work.author_uids.split():
            continue
        if language and language not in work.language.split():
            continue
        yield work


def filtered_author_generator(nationality=None):
    """
    Generate authors matching the provided filter.

    @param nationality: nationality to filter on
    @yield work
    """
    # @TODO: year based filters
    for author in all_authors.values():
        if nationality and nationality not in author.nationalities.split():
            continue
        yield author


def year_range(y_start, y_end):
    """Format a year range."""
    year = y_start or ''
    if y_end:
        year += '̣-' + y_end
    return year


def author_as_string(author, short=False):
    """Format an author."""
    # @TODO: docstring
    # first_name last_name (year_b-year_d) [nat]
    name = '{0} {1}'.format(author.first_name, author.surname).strip()
    if short:
        return name
    year = year_range(author.birth, author.death)
    nat = ', '.join(author.nationalities.split())
    return '{name} ({year}) [{nat}]'.format(
        name=name, year=year, nat=nat or '?')


def work_as_string(work):
    """Format a work."""
    # title (year) by x, y and z [lang]
    year = year_range(work.year_start, work.year_end)
    author_uids = work.author_uids.split() or work.coauthor_uids.split()
    authors = [author_as_string(all_authors[auth_uid], short=True)
               for auth_uid in author_uids]
    author_strings = ''
    if len(authors) == 1:
        author_strings = authors[0]
    elif len(authors) > 1:
        author_strings = '{0} and {1}'.format(
            ', '.join(authors[:-1]), authors[-1])

    return '{title} ({year}) by {authors} [{lang}]'.format(
        title=work.title, year=year, authors=author_strings or '?',
        lang=work.language or '?')


def display_works(per_page=25):
    """@TODO: docstring."""
    chosen_work = pager(filtered_work_generator, work_as_string,
                        'download', per_page=per_page)
    print('You picked {}...'.format(chosen_work.uid))


def display_authors(per_page=25):
    """@TODO: docstring."""
    chosen_author = pager(filtered_author_generator, author_as_string,
                          'display their works', per_page=per_page)
    print('You picked {}...'.format(chosen_author.uid))


def pager(generator, as_string, select_action, per_page=25):
    """@TODO: docstring."""
    displayed = []
    i = 0
    for entry in generator():
        displayed.append(entry)
        print('{0}. {1}'.format(i + 1, as_string(entry)))
        i += 1
        if i % per_page == 0:
            prompt = (
                'What do you want to do? [1-{0}] to {1}, '
                '[N]ext {2}, [Q]uit: '.format(
                    len(displayed), select_action, per_page))  # @TODO: deal with len(1)
            while True:
                choice = input(prompt)
                try:
                    int_choice = int(choice)
                except ValueError:
                    int_choice = None
                    pass

                if choice.lower() == 'n':
                    break
                elif choice.lower() == 'q':
                    exit()
                elif int_choice and int_choice in range(1, len(displayed) + 1):
                    chosen_entry = displayed[int_choice - 1]
                    return chosen_entry
                else:
                    print('Try again!')
    if i % per_page > 0:
        # prompt the last ones
        raise NotImplementedError
    print('Thats all there is!')


def main():
    """@TODO: docstring."""
    load_authors()
    load_works()
    display_works(5)
    display_authors(5)


if __name__ == "__main__":
    main()