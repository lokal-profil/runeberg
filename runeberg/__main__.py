#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Entry point for navigating the works at Runeberg.org."""
# @ TODO: store string representations in all_authors
from collections import namedtuple
import argparse

import runeberg.download as downloader
from runeberg.lst_file import LstFile

DEFAULT_PER_PAGE = 25
all_authors = None
all_works = None
worked_authors = None  # authors which appear in works  # @TODO: redo


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


# @TODO: add uid filter
# @TODO: year based filter
def filtered_work_generator(author=None, language=None, **kargs):
    """
    Generate works matching the provided filter.

    @param author: author to filter on
    @param language: language to filter on
    @yield work
    """
    for work in all_works.values():
        if author and author not in work.author_uids.split():
            continue
        if language and language.lower() not in work.language.split():
            continue
        yield work


# @TODO: add uid filter
def filtered_author_generator(nationality=None, **kargs):
    """
    Generate authors matching the provided filter.

    @param nationality: nationality to filter on
    @yield work
    """
    # @TODO: year based filters
    for author in all_authors.values():
        if author.uid not in worked_authors:
            continue
        if (nationality and
                nationality.lower() not in author.nationalities.split()):
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


def display_works(filters, per_page):
    """@TODO: docstring."""
    chosen_work = pager(filtered_work_generator, filters, work_as_string,
                        'download', per_page=per_page)
    print('You picked {}, downloading...'.format(chosen_work.uid))
    # @TODO: return uid back to main where download is triggered


def display_authors(filters, per_page):
    """@TODO: docstring."""
    chosen_author = pager(filtered_author_generator, filters, author_as_string,
                          'display their works', per_page=per_page)
    print('You picked {}...'.format(chosen_author.uid))
    filters['author'] = chosen_author.uid
    display_works(filters, per_page)


def pager(generator, filters, as_string, select_action, per_page=25):
    """@TODO: docstring."""
    displayed = []
    for i, entry in enumerate(generator(**filters)):
        displayed.append(entry)
        print('{0}. {1}'.format(i + 1, as_string(entry)))
        if (i + 1) % per_page == 0:
            choice = prompt_choice(len(displayed), select_action, per_page)
            if choice is None:
                continue
            return displayed[choice - 1]

    # handle the remainder
    if i % per_page > 0:
        choice = prompt_choice(len(displayed), select_action,
                               per_page, offer_next=False)
        return displayed[choice - 1]

    # Bow out gracefully
    if i == 0:
        print('Got no hits!, Sorry!')
    else:
        print('Thats all there is!, Sorry!')
    exit(0)


def prompt_choice(length, select_action, per_page, offer_next=True):
    """@TODO: docstring."""
    prompt = 'What do you want to do? [{0}] to {1}, {2}[Q]uit: '.format(
        '1' if length == 1 else '1-{length}',
        select_action,
        '[N]ext {per_page}, ' if offer_next else '')
    while True:
        choice = input(prompt.format(length=length, per_page=per_page))
        try:
            int_choice = int(choice)
        except ValueError:
            int_choice = None

        if choice.lower() == 'n' and offer_next:
            return None
        elif choice.lower() == 'q':
            exit(0)
        elif int_choice and int_choice in range(1, length + 1):
            return int_choice
        else:
            print('Invalid choice. Try again!')


class UpdateFilters(argparse.Action):
    """Action whereby the value is stored in a predefined dictionary."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Store the arg and value as a key-value pair in a 'filters' dict."""
        adict = getattr(namespace, 'filters')
        adict.update({self.dest: values})


def handle_args():
    """
    Parse and handle command line arguments. to get data from the database.

    Options:
        --author if present switch to first presenting a list of authors,
            selecting an author presents the list of their works.
        --lang Filter for works in this language
        --nationality Filter for authors with this nationality, two letter
            lower case iso code.
        --uid The author_uid to filter on, if the -a flag is present, else the
            work_uid to download.
        --per_page <int> number of results to output per go. Defaults to 25.
        --dir path to a directory where file should be downloaded.
        --help Display this list
    """
    parser = argparse.ArgumentParser(description='Navigate Runeberg.org works '
                                                 'and select one to download.')
    parser.set_defaults(filters={})
    parser.add_argument('-a', '--list_authors', dest='display_entries',
                        action='store_const', const=display_authors,
                        default=display_works,
                        help=('if present switch to first presenting a list '
                              'of authors, selecting an author presents the '
                              'list of their works.'))
    parser.add_argument('-n', '--per_page', type=int, default=DEFAULT_PER_PAGE,
                        action='store', metavar='N',
                        help=('number of results to output per go. Defaults '
                              'to {}.'.format(DEFAULT_PER_PAGE)))
    parser.add_argument('--dir', action='store', metavar='PATH',
                        help=('path to a directory where file should be '
                              'downloaded.'))

    # filters
    parser.add_argument('--lang', dest='language', action=UpdateFilters,
                        metavar='XX', default=argparse.SUPPRESS,
                        help=('filter for works in this language '
                              '(2 letter code)'))
    parser.add_argument('--nationality', action=UpdateFilters,
                        metavar='XX', default=argparse.SUPPRESS,
                        help=('filter for authors with this nationality, '
                              '(2 letter ISO code).'))
    parser.add_argument('--uid', action=UpdateFilters,
                        default=argparse.SUPPRESS,
                        help=('the author_uid to filter on, if the -a flag is '
                              'present, else the work_uid to download.'))
    return parser.parse_args()


def main(args):
    """@TODO: docstring."""
    load_authors()
    load_works()
    args.display_entries(args.filters, args.per_page)


if __name__ == "__main__":
    args = handle_args()
    main(args)
