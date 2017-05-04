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
from ontopilot.onto_buildtarget import OntoBuildTarget
import unittest
import os.path
from collections import namedtuple

# Java imports.


# Define a simple "struct" type for simulating command-line arguments.
ArgsType = namedtuple('args', 'no_def_expand')


class TestOntoBuildTarget(unittest.TestCase):
    """
    Tests the supporting ("private") methods of the OntoBuildTarget class.
    """
    def setUp(self):
        self.oc = OntoConfig('test_data/project.conf')
        self.oc.set('Ontology', 'entity_sourcedir', '.')

        # We need to set the imports source location so that the
        # ImportsBuildTarget dependency will initialize without error.
        self.oc.set('Imports', 'imports_src', 'imports_src/')

        args = ArgsType(no_def_expand=False)
        self.obt = OntoBuildTarget(args, False, self.oc)

        self.td_path = os.path.abspath('test_data/')

    def test_isGlobPattern(self):
        testvals = [
            ('', False),
            ('a', False),
            ('ab', False),
            ('*', True),
            ('a*', True),
            ('*a', True),
            ('a*b', True),
            ('a?b', True),
            ('[', False),
            (']', False),
            ('[]', False),
            ('[*]', False),
            ('a[*]b', False),
            ('a[*]bc*d', True),
            ('[?]', False),
            ('[[]', False),
            ('[[a]', True),
            ('[?*]', True),
            ('a[ab]', True),
            ('a[ab]b', True)
        ]

        for testval in testvals:
            self.assertEqual(testval[1], self.obt._isGlobPattern(testval[0]))

    def test_getExpandedSourceFilesList(self):
        # Test a set of terms file paths that includes wildcards and duplicate
        # file paths (including duplicates caused by expansion).
        termsfilesstr = 'test_table-valid.csv, test_table*.ods, test_table-valid.csv, test_table-valid.*'
        self.oc.set('Ontology', 'entity_sourcefiles', termsfilesstr)

        exp_fnames = [
            'test_table-valid.csv', 'test_table-valid.ods',
            'test_table-valid.xls', 'test_table-valid.xlsx',
            'test_table-error.ods'
        ]
        exp_fnames = [
            os.path.join(self.td_path, fname) for fname in exp_fnames
        ]

        self.assertEqual(
            sorted(exp_fnames), sorted(self.obt._getExpandedSourceFilesList())
        )

    def test_retrieveAndCheckFilePaths(self):
        # Test a nonexistent base ontology file.
        with self.assertRaisesRegexp(
            RuntimeError, 'base ontology file could not be found'
        ):
            self.obt._retrieveAndCheckFilePaths()

        self.oc.set('Ontology', 'base_ontology_file', './ontology.owl')

        # Test a terms file that is a valid path but not an actual file.
        self.oc.set('Ontology', 'entity_sourcefiles', 'test_table-valid.csv, .')
        with self.assertRaisesRegexp(
            RuntimeError, 'exists, but is not a valid file'
        ):
            self.obt._retrieveAndCheckFilePaths()

    def test_getOutputFilePath(self):
        self.oc.set('Build', 'insource_builds', 'True')
        exppath = os.path.join(self.td_path, 'ontology/ontname-raw.owl')
        self.assertEqual(exppath, self.obt.getOutputFilePath())

        self.oc.set('Build', 'insource_builds', 'True')
        exppath = os.path.join(self.td_path, 'ontology/ontname.owl')
        self.assertEqual(exppath, self.obt.getOutputFilePath(False))

        self.oc.set('Build', 'insource_builds', 'False')
        exppath = os.path.join(self.td_path, 'build/ontname-raw.owl')
        self.assertEqual(exppath, self.obt.getOutputFilePath())

