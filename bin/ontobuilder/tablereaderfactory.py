
# Python imports.
import os
from tablereader_csv import CSVTableReader
from tablereader_odf import ODFTableReader
from tablereader_excel import ExcelTableReader

# Java imports.


class TableReaderFactory:
    """
    A factory class that instantiates a TableReader class to match the type of
    a given input file.  The class instance provides a context manager to
    manage the lifetime of the instantiated table reader.
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.t_reader = None

    def __enter__(self):
        """
        Enter portion of the context manager interface.
        """
        # Determine the type of the input file.  This is currently done by
        # looking at the file extension.  We could add more robust checks of
        # file type at some point, but it might not be worth the trouble.
        ext = os.path.splitext(self.filepath)[1]
        if ext == '.csv':
            self.t_reader = CSVTableReader(self.filepath)
        elif ext in ('.ods', '.fods'):
            self.t_reader = ODFTableReader(self.filepath)
        elif ext in ('.xls', '.xlsx'):
            self.t_reader = ExcelTableReader(self.filepath)
        else:
            raise RuntimeError('The type of the input file "' + self.filepath
                    + '" could not be determined or is not supported.')

        return self.t_reader

    def __exit__(self, etype, value, traceback):
        """
        Exit portion of the context manager interface.
        """
        self.t_reader.close()

