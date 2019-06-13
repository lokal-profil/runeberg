#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Entry point for navigating the works at Runeberg.org."""
# @ TODO: store string representations in all_authors
from collections import namedtuple

import runeberg.download as downloader
from runeberg.lst_file import LstFile

all_authors = None
all_works = None
worked_authors = None  # authors which appear in works


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
    global worked_authors
    if not all_works:
        stream = downloader.download_works_file(save=False)
        Work = namedtuple('Work', 'title uid author_uids language year_start '
                          'year_end coauthor_uids translator_uids '
                          'original_language')
        lst_works = LstFile.from_stream(stream, func=Work)
        all_works = {work.uid: work for work in lst_works.data}

        worked_authors = set()
        for work in lst_works.data:
            worked_authors.update(work.author_uids.split())
            worked_authors.update(work.coauthor_uids.split())


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
        if author.uid not in worked_authors:
            continue
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
        name=name, year=year or '?', nat=nat or '?')


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
        title=work.title, year=year or '?', authors=author_strings or '?',
        lang=work.language or '?')


def display_works(filters, per_page=25):
    """@TODO: docstring."""
    chosen_work = pager(filtered_work_generator, filters, work_as_string,
                        'download', per_page=per_page)
    print('You picked {}, downloading...'.format(chosen_work.uid))


def display_authors(filters, per_page=25):
    """@TODO: docstring."""
    chosen_author = pager(filtered_author_generator, filters, author_as_string,
                          'display their works', per_page=per_page)
    print('You picked {}...'.format(chosen_author.uid))
    filters['author'] = chosen_author.uid
    display_works(filters, per_page)


def pager(generator, filters, as_string, select_action, per_page=25):
    """@TODO: docstring."""
    displayed = []
    i = 0
    for entry in generator(**filters):
        displayed.append(entry)
        print('{0}. {1}'.format(i + 1, as_string(entry)))
        i += 1
        if i % per_page == 0:
            choice = prompt_choice(len(displayed), select_action, per_page)
            if choice is None:
                continue
            return displayed[choice - 1]
    # handle the remainder
    if i % per_page > 0:
        choice = prompt_choice(len(displayed), select_action,
                               per_page, next=False)
        return displayed[choice - 1]
    if i == 0:
        print('Got no hits!, Sorry!')
    else:
        print('Thats all there is!, Sorry!')
    exit()


def prompt_choice(length, select_action, per_page, next=True):
    """@TODO: docstring."""
    prompt = 'What do you want to do? [{0}] to {1}, {2}[Q]uit: '.format(
        '1' if length == 1 else '1-{length}',
        select_action,
        '[N]ext {per_page}, ' if next else '')
    while True:
        choice = input(prompt.format(length=length, per_page=per_page))
        try:
            int_choice = int(choice)
        except ValueError:
            int_choice = None
            pass

        if choice.lower() == 'n' and next:
            return None
        elif choice.lower() == 'q':
            exit()
        elif int_choice and int_choice in range(1, length + 1):
            return int_choice
        else:
            print('Invalid choice. Try again!')


def main():
    """@TODO: docstring."""
    filters = {}
    load_authors()
    load_works()
    # display_works(5)
    display_authors(filters)


if __name__ == "__main__":
    main()
