
# This is a mostly complete implementation of the table reader interface for
# Excel documents that uses the Python xlrd package.  Unfortunately, xlrd does
# not currently support interpreting Excel's cell value format strings, which
# means that there is no easy way to ensure that the values extracted from a
# worksheet will (or ar likely to) match the values displayed by Excel.  At the
# moment, then, the Java Apache POI library is preferrable because it does
# provide this feature.


# Python imports.
from tablereader import TableRow, BaseTable, BaseTableReader
import xlrd

# Java imports.


class _ExcelTable(BaseTable):
    """
    Represents a single table (i.e., sheet) in a Microsoft Excel spreadsheet
    file.  _ExcelTable assumes that the first row of the sheet contains the
    column names.  Each subsequent row is returned as a TableRow object; thus,
    column names are not case sensitive.
    """
    def __init__(self, excelsheet, filename, required_cols=[], optional_cols=[], default_vals={}):
        BaseTable.__init__(self, excelsheet.name, required_cols, optional_cols, default_vals)

        self.sheet = excelsheet
        self.filename = filename

        self.numrows = self.sheet.nrows
        self.numcols = self.sheet.ncols
        #print 'RAW ROW COUNT:', self.sheet.nrows
        #print 'RAW COLUMN COUNT:', self.sheet.ncols

        # Get the column names from the sheet and infer the number of used
        # columns.  The first empty cell encountered in the first row of the
        # sheet is considered to mark the end of the used columns.
        self.colnames = []
        for colnum in range(self.numcols):
            cellval = self._cellStrValue(self.sheet.cell(0, colnum))
            if cellval == '':
                break
            self.colnames.append(cellval)
        self.rowcnt = 1
        self.numcols = len(self.colnames)
        #print 'USED COLUMN COUNT:', self.numcols

        if self.numcols == 0:
            raise RuntimeError('The input Excel spreadsheet "' + self.name
                    + '" in the file "' + self.filename
                    + '" appears to be empty.')

        # Trim the column names and make sure they are unique.
        nameset = set()
        for colnum in range(len(self.colnames)):
            self.colnames[colnum] = self.colnames[colnum].strip().lower()
            if self.colnames[colnum] in nameset:
                raise RuntimeError('The column name "' + self.colnames[colnum]
                    + '" is used more than once in the input Excel spreadsheet "'
                    + self.name + '" in the file "' + self.filename
                    + '".  All column names must be unique.')
            else:
                nameset.add(self.colnames[colnum])

    def _cellStrValue(self, cell):
        """
        Returns the value of an Excel spreadsheet cell as a string.
        """
        if cell.ctype == xlrd.XL_CELL_NUMBER:
            return str(cell.value)
        elif cell.ctype == xlrd.XL_CELL_DATE:
            return str(cell.value)
        elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
            if cell.value == 1:
                return 'TRUE'
            else:
                return 'FALSE'
        elif cell.ctype == xlrd.XL_CELL_ERROR:
            raise RuntimeError('Error detected in row ' + str(self.rowcnt)
                    + ' in the input Excel spreadsheet "' + self.name
                    + '" in the file "' + self.filename + '": '
                    + self.error_text_from_code(cell.value) + '.')
        else:
            return cell.value

    def next(self):
        """
        Allows iteration through each row of the Excel spreadsheet table. Empty
        rows are ignored.
        """
        # Find the next non-empty row.  After the loop, self.rowcnt will be at
        # the next non-empty row, assuming counting starts at 1 (if the search
        # succeeded).
        emptyrow = True
        while (self.rowcnt < self.numrows) and emptyrow:
            for colnum in range(self.numcols):
                if self.sheet.cell(self.rowcnt, colnum).value != '':
                    emptyrow = False
                    break
            self.rowcnt += 1

        if emptyrow:
            raise StopIteration()

        trow = TableRow(
            self.rowcnt, self.filename,
            self.required_cols, self.optional_cols, self.defaultvals
        )
        for colnum in range(self.numcols):
            # Uncomment the following line to print the Excel value type for
            # each data cell.
            print self.sheet.cell(self.rowcnt - 1, colnum).ctype
            cell = self.sheet.cell(self.rowcnt - 1, colnum)
            trow[self.colnames[colnum]] = self._cellStrValue(cell)

        return trow


class ExcelTableReader(BaseTableReader):
    """
    Reads tables (i.e., sheets) from a Microsoft Excel spreadsheet file.
    """
    def __init__(self, filepath):
        BaseTableReader.__init__(self)

        self.filename = filepath
        self.wbook = xlrd.open_workbook(self.filename)

        self.numtables = self.wbook.nsheets

    def getTableByIndex(self, index):
        if (index < 0) or (index >= self.numtables):
            raise KeyError('Invalid table index:' + str(index)
                    + '.  No matching sheet could be found in the file "'
                    + self.filename + '".')

        return _ExcelTable(self.wbook.sheet_by_index(index), self.filename)

    def getTableByName(self, tablename):
        sheet = self.wbook.sheet_by_name(tablename)
        if sheet == None:
            raise KeyError('Invalid table name: "' + str(tablename)
                    + '".  No matching sheet could be found in the file "'
                    + self.filename + '".')

        table = _ExcelTable(sheet, self.filename)

        return table

