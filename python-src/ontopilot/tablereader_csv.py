# Copyright (C) 2017 Brian J. Stucky
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Python imports.
from __future__ import unicode_literals
import csv
from tablereader import TableRow, BaseTable, BaseTableReader

# Java imports.


class UnicodeCSVReader(csv.DictReader):
    """
    Wraps the built-in CSV reader object to support various unicode encodings
    of input CSV files.  All data are parsed into Python unicode strings.  By
    default, data are assumed to be encoded using UTF-8, but alternative
    encodings can also be specified.
    """
    def __init__(self, csvfile, dialect='excel', encoding='utf-8', **fmtparams):
        """
        This initializer has the same signature as that of the standard
        csv.reader() method, except that an additional argument is added to
        specify the source encoding.
        """
        self.encoding = encoding

        # Get the built-in reader object.
        self.reader = csv.reader(csvfile, dialect, **fmtparams)

    def __iter__(self):
        return self

    def next(self):
        row = self.reader.next()
        u_row = [unicode(cellstr, self.encoding) for cellstr in row]

        return u_row


class _CSVTable(BaseTable):
    """
    Represents a single table in a CSV file.  _CSVTable assumes that the first
    row of the file contains the column names.  Each subsequent row is returned
    as a TableRow object; thus, column names are not case sensitive.
    """
    def __init__(self, csvreader, tablename, csvtablereader, required_cols=[], optional_cols=[], default_vals={}):
        BaseTable.__init__(
            self, tablename, csvtablereader,
            required_cols, optional_cols, default_vals
        )

        self.csvr = csvreader

        # Get the column names from the input CSV file.
        try:
            self.colnames = self.csvr.next()
        except StopIteration:
            raise RuntimeError('The input CSV file "' + self.getFileName()
                    + '" is empty.')

        self.rowcnt = 1

        # Trim the column names and make sure they are unique.
        nameset = set()
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip().lower()
            if self.colnames[colnum] in nameset:
                raise RuntimeError('The column name "' + self.colnames[colnum]
                    + '" is used more than once in the input CSV file "'
                    + self.getFileName()
                    + '".  All column names must be unique.')
            else:
                nameset.add(self.colnames[colnum])

    def next(self):
        """
        Allows iteration through each row of the CSV file.  Empty rows are
        ignored.
        """
        # Find the next non-empty row.  After the loop, self.rowcnt will be
        # equal to the next non-empty row, assuming row counting starts at 1
        # (and if the search succeeded).  Note that we don't need to check for
        # an end-of-file condition, because if we reach the end of the file,
        # the CSV reader will raise a StopIteration exception and we can just
        # let that propagate to the caller, which will give us the desired
        # behavior.
        emptyrow = True
        while emptyrow:
            rowdata = self.csvr.next()
            for val in rowdata:
                if val.strip() != '':
                    emptyrow = False
                    break
            self.rowcnt += 1

        if emptyrow:
            raise StopIteration()

        if len(rowdata) != len(self.colnames):
            raise RuntimeError(
                'The number of column names in the header of the CSV file '
                '"{0}" does not match the number of fields in row '
                '{1}.'.format(self.getFileName(), self.rowcnt)
            )

        trow = TableRow(
            self.rowcnt, self,
            self.required_cols, self.optional_cols, self.defaultvals
        )
        for colnum in range(len(rowdata)):
            trow[self.colnames[colnum]] = rowdata[colnum]

        return trow


class CSVTableReader(BaseTableReader):
    """
    Reads a table of values from a CSV file.
    """
    def __init__(self, filepath):
        BaseTableReader.__init__(self)

        self.filename = filepath

        # We need to use universal newline mode because at least some mac
        # software will still produce CSV files that use '\r' (carriage return)
        # line endings.
        self.filein = open(filepath, 'rU')

        # Use a standard table name.
        self.tablename = 'table'

        self.numtables = 1

    def getTableByIndex(self, index):
        if index != 0:
            raise KeyError(
                '{0} is an invalid table index for the file "{1}".  The only '
                'valid table index for CSV files is 0.'.format(
                    index, self.filename
                )
            )

        self.filein.seek(0)
        self.csvr = UnicodeCSVReader(self.filein)

        # Get the single table from the input source.
        return _CSVTable(self.csvr, self.tablename, self)

    def getTableByName(self, tablename):
        if tablename != self.tablename:
            raise KeyError(
                '"{0}" is an invalid table name for the file "{1}".'.format(
                    tablename, self.filename
                )
            )

        return self.getTableByIndex(0)

    def close(self):
        self.filein.close()

