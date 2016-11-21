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


from ontobuilder.tablereader import _TableRow, ColumnNameError, CSVTableReader
import unittest


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
        # Test missing required column.
        with self.assertRaises(ColumnNameError):
            self.tr['col1']


class TestCSVTableReader(unittest.TestCase):
    """
    Tests the CSVTableReader class.
    """
    tr = None

    # The expected values from the table test files.  The casing of the column
    # names varies to test that the returned table rows are not case sensitive.
    testvals = (
        {'COL1': 'data 1', 'COLUMN 2':'extra whitespace!', 'COL3':'data2'},
        {'col1': 'the', 'column 2':'last', 'col3':'row'}
    )

    def _openFile(self, filename):
        self.fin = open(filename)
        self.tr = CSVTableReader(self.fin)

    def tearDown(self):
        self.fin.close()

    def test_iteration(self):
        self._openFile('test_data/test_table-valid.csv')

        rowcnt = 0
        for row in self.tr:
            rowcnt += 1

        self.assertEqual(rowcnt, 2)

    def test_read(self):
        self._openFile('test_data/test_table-valid.csv')

        for exprow, row in zip(self.testvals, self.tr):
            for colname in exprow:
                self.assertEqual(exprow[colname], row[colname])

    def test_colnumErrors(self):
        """
        Tests errors caused by the number of columns in a row not being equal
        to the number of columns found in the header.
        """
        self._openFile('test_data/test_table-colnum_error.csv')

        # Read a row that is too short.
        with self.assertRaises(RuntimeError):
            self.tr.next()

        # Read a row that is too long.
        with self.assertRaises(RuntimeError):
            self.tr.next()

    def test_requiredAndOptional(self):
        """
        Tests that required column names are handled properly.
        """
        self._openFile('test_data/test_table-valid.csv')
        self.tr.setRequiredColumns(['col1', 'col4', 'COL5'])
        self.tr.setOptionalColumns(['col6'])

        row = self.tr.next()

        # These should not trigger exceptions.
        row['col1']
        row['col6']

        # Reference missing required columns, including a test to make sure
        # that column specification is not case sensitive.
        with self.assertRaises(RuntimeError):
            row['col4']
        with self.assertRaises(RuntimeError):
            row['col5']

    def test_defaults(self):
        """
        Tests setting and using default column values.
        """
        self._openFile('test_data/test_table-valid.csv')
        self.tr.setOptionalColumns(['col4', 'col5', 'col6'])
        self.tr.setDefaultValues({'col4': 'default 1', 'COL5': 'default2'})

        row = self.tr.next()

        # Test explicitly specified defaults, including a test to make sure
        # that default value column names are not case sensitive.
        self.assertEqual(row['col4'], 'default 1')
        self.assertEqual(row['col5'], 'default2')

        # Test the default default value.
        self.assertEqual(row['col6'], '')

