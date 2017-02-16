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


# Python imports.
from ontobuilder.ontoconfig import OntoConfig
from ontobuilder.onto_buildmanager import OntoBuildManager
import unittest
import os.path

# Java imports.


class TestOntoBuildManager(unittest.TestCase):
    """
    Tests the supporting ("private") methods of the OntoBuildManager class.
    """
    def setUp(self):
        self.oc = OntoConfig('test_data/config.conf')
        self.oc.set('Ontology', 'termsdir', '.')

        self.obm = OntoBuildManager(self.oc)

        self.td_path = os.path.abspath('test_data/')

    def test_getExpandedTermsFilesList(self):
        # Test a set of terms file paths that includes wildcards and duplicate
        # file paths (including duplicates caused by expansion).
        termsfilesstr = 'test_table-valid.csv, test_table*.ods, test_table-valid.csv, test_table-valid.*'
        self.oc.set('Ontology', 'termsfiles', termsfilesstr)

        exp_fnames = [
            'test_table-valid.csv', 'test_table-valid.ods',
            'test_table-valid.xls', 'test_table-valid.xlsx',
            'test_table-error.ods'
        ]
        exp_fnames = [
            os.path.join(self.td_path, fname) for fname in exp_fnames
        ]

        self.assertEqual(
            sorted(exp_fnames), sorted(self.obm._getExpandedTermsFilesList())
        )

    def test_retrieveAndCheckFilePaths(self):
        # Test a nonexistent base ontology file.
        with self.assertRaisesRegexp(
            RuntimeError, 'base ontology file could not be found'
        ):
            self.obm._retrieveAndCheckFilePaths()

        self.oc.set('Ontology', 'base_ontology_file', './ontology.owl')

        # Test a terms file that is a valid path but not an actual file.
        self.oc.set('Ontology', 'termsfiles', 'test_table-valid.csv, .')
        with self.assertRaisesRegexp(
            RuntimeError, 'exists, but is not a valid file'
        ):
            self.obm._retrieveAndCheckFilePaths()

        self.oc.set('Ontology', 'termsfiles', 'test_table-valid.csv')

        # Test an invalid build directory.
        with self.assertRaisesRegexp(
            RuntimeError, 'directory for the ontology does not exist'
        ):
            self.obm._retrieveAndCheckFilePaths()

