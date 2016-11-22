
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
        # A list of tables in the input source.
        self.tables = []
        # A dictionary mapping table names to indices in the table list.
        self.tablename_map = {}

        self.curr_table = -1

    def getTableByIndex(self, index):
        return self.tables[index]

    def getTableByName(self, tablename):
        return self.tables[self.tablename_map[tablename]]

    def __iter__(self):
        return self

    def next(self):
        """
        Allows iteration through the set of tables in the input source.
        """
        self.curr_table += 1

        if self.curr_table == len(self.tables):
            raise StopIteration()
        else:
            return self.tables[self.curr_table]


class _CSVTable(_BaseTable):
    """
    Represents a single table in a CSV file.
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

        # Trim the column names and make sure none are empty.
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip()
            if self.colnames[colnum] == '':
                raise RuntimeError('The input CSV file, "' + self.name
                    + '", has one or more empty column names.')

        self.rowcnt = 1

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
    Reads a table of values from a CSV file.  CSVTableReader assumes that the
    first row of the file contains the column names.  Each subsequent row is
    returned as a _TableRow object; thus, column names are not case sensitive.
    """
    def __init__(self, filein):
        _BaseTableReader.__init__(self)

        self.csvr = csv.reader(filein)
        self.filename = filein.name

        # A list of tables in the input source.
        self.tables = [_CSVTable(self.csvr, self.filename)]
        # A dictionary mapping table names to indices in the table list.
        self.tablename_map = {self.filename: 0}

