#!/usr/bin/python
# -*- coding: utf-8 -*-
"""A sequence of consecutive Pages."""
from collections import OrderedDict
from itertools import islice


class PageRange(OrderedDict):
    """A non interrupted sequence of consecutive Pages."""

    def index(self, *args):
        """
        Find the index, or indexes, of the provided key(s).

        @return: list of indexes if multiple keys are provided otherwise a
            single index.
        """
        key_list = list(self.keys())
        if len(args) == 0:
            raise ValueError('At least one index required')
        elif len(args) == 1:
            return key_list.index(args[0])
        else:
            return [key_list.index(arg) for arg in args]

    def get_range(self, first, last, inclusive=True):
        """Create a sub-PageRange from between the provided values."""
        # the below should deal with 0 < last < first
        first_i, last_i = self.index(first, last)
        return self.slice(first_i, last_i + (1 * inclusive))

    def first(self):
        """Return the first page in the PageRange."""
        return next(iter(self.values()), None)

    def last(self):
        """Return the last page in the PageRange."""
        return next(reversed(self.values()), None)

    def __str__(self):
        """Represent the PageRange as a string."""
        # first-last
        # deal with zero pages?
        key_list = list(self.keys())
        if len(self) == 0:
            return ''
        if len(self) == 1:
            return key_list[0]
        else:
            return '{}-{}'.format(key_list[0], key_list[-1])

    # not implemented in __getitem__ to avoid it mixing keys and indexes
    # at the cost of a bulkier syntax
    def slice(self, start=None, stop=None, step=None):
        """Add slicing capabilities missing in OrderedDict."""
        return PageRange(islice(self.items(), start, stop, step))

    # def __getitem__(self, k):
    #     """Add slicing to __getitem__ of OrderedDict."""
    #     if not isinstance(k, slice):
    #         return OrderedDict.__getitem__(self, k)
    #     return PageRange(islice(self.items(), k.start, k.stop))
