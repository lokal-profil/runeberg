#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Handler for the .lst file format, a fairly simple text document.

See definition at http://runeberg.org/admin/19990511.html
"""
import os


class LstFile(object):
    """Handler for the Lst file format."""

    CMT_SYMBOL = '#'
    DELIMITER = '|'

    def __init__(self, func=None):
        """
        Construct a file object.

        @param func: a function to which each parsed line is passed. If non is
            provided each line is returned as a tuple
        """
        self.data = []
        self.comments = []
        self.name = ''
        self._func = func

    @staticmethod
    def from_file(file_path, func=None):
        """
        Create an LstFile from an .lst file object.

        @param func: a function to which each parsed line is passed. If none is
            provided each line is returned as a tuple.
        """
        lst = LstFile(func)
        with open(file_path) as f:
            lst.name = os.path.basename(f.name)
            for line in f:
                lst.parse_line(line)
        return lst

    @staticmethod
    def from_stream(stream, file_name=None, func=None):
        """
        Create an LstFile from an .lst file stream.

        @param func: a function to which each parsed line is passed. If none is
            provided each line is returned as a tuple.
        """
        lst = LstFile(func)
        if file_name:
            lst.name = file_name
        for line in stream.split('\n'):
            lst.parse_line(line)
        return lst

    def parse_line(self, line):
        """Parse a line in an .lst file separating data from comments."""
        line = line.rstrip('\n')
        if not line:
            # skip completely empty lines
            pass
        elif line.startswith(LstFile.CMT_SYMBOL):
            # skip completly empty comments
            if line[len(LstFile.CMT_SYMBOL):].strip():
                self.comments.append(
                    line[len(LstFile.CMT_SYMBOL):].lstrip())
        else:
            d = line.split(LstFile.DELIMITER)
            if self._func:
                d = self._func(*d)
            else:
                d = tuple(d)
            self.data.append(d)

    @property
    def columns(self):
        """Determine the number of columns in the data set."""
        try:
            return max(len(row) for row in self.data)
        except TypeError:
            if self._func:
                raise NotImplementedError(
                    '{0} does not specify a length'.format(
                        self._func.__name__))
            raise

    def __len__(self):
        """Set length of file to number of data entries."""
        return len(self.data)
