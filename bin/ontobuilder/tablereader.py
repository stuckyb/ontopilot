
import csv
import logging


class ColumnNameError(RuntimeError):
    """
    Exception class for missing required columns.
    """
    pass


class _TableRow:
    """
    Provides an abstract interface to a single row in a table.  Columns are
    indexed by their names, and column names are not case sensitive.  Setting
    and retrieving column values is done using subscript notation, just as for
    a dictionary.  _TableRow also supports specifying required and optional
    columns and default column values.  All row data values will be trimmed to
    remove leading and/or trailing whitespace.  This class should not be
    instantiated directly; rather, instances should be obtained from one of the
    TableReader classes.
    """
    def __init__(self, required_cols=[], warning_cols=[], default_vals={}):
        # Required columns.
        self.required = required_cols

        # Columns for which a warning is issued if the column is missing.
        self.warning = warning_cols

        # A dictionary for storing the data values.
        self.data = {}

        # Default column values.
        self.defaults = default_vals

    def __setitem__(self, colname, value):
        self.data[colname.lower()] = value.strip()

    def __getitem__(self, colname):
        colname = colname.lower()

        if colname in self.data:
            return self.data[colname]
        else:
            if colname in self.required:
                raise ColumnNameError(
                    'The required column "' + colname
                    + '" was missing in the table row.'
                )
            else:
                if colname in self.warning:
                    logging.warning(
                        'The column "' + colname
                        + '" was missing in the table row.'
                    )

                if colname in self.defaults:
                    return self.defaults[colname]
                else:
                    return ''

    def __contains__(self, colname):
        return colname.lower() in self.data


class CSVTableReader:
    """
    Reads a table of values from a CSV file.  CSVTable assumes that the first
    row of the file contains the column names.  Each subsequent row is returned
    as a _TableRow object; thus, column names are not case sensitive.
    """
    def __init__(self, filein):
        self.csvr = csv.reader(filein)
        self.filename = filein.name

        try:
            self.colnames = self.csvr.next()
        except StopIteration:
            raise RuntimeError('The input CSV file, "' + self.filename
                    + '", is empty.')

        # Trim the column names and make sure none are empty.
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip()
            if self.colnames[colnum] == '':
                raise RuntimeError('The input CSV file, "' + self.filename
                    + '", has one or more empty column names.')

        self.rowcnt = 1

    def __iter__(self):
        return self

    def next(self):
        rowdata = self.csvr.next()
        self.rowcnt += 1

        if len(rowdata) != len(self.colnames):
            raise RuntimeError(
                'The number of column names in the header of the CSV file "'
                + self.filename + '" does not match the number of fields in row '
                + str(self.rowcnt) + '.'
            )

        trow = _TableRow()
        for colnum in range(len(rowdata)):
            trow[self.colnames[colnum]] = rowdata[colnum]

        return trow

