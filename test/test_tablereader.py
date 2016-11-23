# Copyright (C) 2016 Brian J. Stucky
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


from ontobuilder.tablereader import _TableRow, ColumnNameError
from ontobuilder.tablereader import CSVTableReader, ODFTableReader
import unittest
from testfixtures import LogCapture


class TestTableRow(unittest.TestCase):
    """
    Tests the _TableRow class.
    """
    def setUp(self):
        self.required = ['col1']
        self.optional = ['col2', 'col3', 'col4', 'col5']
        self.defaults = {'col3': 'default1', 'col4': 'default2'}

        self.tr = _TableRow(self.required, self.optional, self.defaults)

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
            'root', 'WARNING',
            'The column "col6" was missing in the table row.'
        ))


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
        # Call the exit routine of the TableReader's context manager interface.
        self.tr.__exit__(None, None, None)

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

        for tname in self.expvals:
            table = self.tr.getTableByName(tname)
            for exprow, row in zip(self.expvals[tname], table):
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
            'root', 'WARNING',
            'The column "column 7" was missing in the table row.'
        ))

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
            {'col1': 'the', 'column 2':'last', 'col3':'row'}
        )
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
    # The expected values from the ODF test file.
    expvals = {
        # Vary the casing of the column names to test that the returned table
        # rows are not case sensitive.  The first sheet in the test file
        # includes an empty row in between the two data-containing rows; the
        # empty row should be ignored.
        'sheet 1': (
            {'COL1': 'data 1', 'COLUMN 2':'extra whitespace!', 'COL3':'data2'},
            {'col1': 'the', 'column 2':'last', 'col3':'row'}
        ),
        # The second sheet in the test file includes date and time types as
        # well as a huge number of empty cells that nevertheless count as
        # defined rows and columns because they have explicit style formatting.
        # These should be ignored by the table reader.
        'Sheet2': (
            {'date val': 'Nov. 24, 2016', 'time val': '01:22:00 PM', 'one more': 'Blah!!'},
        )
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
        with self.assertRaisesRegexp(RuntimeError, 'The input ODF spreadsheet .* is empty.'):
            self.tr.getTableByIndex(1)

