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


#
# This module includes tests for all classes related to reading input data
# tables, including concrete implementations of BaseTable and BaseTableReader.
#

from ontopilot.tablereader import TableRow, TableRowError, ColumnNameError
from ontopilot.tablereaderfactory import TableReaderFactory
from ontopilot.tablereader_csv import CSVTableReader
from ontopilot.tablereader_odf import ODFTableReader
from ontopilot.tablereader_excel import ExcelTableReader
import unittest
from testfixtures import LogCapture


class TestTableReaderFactory(unittest.TestCase):
    """
    Tests the TableReaderFactory class.
    """
    def test_tableReaderFactory(self):
        with TableReaderFactory('test_data/test_table-valid.csv') as t_reader:
            self.assertEqual(t_reader.getNumTables(), 1)

        with TableReaderFactory('test_data/test_table-valid.ods') as t_reader:
            self.assertEqual(t_reader.getNumTables(), 2)

        with self.assertRaisesRegexp(
            RuntimeError,
            'The type of the input file .* could not be determined'
        ):
            TableReaderFactory('unknown_type.blah').__enter__()


# Define two simple stub classes to provide the BaseTable and BaseTableReader
# functionality that TableRowError and TableRow need.  This could be done more
# neatly using the mock package, but in this case, the additional package
# installations probably aren't worth it.
class TableReaderStub:
    numtables = 1
    def getNumTables(self):
        return self.numtables

class TableStub:
    def __init__(self):
        self.t_reader = TableReaderStub()
    def getFileName(self):
        return 'mock_file'
    def getTableName(self):
        return 'mock_table'
    def getTableReader(self):
        return self.t_reader


class TestTableRowError(unittest.TestCase):
    """
    Tests TableRowError to verify that error context information is correctly
    reported.
    """
    def setUp(self):
        self.tr = TableRow(1, TableStub())
        self.errobj = TableRowError('Sample message.', self.tr)

    def test__generateContextStr(self):
        """
        Verifies that context messages are correct for data sources with only
        one table or with multiple named tables.
        """
        # Mimic a data source with only 1 table.
        self.assertEqual(
            'row 1 of "mock_file"', self.errobj._generateContextStr(self.tr)
        )

        # Mimic a data source with more than 1 table.
        self.tr.getTable().getTableReader().numtables = 2
        self.assertEqual(
            'row 1 of table "mock_table" in "mock_file"',
            self.errobj._generateContextStr(self.tr)
        )


class TestTableRow(unittest.TestCase):
    """
    Tests the TableRow class.
    """
    def setUp(self):
        self.required = ['col1']
        self.optional = ['col2', 'col3', 'col4', 'col5']
        self.defaults = {'col3': 'default1', 'col4': 'default2'}

        self.tr = TableRow(1, TableStub(), self.required, self.optional, self.defaults)

    def test_setGetContains(self):
        self.tr['Col1'] = 'testval'

        # Make sure that inclusion testing works and is not case sensitive.
        self.assertFalse('col2' in self.tr)
        self.assertTrue('Col1' in self.tr)
        self.assertTrue('COL1' in self.tr)
        self.assertTrue('col1' in self.tr)

        # Make sure that retrieval works and is not case sensitive.
        self.assertEqual('testval', self.tr['Col1'])
        self.assertEqual('testval', self.tr['COL1'])
        self.assertEqual('testval', self.tr['col1'])

    def test_defaults(self):
        # Columns for which default values were provided.
        self.assertEqual(self.tr['col3'], 'default1')
        self.assertEqual(self.tr['col4'], 'default2')

        # Column for which no default was provided.
        self.assertEqual(self.tr['col5'], '')

    def test_missing(self):
        # Test a missing required column.
        with self.assertRaises(ColumnNameError):
            self.tr['col1']

        # Test a column that should trigger a warning.
        with LogCapture() as lc:
            self.tr['col6']
        lc.check((
            'ontopilot', 'WARNING',
            'The column "col6" was missing in the table row.'
        ))

        # Test support for making all non-required columns optional.
        self.tr.optional = [0]
        with LogCapture() as lc:
            self.tr['col6']
        # No warnings should have been issued.
        self.assertEqual(0, len(lc.records))

        # A missing required column should still trigger an error.
        with self.assertRaises(ColumnNameError):
            self.tr['col1']

    def test_iteration(self):
        """
        Tests that iteration through the column names (keys) works properly.
        """
        self.tr['col1'] = 'val1'
        self.tr['col2'] = 'val2'
        self.tr['col3'] = 'val3'

        exp_keys = ['col1', 'col2', 'col3']
        result = []
        for key in self.tr:
            result.append(key)

        self.assertEqual(exp_keys, sorted(result))


class _TestTableReader:
    """
    Defines tests that apply to all concrete subclasses of _BaseTableReader.
    This class should not be instantiated directly; only its subclasses that
    target concrete subclasses of _BaseTableReader should be run.  To help
    reinforce this, _TestTableReader does not inherit from unittest.TestCase.
    All subclasses of _TestTableReader should inherit from unittest.TestCase
    and treat _TestTableReader as a sort of "mixin" class that provides
    standard testing routines.
    """
    tr = None

    def setUp(self):
        # Calculate the expected number of tables and the total row count.
        self.exp_tablecnt = 0
        self.exp_rowcnt = 0
        for tname in self.expvals:
            self.exp_tablecnt += 1
            for row in self.expvals[tname]:
                self.exp_rowcnt += 1

    def tearDown(self):
        self.tr.close()

    def test_retrieveTable(self):
        """
        Test retrieving tables by index and by name.
        """
        self._openFile(self.valid_input_testfile)

        self.assertEqual(self.tr.numtables, self.exp_tablecnt)

        tname = self.tr.getTableByIndex(0).name
        self.assertEqual(self.tr.getTableByName(tname).name, tname)

    def test_iteration(self):
        """
        Test that iteration over tables in a TableReader and rows in a Table
        behave as expected.
        """
        self._openFile(self.valid_input_testfile)

        tablecnt = 0
        rowcnt = 0
        for table in self.tr:
            tablecnt += 1
            for row in table:
                rowcnt += 1

        self.assertEqual(tablecnt, self.exp_tablecnt)
        self.assertEqual(rowcnt, self.exp_rowcnt)

    def test_read(self):
        """
        Read all data from the input file, comparing the results to the
        expected data values.
        """
        self._openFile(self.valid_input_testfile)
        
        self.assertEqual(self.tr.getNumTables(), self.exp_tablecnt)

        for tname in self.expvals:
            table = self.tr.getTableByName(tname)
            for exprow, row, exp_rownum in zip(self.expvals[tname], table, self.exp_rownums[tname]):
                # Make sure the file name and row number are correct.
                self.assertEqual(exp_rownum, row.getRowNum())
                self.assertEqual(self.valid_input_testfile, row.getFileName())
                # Make sure the row values are correct.
                for colname in exprow:
                    self.assertEqual(exprow[colname], row[colname])

    def test_requiredAndOptional(self):
        """
        Tests that required column names are handled properly.
        """
        self._openFile(self.valid_input_testfile)
        table = self.tr.next()

        table.setRequiredColumns(['col1', 'col4', 'COL5'])
        table.setOptionalColumns(['col6'])

        row = table.next()

        # These should not trigger exceptions.
        row['col1']
        row['col6']

        # Reference missing required columns, including a test to make sure
        # that column specification is not case sensitive.
        with self.assertRaises(RuntimeError):
            row['col4']
        with self.assertRaises(RuntimeError):
            row['col5']

        # Reference a column that should trigger a warning.
        with LogCapture() as lc:
            row['column 7']
        lc.check((
            'ontopilot', 'WARNING',
            'The column "column 7" was missing in the table row.'
        ))

        # Now test making all non-required columns optional.
        table.setOptionalColumns([0])
        row = table.next()

        # This should no longer trigger a warning.
        row['column 7']

    def test_defaults(self):
        """
        Tests setting and using default column values.
        """
        self._openFile(self.valid_input_testfile)
        table = self.tr.next()

        table.setOptionalColumns(['col4', 'col5', 'col6'])
        table.setDefaultValues({'col4': 'default 1', 'COL5': 'default2'})

        row = table.next()

        # Test explicitly specified defaults, including a test to make sure
        # that default value column names are not case sensitive.
        self.assertEqual(row['col4'], 'default 1')
        self.assertEqual(row['col5'], 'default2')

        # Test the default default value.
        self.assertEqual(row['col6'], '')


class TestCSVTableReader(_TestTableReader, unittest.TestCase):
    """
    Tests the CSVTableReader class.
    """
    # The expected values from the CSV test file.
    expvals = {
        # Vary the casing of the column names to test that the returned table
        # rows are not case sensitive.  The test file includes an empty row in
        # between the two data-containing rows; the empty row should be
        # ignored.
        'table': (
            {'COL1': 'data 1', 'COLUMN 2':'extra whitespace!', 'COL3':'data2'},
            {
                # The 1st cell of row 2 is a unicode lower-case Greek alpha.
                'col1': unicode('\xce\xb1', 'utf-8'),
                'column 2':'unicode', 'col3':'row'
            }
        )
    }

    # The number of each data-containing row in each table of the test file,
    # with counting starting at 1.
    exp_rownums = {
        'table': (2, 4)
    }

    valid_input_testfile = 'test_data/test_table-valid.csv'

    def _openFile(self, filename):
        self.tr = CSVTableReader(filename)

    def test_errors(self):
        """
        Tests a variety of error conditions.
        """
        self._openFile('test_data/test_table-colnum_errors.csv')

        # Use an invalid table index and name.
        with self.assertRaises(KeyError):
            self.tr.getTableByIndex(1)
        with self.assertRaises(KeyError):
            self.tr.getTableByName('nonexistant')

        # Test errors caused by the number of columns in a row not being equal
        # to the number of columns found in the header.
        table = self.tr.next()

        # Read a row that is too short.
        with self.assertRaisesRegexp(RuntimeError, 'The number of column names .* does not match'):
            table.next()

        # Read a row that is too long.
        with self.assertRaisesRegexp(RuntimeError, 'The number of column names .* does not match'):
            table.next()

        # Try loading a table with non-unique column names.  The test data is
        # such that this also tests that checking for unique column names is
        # not case sensitive.
        self._openFile('test_data/test_table-invalid_colnames.csv')
        with self.assertRaisesRegexp(RuntimeError, 'The column name "col1" is used more than once'):
            self.tr.next()

        # Try loading a table that is completely empty.
        self._openFile('test_data/test_table-empty.csv')
        with self.assertRaisesRegexp(RuntimeError, 'The input CSV file .* is empty.'):
            self.tr.getTableByIndex(0)


class TestODFTableReader(_TestTableReader, unittest.TestCase):
    """
    Tests the ODFTableReader class.
    """
    # The expected values from the ODF test file.  Both sheets in the test file
    # include a huge number of empty cells that nevertheless count as defined
    # rows and columns because they have explicit style formatting.  These
    # should be ignored by the table reader.
    expvals = {
        # Vary the casing of the column names to test that the returned table
        # rows are not case sensitive.  The first sheet in the test file
        # includes an empty row in between the two data-containing rows; the
        # empty row should be ignored.
        'sheet 1': (
            {'COL1': 'data 1', 'COLUMN 2':'extra whitespace!', 'COL3':'data2'},
            {
                # The 1st cell of row 2 is a unicode lower-case Greek alpha.
                'col1': unicode('\xce\xb1', 'utf-8'),
                'column 2':'unicode', 'col3':'row'
            }
        ),
        # The second sheet in the test file includes date and time types.
        'Sheet2': (
            {'date val': 'Nov. 24, 2016', 'time val': '01:22:00 PM', 'one more': '123'},
            {'date val': '1/20/2017', 'time val': '14:50', 'one more': '12.123'}
        )
    }

    # The number of each data-containing row in each table of the test file,
    # with counting starting at 1.
    exp_rownums = {
        'sheet 1': (2, 4),
        'Sheet2': (2,)
    }

    valid_input_testfile = 'test_data/test_table-valid.ods'

    def _openFile(self, filename):
        self.tr = ODFTableReader(filename)

    def test_errors(self):
        """
        Tests a variety of error conditions.
        """
        self._openFile('test_data/test_table-error.ods')

        # Use an invalid table index and name.
        with self.assertRaises(KeyError):
            self.tr.getTableByIndex(2)
        with self.assertRaises(KeyError):
            self.tr.getTableByName('nonexistant')

        # Try loading a table with non-unique column names.  The test data is
        # such that this also tests that checking for unique column names is
        # not case sensitive.
        with self.assertRaisesRegexp(RuntimeError, 'The column name "col1" is used more than once'):
            self.tr.next()

        # Try loading a table that is completely empty.
        with self.assertRaisesRegexp(RuntimeError, 'The input ODF spreadsheet .* empty.'):
            self.tr.getTableByIndex(1)


class TestExcelTableReader(_TestTableReader):
    """
    Tests the ExcelTableReader class.  Note this class does not inherit from
    unittest.TestCase, because we need two concrete subclasses, one for XLS
    (Excel 97-2003) documents and one for XLSX (Excel 2007+) documents.  These
    two subclasses will inherit from unittest.TestCase, and they are
    dynamically generated using a simple implementation of test
    parameterization; see code below this class.
    """
    # The expected values from the Excel test file.  Both sheets in the test
    # file include a huge number of empty cells that nevertheless have explicit
    # style formatting.  These should be ignored by the table reader.
    expvals = {
        # Vary the casing of the column names to test that the returned table
        # rows are not case sensitive.  The first sheet in the test file
        # includes an empty row in between the two data-containing rows; the
        # empty row should be ignored.
        'sheet 1': (
            {'COL1': 'data 1', 'COLUMN 2':'extra whitespace!', 'COL3':'data2'},
            {
                # The 1st cell of row 2 is a unicode lower-case Greek alpha.
                'col1': unicode('\xce\xb1', 'utf-8'),
                'column 2':'unicode', 'col3':'row'
            }
        ),
        # The second sheet in the test file includes date, time, and number
        # types.
        'Sheet2': (
            {'date val': 'Nov. 24, 2016', 'time val': '01:22:00 PM', 'one more': '123'},
            {'date val': '1/20/2017', 'time val': '14:50', 'one more': '12.123'}
        )
    }

    # The number of each data-containing row in each table of the test file,
    # with counting starting at 1.
    exp_rownums = {
        'sheet 1': (2, 4),
        'Sheet2': (2,)
    }

    # These should be overridden by child classes to provide the paths to the
    # test data files.
    valid_input_testfile = None
    error_input_testfile = None

    def _openFile(self, filename):
        self.tr = ExcelTableReader(filename)

    def test_errors(self):
        """
        Tests a variety of error conditions.
        """
        self._openFile(self.error_input_testfile)

        # Use an invalid table index and name.
        with self.assertRaises(KeyError):
            self.tr.getTableByIndex(2)
        with self.assertRaises(KeyError):
            self.tr.getTableByName('nonexistant')

        # Try loading a table with non-unique column names.  The test data is
        # such that this also tests that checking for unique column names is
        # not case sensitive.
        with self.assertRaisesRegexp(RuntimeError, 'The column name "col1" is used more than once'):
            self.tr.next()

        # Try loading a table that is completely empty.
        with self.assertRaisesRegexp(RuntimeError, 'The input Excel spreadsheet .* empty.'):
            self.tr.getTableByIndex(1)


# Python's unittest does not support parameterized tests, so we mimic it here
# by using the type() function to dynamically generate two concrete testing
# classes: one for XLS documents (Excel 97-2003), and one for XLSX documents
# (Excel 2007+).  Each class will have custom values for the
# 'valid_input_testfile' and 'error_input_testfile' attributes that provide the
# correct test data file names.
excel_test_params = (
    ('XLS', ('test_data/test_table-valid.xls', 'test_data/test_table-error.xls')),
    ('XLSX', ('test_data/test_table-valid.xlsx', 'test_data/test_table-error.xlsx'))
)
for clname_suffix, filenames in excel_test_params:
    clname = 'TestExcelTableReader_' + clname_suffix
    globals()[clname] = type(
        clname, (TestExcelTableReader, unittest.TestCase), {
            'valid_input_testfile': filenames[0],
            'error_input_testfile': filenames[1]
        }
    )

