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
from ontopilot.ontoconfig import OntoConfig
from ontopilot.imports_buildtarget import ImportsBuildTarget, ModuleInfo
from test_tablereader import TableStub
from ontopilot.tablereader import TableRow, TableRowError
import unittest
import os.path

# Java imports.


class TestImportsBuildTarget(unittest.TestCase):
    """
    Tests the ImportsBuildTarget class.
    """
    def setUp(self):
        self.oc = OntoConfig('test_data/project.conf')
        self.oc.set('IRIs', 'dev_base_IRI', 'https://a.sample.iri/to/')
        self.oc.set('Imports', 'imports_src', 'imports_src/')
        self.oc.set('Build', 'builddir', '.')

        self.ibt = ImportsBuildTarget(None, False, self.oc)

        self.td_path = os.path.abspath('test_data/')
        self.isrc_path = os.path.abspath('test_data/imports_src/')

    def test_getAbsTermsFilePath(self):
        tr = TableRow(1, TableStub())

        # Test an empty terms file path.
        tr['Entities file'] = ''
        self.assertEqual('', self.ibt._getAbsTermsFilePath(tr))

        # Test an invalid terms file path.
        tr['Entities file'] = 'nonexistent/file.csv'
        with self.assertRaisesRegexp(
            TableRowError, 'Could not find the input terms file'
        ):
            self.ibt._getAbsTermsFilePath(tr)

        # Test a valid terms file path.
        tr['Entities file'] = 'bco_terms.csv'
        self.assertEqual(
            self.isrc_path + '/bco_terms.csv',
            self.ibt._getAbsTermsFilePath(tr)
        )

    def test_checkSourceIRI(self):
        tr = TableRow(1, TableStub())

        # Test an empty source IRI string.
        tr['IRI'] = ''
        with self.assertRaisesRegexp(
            TableRowError, 'Invalid source ontology IRI string'
        ):
            self.ibt._checkSourceIRI(tr)

        # Test an invalid source IRI string.
        tr['IRI'] = 'invalid IRI'
        with self.assertRaisesRegexp(
            TableRowError, 'Invalid source ontology IRI string'
        ):
            self.ibt._checkSourceIRI(tr)

    def test_getImportsInfo(self):
        # The source file includes an ignored row, two ontologies for which
        # import modules will be built, and one for which the entire ontology
        # will be imported.
        expected = [
            ModuleInfo(
                filename=self.td_path + '/ro_ontname_import_module.owl',
                iristr='https://a.sample.iri/to/imports/ro_ontname_import_module.owl'
            ),
            ModuleInfo(
                filename='',
                iristr='http://purl.obolibrary.org/obo/iao/ontology-metadata.owl'
            ),
            ModuleInfo(
                filename=self.td_path + '/bco_ontname_import_module.owl',
                iristr='https://a.sample.iri/to/imports/bco_ontname_import_module.owl'
            )
        ]

        self.assertEqual(expected, self.ibt.getImportsInfo())

