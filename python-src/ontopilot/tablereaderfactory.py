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
        if not(os.path.isfile(self.filepath)):
            raise RuntimeError('The input file "' + self.filepath
                    + '" does not exist or is not a regular file.')

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

