#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Entry point for navigating the works at Runeberg.org."""
import argparse
from collections import namedtuple

import runeberg.download as downloader
from runeberg.lst_file import LstFile

DEFAULT_PER_PAGE = 25
all_authors = None
all_works = None


def load_authors(in_use_authors):
    """
    Load the authors file.

    Loads all authors but only returns those which are used in works.
    @param in_use_authors: set of all author and coauthor uids encountered in
        works.
    """
    global all_authors
    if not all_authors:
        stream = downloader.download_author_file(save=False)
        # @TODO replace by runeberg.Person once #3 gets implemented
        Author = namedtuple('Author', 'birth death surname first_name '
                                      'nationalities notes uid')
        lst_authors = LstFile.from_stream(stream, func=Author)
        all_authors = {author.uid: author
                       for author in lst_authors.data
                       if author.uid in in_use_authors}


def load_works():
    """
    Load the works file.

    @return: set of all author and coauthor uids.
    """
    global all_works
    if not all_works:
        stream = downloader.download_works_file(save=False)
        Work = namedtuple('Work', 'title uid author_uids language year_start '
                          'year_end coauthor_uids translator_uids '
                          'original_language')
        lst_works = LstFile.from_stream(stream, func=Work)
        all_works = {work.uid: work for work in lst_works.data}

        in_use_authors = set()
        for work in lst_works.data:
            in_use_authors.update(work.author_uids.split())
            in_use_authors.update(work.coauthor_uids.split())
    return in_use_authors


# @TODO: year based filter
def filtered_work_generator(author=None, language=None, uid=None, **kargs):
    """
    Generate works matching the provided filter.

    @param author: author to filter on
    @param language: language to filter on
    @yield work
    """
    for work in all_works.values():
        if uid and uid != work.uid:
            continue
        if (author and author not in work.author_uids.split()
                and author not in work.coauthor_uids.split()):
            continue
        if language and language.lower() not in work.language.split():
            continue
        yield work


# @TODO: year based filters
def filtered_author_generator(nationality=None, uid=None, **kargs):
    """
    Generate authors matching the provided filter.

    @param nationality: nationality to filter on
    @yield work
    """
    for author in all_authors.values():
        if uid and uid != author.uid:
            continue
        if (nationality and
                nationality.lower() not in author.nationalities.split()):
            continue
        yield author


def year_range(y_start, y_end):
    """Format a year range."""
    year = y_start or ''
    if y_end:
        year += '–' + y_end
    return year


def author_as_string(author, short=False):
    """
    Format an author.

    Uses the format: first_name last_name (year_b-year_d) [nationalities]

    @param author: Author to format
    @param short: Whether to just return the name
    """
    name = '{0} {1}'.format(author.first_name, author.surname).strip()
    if short:
        return name
    year = year_range(author.birth, author.death)
    nat = ', '.join(author.nationalities.split())
    return '{name} ({year}) [{nat}]'.format(
        name=name, year=year or '?', nat=nat or '?')


def work_as_string(work):
    """
    Format a work.

    Uses the format: title (year) by author_1, author_2 and author_3 [langs]

    If the work has no authors it falls back on coauthors.
    """
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
    """
    Display a filtered list of works for the user to choose from.

    @param filters: author and work filters to pass on
    @param per_page: results to output per page.
    @return: chosen work uid
    """
    chosen_work = pager(filtered_work_generator, filters, work_as_string,
                        'download', per_page=per_page)
    print("You picked '{0}' [uid={1}], downloading…".format(
        chosen_work.title, chosen_work.uid))
    return chosen_work.uid


def display_authors(filters, per_page):
    """
    Display a filtered list of authors for the user to choose works from.

    Upon choosing one the list of works is displayed.

    @param filters: author and work filters to pass on
    @param per_page: results to output per page.
    @return: chosen work uid
    """
    chosen_author = pager(filtered_author_generator, filters, author_as_string,
                          'display their works', per_page=per_page)
    print('Displaying works by {0} [uid={1}]…'.format(
        author_as_string(chosen_author, short=True), chosen_author.uid))
    filters['author'] = chosen_author.uid
    filters.pop('uid', None)  # since this was an author_uid not work_uid
    return display_works(filters, per_page)


def pager(generator, filters, as_string, select_action, per_page):
    """
    Page through the results from a generator, prompting a choice.

    @param generator: a generator for the entries to list.
    @param filters: filter which is passed on to the filtered_work_generator.
    @param as_string: function to convert generator entries to strings.
    @param select_action: description of what choosing an entry will result in.
    @param per_page: results to output per page.
    """
    displayed = []
    i = 0  # in case generator is empty
    for i, entry in enumerate(generator(**filters), 1):
        displayed.append(entry)
        print('{0}. {1}'.format(i, as_string(entry)))
        if i % per_page == 0:
            choice = prompt_choice(len(displayed), select_action, per_page)
            if choice is None:
                continue
            return displayed[choice - 1]

    if i == 0:
        print('Got no hits!, Sorry!')
        exit(0)
    else:  # handle the remainder
        if i % per_page == 0:
            print('That is all there was!, Sorry!')
        choice = prompt_choice(len(displayed), select_action, per_page=0)
        return displayed[choice - 1]


def prompt_choice(length, select_action, per_page):
    """
    Prompt the user for a choice of entry, to continue or to quit.

    An invalid choice will repeat the prompt.

    @param length: the largest choosable value
    @param select_action: description of what choosing an entry will result in.
    @param per_page: number of results to offer next. Set to 0 to hide "next"
        option.
    """
    prompt = 'What do you want to do? [{0}] to {1}, {2}[Q]uit: '.format(
        '1' if length == 1 else '1–{length}',
        select_action,
        '[N]ext {per_page}, ' if per_page else '')
    while True:
        choice = input(prompt.format(length=length, per_page=per_page))
        try:
            int_choice = int(choice)
        except ValueError:
            int_choice = None

        if choice.lower() == 'n' and per_page:
            return None
        elif choice.lower() == 'q':
            exit(0)
        elif int_choice and (1 <= int_choice <= length):
            return int_choice
        else:
            print('Invalid choice. Try again!')


class UpdateFilters(argparse.Action):
    """Action whereby the value is stored in a predefined dictionary."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Store the arg and value as a key-value pair in a 'filters' dict."""
        adict = getattr(namespace, 'filters')
        adict.update({self.dest: values})


def handle_args(argv=None):
    """
    Parse and handle command line arguments.

    @param argv: arguments to parse. Defaults to sys.argv[1:].
    @return: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description='Navigate Runeberg.org works and select one to download.')
    parser.set_defaults(filters={})
    parser.add_argument('-a', '--list_authors', dest='display_entries',
                        action='store_const', const=display_authors,
                        default=display_works,
                        help=('switch to first presenting a list of authors, '
                              'selecting an author presents the list of their '
                              'works.'))
    parser.add_argument('-n', '--per_page', type=int, default=DEFAULT_PER_PAGE,
                        action='store', metavar='N',
                        help=('number of results to output per go. Defaults '
                              'to {}.'.format(DEFAULT_PER_PAGE)))
    parser.add_argument('--dir', action='store', metavar='PATH',
                        help=('path to directory where files should be '
                              'downloaded.'))
    parser.add_argument('--update', action='store_true',
                        help='forced update of any previously downloaded '
                             'files.')
    parser.add_argument('--dry', action='store_true',
                        help='simulated run without the final download.')

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
    return parser.parse_args(argv)


def main():
    """Run main process."""
    args = handle_args()
    in_use_authors = load_works()
    load_authors(in_use_authors)
    work_uid = args.display_entries(args.filters, args.per_page)
    if not args.dry:
        downloader.get_work(work_uid, data_dir=args.dir, update=args.update)


if __name__ == "__main__":
    main()
