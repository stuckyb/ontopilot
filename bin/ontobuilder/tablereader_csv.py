
# Python imports.
import csv
from tablereader import TableRow, BaseTable, BaseTableReader

# Java imports.


class _CSVTable(BaseTable):
    """
    Represents a single table in a CSV file.  _CSVTable assumes that the first
    row of the file contains the column names.  Each subsequent row is returned
    as a TableRow object; thus, column names are not case sensitive.
    """
    def __init__(self, csvreader, tablename, filename, required_cols=[], optional_cols=[], default_vals={}):
        BaseTable.__init__(self, tablename, required_cols, optional_cols, default_vals)

        self.csvr = csvreader
        self.filename = filename

        # Get the column names from the input CSV file.
        try:
            self.colnames = self.csvr.next()
        except StopIteration:
            raise RuntimeError('The input CSV file "' + self.filename
                    + '" is empty.')

        self.rowcnt = 1

        # Trim the column names and make sure they are unique.
        nameset = set()
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip().lower()
            if self.colnames[colnum] in nameset:
                raise RuntimeError('The column name "' + self.colnames[colnum]
                    + '" is used more than once in the input CSV file "'
                    + self.filename + '".  All column names must be unique.')
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
                'The number of column names in the header of the CSV file "'
                + self.filename + '" does not match the number of fields in row '
                + str(self.rowcnt) + '.'
            )

        trow = TableRow(
            self.rowcnt, self.filename,
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
        self.filein = open(filepath, 'r')

        # Use a standard table name.
        self.tablename = 'table'

        self.numtables = 1

    def getTableByIndex(self, index):
        if index != 0:
            raise KeyError('Invalid table index ' + str(index)
                    + ' for the file "' + self.filename + '".')

        self.filein.seek(0)
        self.csvr = csv.reader(self.filein)

        # Get the single table from the input source.
        return _CSVTable(self.csvr, self.tablename, self.filename)

    def getTableByName(self, tablename):
        if tablename != self.tablename:
            raise KeyError('Invalid table name "' + str(tablename)
                    + '" for the file "' + self.filename + '".')

        return self.getTableByIndex(0)

    def close(self):
        self.filein.close()

