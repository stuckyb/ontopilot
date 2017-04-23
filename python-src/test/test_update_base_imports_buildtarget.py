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
from ontopilot.update_base_imports_buildtarget import UpdateBaseImportsBuildTarget
import unittest
import os.path

# Java imports.


# Define a simple "struct" type for simulating command-line arguments.
class ArgsType:
    pass


class TestOntoBuildTarget(unittest.TestCase):
    """
    Tests the supporting ("private") methods of the OntoBuildTarget class.
    """
    def setUp(self):
        self.oc = OntoConfig('test_data/project.conf')

        # We need to set the imports source location so that the
        # ImportsBuildTarget dependency will initialize without error.
        self.oc.set('Imports', 'imports_src', 'imports_src/')

        args = ArgsType()
        self.obt = UpdateBaseImportsBuildTarget(args, False, self.oc)

        self.td_path = os.path.abspath('test_data/')

    def test_retrieveAndCheckFilePaths(self):
        # Test a nonexistent base ontology file.
        with self.assertRaisesRegexp(
            RuntimeError, 'base ontology file could not be found'
        ):
            self.obt._retrieveAndCheckFilePaths()

        self.oc.set('Ontology', 'base_ontology_file', './ontology.owl')

        # Test an invalid build directory.
        with self.assertRaisesRegexp(
            RuntimeError,
            'directory for the updated base ontology file does not exist'
        ):
            self.obt._retrieveAndCheckFilePaths()

    def test_getOutputFilePath(self):
        self.oc.set('Build', 'insource_builds', 'True')
        exppath = os.path.join(self.td_path, 'src/ontname-base.owl')
        self.assertEqual(exppath, self.obt.getOutputFilePath())

        self.oc.set('Build', 'insource_builds', 'False')
        exppath = os.path.join(self.td_path, 'build/ontname-base.owl')
        self.assertEqual(exppath, self.obt.getOutputFilePath())

