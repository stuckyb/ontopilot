
# Python imports.
import abc
import logging

# Java imports.


class ColumnNameError(RuntimeError):
    """
    Exception class for missing required columns.
    """
    pass


class TableRow:
    """
    Provides an interface to a single row in a table.  Columns are indexed by
    their names, and column names are not case sensitive.  Setting and
    retrieving column values is done using subscript notation, just as for a
    dictionary.  _TableRow also supports specifying required and optional
    columns and default column values.  All row data values will be trimmed to
    remove leading and/or trailing whitespace.  In general, this class should
    not be instantiated directly; rather, instances should be obtained from one
    of the TableReader classes.
    """
    def __init__(self, rownum, filename, required_cols=[], optional_cols=[], default_vals={}):
        self.rownum = rownum
        self.filename = filename

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

    def __str__(self):
        metadata = 'row {0} in "{1}":\n'.format(
            self.getRowNum(), self.getFileName()
        )

        return metadata + str(self.data)

    def getRowNum(self):
        return self.rownum

    def getFileName(self):
        return self.filename


class BaseTable:
    """
    Base class for a single table in an input data file.  This is an abstract
    base class and should not be instantiated directly.
    """
    def __init__(self, tablename, required_cols=[], optional_cols=[], default_vals={}):
        # This is an abstract base class.
        __metaclass__ = abc.ABCMeta

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

    @abc.abstractmethod
    def next(self):
        """
        Allows iteration through each row of the table.  This needs to be
        overridden in child classes.
        """
        pass


class BaseTableReader:
    """
    An abstract base class for all table readers.
    """
    def __init__(self):
        # This is an abstract base class.
        __metaclass__ = abc.ABCMeta

        self.numtables = 0
        self.curr_table = -1

    def getNumTables(self):
        return self.numtables

    @abc.abstractmethod
    def getTableByIndex(self, index):
        """
        Retrieves a table from the source document according to an integer
        index.  Must be implemented by child classes.
        """
        pass

    @abc.abstractmethod
    def getTableByName(self, tablename):
        """
        Retrieves a table from the source document according to a string index.
        Must be implemented by child classes.
        """
        pass

    def close(self):
        """
        Closes the file associated with this TableReader.  Does nothing by
        default; so might need to be overriden by child classes.
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

