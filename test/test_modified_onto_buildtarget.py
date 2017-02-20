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
from ontobuilder.modified_onto_buildtarget import ModifiedOntoBuildTarget
import unittest
import os.path
from collections import namedtuple

# Java imports.


# Define a simple "struct" type for simulating command-line arguments.
ArgsType = namedtuple('args', 'merge_imports, reason, no_def_expand')


class TestModifiedOntoBuildTarget(unittest.TestCase):
    """
    Tests the supporting methods of the ModifiedOntoBuildTarget class.
    """
    def setUp(self):
        self.oc = OntoConfig('test_data/config.conf')
        self.oc.set('Ontology', 'termsdir', '.')

        # We need to set the imports source location so that the
        # ImportsBuildTarget dependency of OntoBuildTarget will initialize
        # without error.
        self.oc.set('Imports', 'imports_src', 'imports_src/')

        self.td_path = os.path.abspath('test_data/')

    def test_isBuildRequired(self):
        # The test coverage here is incomplete and only covers a few cases.
        # More thorough testing would require mocking os module functionality.
        args = ArgsType(merge_imports=False, reason=False, no_def_expand=False)
        mobt = ModifiedOntoBuildTarget(self.oc, args)
        self.assertFalse(mobt._isBuildRequired())

        args = ArgsType(merge_imports=True, reason=False, no_def_expand=False)
        mobt = ModifiedOntoBuildTarget(self.oc, args)
        self.assertTrue(mobt._isBuildRequired())

    def test_retrieveAndCheckFilePaths(self):
        # Test a nonexistent main ontology file.
        args = ArgsType(merge_imports=True, reason=False, no_def_expand=False)
        mobt = ModifiedOntoBuildTarget(self.oc, args)
        with self.assertRaisesRegexp(
            RuntimeError, 'main compiled ontology file could not be found'
        ):
            mobt._retrieveAndCheckFilePaths()

    def test_getOutputFilePath(self):
        self.oc.set('Build', 'insource_builds', 'False')

        args = ArgsType(merge_imports=False, reason=False, no_def_expand=False)
        mobt = ModifiedOntoBuildTarget(self.oc, args)
        exppath = os.path.join(self.td_path, 'build/ontname.owl')
        self.assertEqual(exppath, mobt.getOutputFilePath())

        args = ArgsType(merge_imports=True, reason=False, no_def_expand=False)
        mobt = ModifiedOntoBuildTarget(self.oc, args)
        exppath = os.path.join(self.td_path, 'build/ontname-merged.owl')
        self.assertEqual(exppath, mobt.getOutputFilePath())

        args = ArgsType(merge_imports=False, reason=True, no_def_expand=False)
        mobt = ModifiedOntoBuildTarget(self.oc, args)
        exppath = os.path.join(self.td_path, 'build/ontname-reasoned.owl')
        self.assertEqual(exppath, mobt.getOutputFilePath())

        args = ArgsType(merge_imports=True, reason=True, no_def_expand=False)
        mobt = ModifiedOntoBuildTarget(self.oc, args)
        exppath = os.path.join(
            self.td_path, 'build/ontname-merged-reasoned.owl'
        )
        self.assertEqual(exppath, mobt.getOutputFilePath())

