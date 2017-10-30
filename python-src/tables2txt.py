#!/usr/bin/env jython

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
import sys
from argparse import ArgumentParser
import csv
from ontopilot.tablereaderfactory import TableReaderFactory

# Java imports.


# Define the command-line arguments.
argp = ArgumentParser(
    prog='tables2txt',
    description='Converts a spreadsheet document to plain text, CSV output.'
)
argp.add_argument(
    'file_in', type=str, help='The spreadsheet file to convert.  Excel (.xls, '
    '.xlsx), OpenDocument (e.g., LibreOffice, OpenOffice), and CSV documents '
    'are supported.'
)

args = argp.parse_args()

try:
    with TableReaderFactory(args.file_in) as treader:
        for table in treader:
            colnames = table.getColumnNames()
            writer = csv.DictWriter(sys.stdout, colnames)
            rowout = {}

            print 'Table:', table.getTableName()
            writer.writeheader()

            for row in table:
                for colname in colnames:
                    # Encode all output as UTF-8 text.
                    rowout[colname] = row[colname].encode('utf-8')
                writer.writerow(rowout)

except (RuntimeError) as err:
    print '\n', unicode(err), '\n'
    sys.exit(1)

