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
import os
from tablereader import TableRow, BaseTable, BaseTableReader

# Java imports.
# The obvious way to support ODF spreadsheet documents (as produced, e.g., by
# LibreOffice and OpenOffice) would be with the ezodf package in Python.
# Unfortunately, this package requires the lxml package, which requires a
# compiled C library.  Thus, it cannot run on the JVM, which means it won't
# work with Jython.  The best alternative I could come up with was to use a
# Java ODF library.
from java.io import File
from org.jopendocument.dom.spreadsheet import SpreadSheet
from org.jopendocument.dom import ODSingleXMLDocument


class _ODFTable(BaseTable):
    """
    Represents a single table (i.e., sheet) in an ODF spreadsheet file.
    _CSVTable assumes that the first row of the sheet contains the column
    names.  Each subsequent row is returned as a TableRow object; thus, column
    names are not case sensitive.
    """
    def __init__(self, odfsheet, odftablereader, required_cols=[], optional_cols=[], default_vals={}):
        BaseTable.__init__(
            self, odfsheet.getName(), odftablereader,
            required_cols, optional_cols, default_vals
        )

        self.sheet = odfsheet

        # Define the number of consecutive empty rows to be encountered before
        # the remainder of an input sheet is assumed to be empty.
        self.EMPTYROW_LIM = 1000

        # If the spreadsheet includes cells that contain no data, but to which
        # formatting was applied, then the number of defined rows and/or
        # columns (as returned, e.g., by self.sheet.getRowCount()) can be much
        # greater than the range of rows and columns that actually contain
        # data.  This could slow things down considerably since a naive
        # algorithm could be iterating over millions of empty cells.  There are
        # at least three ways to deal with this.  First is to use the
        # getUsedRange() method of the Sheet class to get the range of cells
        # that actually contain data and iterate only over those.  The second
        # option is to inspect the first table row to infer the number of
        # data-containing columns, then skipping empty rows assuming no data
        # are found beyond the used columns in the header row.  This option
        # will still read all the way to the end of the sheet.  A third option,
        # which is a slight modification of option 2, is to stop reading a
        # sheet once a certain number of consecutive empty rows are
        # encountered.  I implemented all three of these options and timed each
        # on the valid test data file running the ODFTableReader unit tests.
        # The first sheet ("sheet 1") of this test file is an example of a
        # sheet that has "spurious" rows and column caused by defining
        # formatting styles with no data.  This sheet is a worst-case scenario,
        # because *every* row and column in the spreadsheet has a formatting
        # style applied to it, which means the numbers of rows and columns are
        # as large as possible (1,024 x 1,048,576; more than 1 billion cells).
        # The results are as follows:
        #
        #   Option 1 (getUsedRange()): 131.1 s
        #   Option 2 (infer column count, skip empty rows): 7.0 s
        #   Option 3 (same as 2, but stop after 1,000 consecutive empty rows): 0.5 s
        #
        # Option 3 should be perfectly reasonable for any real-world input
        # data, and the speed improvement is substantial.
        #
        self.numrows = self.sheet.getRowCount()
        self.numcols = self.sheet.getColumnCount()
        #print 'RAW ROW COUNT:', self.sheet.getRowCount()
        #print 'RAW COLUMN COUNT:', self.sheet.getColumnCount()

        # Get the column names from the sheet and infer the number of used
        # columns.  The first empty cell encountered in the first row of the
        # sheet is considered to mark the end of the used columns.
        self.colnames = []
        for colnum in range(self.numcols):
            cellval = self.sheet.getImmutableCellAt(colnum, 0).getTextValue()
            if cellval == '':
                break
            self.colnames.append(cellval)
        self.rowcnt = 1
        self.numcols = len(self.colnames)
        #print 'USED COLUMN COUNT:', self.numcols

        if self.numcols == 0:
            raise RuntimeError('The input ODF spreadsheet "' + self.name
                    + '" in the file "' + self.getFileName()
                    + '" appears to be empty.')

        # Trim the column names and make sure they are unique.
        nameset = set()
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip().lower()
            if self.colnames[colnum] in nameset:
                raise RuntimeError('The column name "' + self.colnames[colnum]
                    + '" is used more than once in the input ODF spreadsheet "'
                    + self.name + '" in the file "' + self.getFileName()
                    + '".  All column names must be unique.')
            else:
                nameset.add(self.colnames[colnum])

    def next(self):
        """
        Allows iteration through each row of the ODF spreadsheet table. Empty
        rows are ignored.
        """
        # Find the next non-empty row.  After the loop, self.rowcnt will be at
        # the next non-empty row, assuming counting starts at 1 (if the search
        # succeeded).
        emptyrow = True
        emptyrowcnt = 0
        while (
            (self.rowcnt < self.numrows) and emptyrow and (emptyrowcnt < self.EMPTYROW_LIM)
        ):
            for colnum in range(self.numcols):
                if self.sheet.getImmutableCellAt(colnum, self.rowcnt).getTextValue() != '':
                    emptyrow = False
                    break
            if emptyrow:
                emptyrowcnt += 1
            self.rowcnt += 1

        if emptyrow:
            raise StopIteration()

        trow = TableRow(
            self.rowcnt, self,
            self.required_cols, self.optional_cols, self.defaultvals
        )
        for colnum in range(self.numcols):
            # Uncomment the following line to print the ODF value type for each
            # data cell.
            # print self.sheet.getImmutableCellAt(colnum, self.rowcnt - 1).getValueType()
            trow[self.colnames[colnum]] = self.sheet.getImmutableCellAt(
                colnum, self.rowcnt - 1
            ).getTextValue()

        return trow


class ODFTableReader(BaseTableReader):
    """
    Reads tables (i.e., sheets) from an ODF spreadsheet file (as produced,
    e.g., by LibreOffice and OpenOffice).
    """
    def __init__(self, filepath):
        BaseTableReader.__init__(self)

        self.filename = filepath
        ext = os.path.splitext(self.filename)[1]
        filein = File(filepath)

        if ext == '.ods':
            # A "regular" ODF spreadsheet.
            self.odfs = SpreadSheet.createFromFile(filein)
        elif ext == '.fods':
            # A flat XML ODF spreadsheet.
            odf_xml = ODSingleXMLDocument.createFromFile(filein)
            self.odfs = odf_xml.getPackage().getSpreadSheet()
        else:
            raise RuntimeError('Unrecognized file type: ' + self.filename + '.')

        self.numtables = self.odfs.getSheetCount()

    def getTableByIndex(self, index):
        if (index < 0) or (index >= self.numtables):
            raise KeyError(
                'Invalid table index: {0}.  No matching sheet could be found '
                'in the file "{1}".'.format(index, self.filename)
            )

        return _ODFTable(self.odfs.getSheet(index), self)

    def getTableByName(self, tablename):
        sheet = self.odfs.getSheet(tablename)
        if sheet is None:
            raise KeyError(
                'Invalid table name: "{0}".  No matching sheet could be found '
                'in the file "{1}".'.format(tablename, self.filename)
            )

        table = _ODFTable(sheet, self)

        return table

