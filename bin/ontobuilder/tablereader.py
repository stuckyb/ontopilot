
# Python imports.
import csv
import logging

# Java imports.
# The obvious way to support ODF spreadsheet documents (as produced, e.g., by
# LibreOffice and OpenOffice) would be with the ezodf package in Python.
# Unfortunately, this package requires the lxml package, which requires a
# compiled C library.  Thus, it cannot run on the JVM, which means it won't
# work with Jython.  The best alternative I could come up with was to use a
# Java ODF library.
from java.io import File
from org.jopendocument.dom.spreadsheet import SpreadSheet


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
    def __init__(self, required_cols=[], optional_cols=[], default_vals={}):
        # Required columns.
        self.required = required_cols

        # Columns which are optional: no exception will be raised and no
        # warning will be issued if one of these columns is missing.
        self.optional = optional_cols

        # A dictionary for storing the data values.
        self.data = {}

        # Default column values.
        self.defaults = default_vals

    def __setitem__(self, colname, value):
        self.data[colname.lower()] = value.strip()

    def __getitem__(self, colname):
        """
        Retrieves an item from the table row using a column name as an index.
        If the column is missing and required, an exception is raised.  If the
        missing column is optional, not exception is raised and no warning is
        issued.  If the missing column is neither required nor optional, a
        warning is issued.
        """
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
                if colname not in self.optional:
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


class _BaseTable:
    """
    Base class for a single table in an input data file.
    """
    def __init__(self, tablename, required_cols=[], optional_cols=[], default_vals={}):
        self.name = tablename

        # Required columns.
        self.required_cols = required_cols

        # Columns which are optional: no exception will be raised and no
        # warning will be issued if one of these columns is missing.
        self.optional_cols = optional_cols

        # Default column values.
        self.defaultvals = default_vals

        self.rowcnt = 0

    def setRequiredColumns(self, colnames):
        """
        Sets the column names that are required in the input CSV file.  If one
        or more of these columns are missing, an exception will be thrown.
        Note, however, that required column checking is "lazy": columns are
        only checked when they are accessed.  In other words, if a required
        column is missing in an input file, but no data from that column are
        ever accessed, then no exception will be raised.

        colnames: A list of column names (strings).
        """
        # Make sure all column names are lower case so comparisons in _TableRow
        # are not case sensitive.  From a modularity standpoint, this should be
        # done in _TableRow, but it is more efficient to do it here, since the
        # conversion need be done only once.
        self.required_cols = [colname.lower() for colname in colnames]

    def setOptionalColumns(self, colnames):
        """
        Sets the column names that are optional in the input CSV file.  If one
        or more of these columns are missing, no exception will be thrown and
        no warning will be issued.  Access to missing columns that are neither
        required nor optional will result in a warning being issued.

        colnames: A list of column names (strings).
        """
        # Make sure all column names are lower case so comparisons in _TableRow
        # are not case sensitive.  From a modularity standpoint, this should be
        # done in _TableRow, but it is more efficient to do it here, since the
        # conversion need be done only once.
        self.optional_cols = [colname.lower() for colname in colnames]

    def setDefaultValues(self, defaultvals):
        """
        Sets default values for one or more columns.  If a non-required column
        is missing, the default value will be returned.  An empty string ('')
        is the default default value.

        defaultvals: A dictionary mapping column names to default values.
        """
        # Add lower-case versions of all column names to the dictionary to
        # ensure that comparisions in _TableRow are not case sensitive.  From a
        # modularity standpoint, this should be done in _TableRow, but it is
        # more efficient to do it here rather than each time a _TableRow is
        # instantiated.
        for colname in defaultvals:
            defaultvals[colname.lower()] = defaultvals[colname]

        self.defaultvals = defaultvals

    def __iter__(self):
        return self

    def next(self):
        """
        Allows iteration through each row of the table.  This needs to be
        overridden in child classes.
        """
        raise StopIteration()


class _BaseTableReader:
    """
    A base class for all table readers.
    """
    def __init__(self):
        self.numtables = 0
        self.curr_table = -1

    def getTableByIndex(self, index):
        """
        Retrieves a table from the source document according to an integer
        index.  Must be implemented by child classes.
        """
        pass

    def getTableByName(self, tablename):
        """
        Retrieves a table from the source document according to a string index.
        Must be implemented by child classes.
        """
        pass

    def __enter__(self):
        """
        Enter portion of the context manager interface.
        """
        return self

    def __exit__(self, etype, value, traceback):
        """
        Exit portion of the context manager interface.  Might need to be
        implemented by child classes.
        """
        pass

    def __iter__(self):
        self.curr_table = -1

        return self

    def next(self):
        """
        Allows iteration through the set of tables in the input source.
        """
        self.curr_table += 1

        if self.curr_table == self.numtables:
            raise StopIteration()
        else:
            return self.getTableByIndex(self.curr_table)


class _CSVTable(_BaseTable):
    """
    Represents a single table in a CSV file.  _CSVTable assumes that the first
    row of the file contains the column names.  Each subsequent row is returned
    as a _TableRow object; thus, column names are not case sensitive.
    """
    def __init__(self, csvreader, tablename, required_cols=[], optional_cols=[], default_vals={}):
        _BaseTable.__init__(self, tablename, required_cols, optional_cols, default_vals)

        self.csvr = csvreader

        # Get the column names from the input CSV file.
        try:
            self.colnames = self.csvr.next()
        except StopIteration:
            raise RuntimeError('The input CSV file, "' + self.name
                    + '", is empty.')

        self.rowcnt = 1

        # Trim the column names and make sure they are unique.
        nameset = set()
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip().lower()
            if self.colnames[colnum] in nameset:
                raise RuntimeError('The column name "' + self.colnames[colnum]
                    + '" is used more than once in the input CSV file, "'
                    + self.name + '".  All column names must be unique.')
            else:
                nameset.add(self.colnames[colnum])

    def next(self):
        """
        Allows iteration through each row of the CSV file.
        """
        rowdata = self.csvr.next()
        self.rowcnt += 1

        if len(rowdata) != len(self.colnames):
            raise RuntimeError(
                'The number of column names in the header of the CSV file "'
                + self.name + '" does not match the number of fields in row '
                + str(self.rowcnt) + '.'
            )

        trow = _TableRow(self.required_cols, self.optional_cols, self.defaultvals)
        for colnum in range(len(rowdata)):
            trow[self.colnames[colnum]] = rowdata[colnum]

        return trow


class CSVTableReader(_BaseTableReader):
    """
    Reads a table of values from a CSV file.
    """
    def __init__(self, filepath):
        _BaseTableReader.__init__(self)

        self.filename = filepath
        self.filein = open(filepath, 'r')

        # Use the file name as the table name.
        self.tablename = self.filename

        self.numtables = 1

    def getTableByIndex(self, index):
        if index != 0:
            raise KeyError('Invalid table index ' + str(index)
                    + ' for the file "' + self.filename + '".')

        self.filein.seek(0)
        self.csvr = csv.reader(self.filein)

        # Get the single table from the input source.
        return _CSVTable(self.csvr, self.filename)

    def getTableByName(self, tablename):
        if tablename != self.tablename:
            raise KeyError('Invalid table name "' + str(tablename)
                    + '" for the file "' + self.filename + '".')

        return self.getTableByIndex(0)

    def __exit__(self, etype, value, traceback):
        self.filein.close()


class _ODFTable(_BaseTable):
    """
    Represents a single table (i.e., sheet) in an ODF spreadsheet file.
    _CSVTable assumes that the first row of the sheet contains the column
    names.  Each subsequent row is returned as a _TableRow object; thus, column
    names are not case sensitive.
    """
    def __init__(self, odfsheet, filename, required_cols=[], optional_cols=[], default_vals={}):
        _BaseTable.__init__(self, odfsheet.getName(), required_cols, optional_cols, default_vals)

        self.sheet = odfsheet
        self.filename = filename

        # If the spreadsheet includes cells that contain no data, but to which
        # formatting was applied, then the number of defined rows and/or
        # columns (as returned, e.g., by self.sheet.getRowCount()) can be much
        # greater than the range of rows and columns that actually contain
        # data.  Thus, we use the "used range" rather than the raw row and
        # column counts to define the number of rows and columns in the
        # spreadsheet.  The second sheet ("Sheet2") of the valid test data file
        # is an example of a sheet that has "spurious" rows and column caused
        # by defining formatting styles with no data.  This sheet is a
        # worst-case scenario, because *every* cell in the spreadsheet has a
        # formatting style applied to it, which means the numbers of rows and
        # columns are as large as possible.
        usedrange = self.sheet.getUsedRange(False)
        if usedrange == None:
            raise RuntimeError('The input ODF spreadsheet "' + self.name
                    + '" in the file "' + self.filename + '" is empty.')
        self.numrows = usedrange.getEndPoint().y + 1
        self.numcols = usedrange.getEndPoint().x + 1
        #print 'RAW ROW COUNT:', self.sheet.getRowCount()
        #print 'RAW COLUMN COUNT:', self.sheet.getColumnCount()
        #print 'USED ROW COUNT:', self.numrows
        #print 'USED COLUMN COUNT:', self.numcols

        # Get the column names from the sheet.
        self.colnames = []
        for colnum in range(self.numcols):
            self.colnames.append(self.sheet.getImmutableCellAt(colnum, 0).getTextValue())
        self.rowcnt = 1

        # Trim the column names and make sure they are unique.
        nameset = set()
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip().lower()
            if self.colnames[colnum] in nameset:
                raise RuntimeError('The column name "' + self.colnames[colnum]
                    + '" is used more than once in the input ODF spreadsheet "'
                    + self.name + '" in the file "' + self.filename
                    + '".  All column names must be unique.')
            else:
                nameset.add(self.colnames[colnum])

    def next(self):
        """
        Allows iteration through each row of the ODF spreadsheet table. Empty
        rows are ignored.
        """
        # Find the next non-empty row.  After the loop, self.rowcnt will be one
        # row beyond the next non-empty row (if the search succeeded).
        emptyrow = True
        while (self.rowcnt < self.numrows) and emptyrow:
            for colnum in range(self.numcols):
                if self.sheet.getImmutableCellAt(colnum, self.rowcnt).getTextValue() != '':
                    emptyrow = False
                    break
            self.rowcnt += 1

        if emptyrow:
            raise StopIteration()

        trow = _TableRow(self.required_cols, self.optional_cols, self.defaultvals)
        for colnum in range(self.numcols):
            # Uncomment the following line to print the ODF value type for each
            # data cell.
            # print self.sheet.getImmutableCellAt(colnum, self.rowcnt - 1).getValueType()
            trow[self.colnames[colnum]] = self.sheet.getImmutableCellAt(colnum, self.rowcnt - 1).getTextValue()

        return trow


class ODFTableReader(_BaseTableReader):
    """
    Reads tables (i.e., sheets) from an ODF spreadsheet file (as produced,
    e.g., by LibreOffice and OpenOffice).
    """
    def __init__(self, filepath):
        _BaseTableReader.__init__(self)

        self.filename = filepath
        self.filein = File(filepath)
        self.odfs = SpreadSheet.createFromFile(self.filein)
        self.numtables = self.odfs.getSheetCount()

    def getTableByIndex(self, index):
        if (index < 0) or (index >= self.numtables):
            raise KeyError('Invalid table index:' + str(index)
                    + '.  No matching sheet could be found in the file "'
                    + self.filename + '".')

        return _ODFTable(self.odfs.getSheet(index), self.filename)

    def getTableByName(self, tablename):
        sheet = self.odfs.getSheet(tablename)
        if sheet == None:
            raise KeyError('Invalid table name: "' + str(tablename)
                    + '".  No matching sheet could be found in the file "'
                    + self.filename + '".')

        table = _ODFTable(sheet, self.filename)

        return table

