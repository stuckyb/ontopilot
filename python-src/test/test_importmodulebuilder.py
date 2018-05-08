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
from ontopilot.importmodulebuilder import ImportModuleBuilder
from ontopilot.ontology import Ontology
from ontopilot.tablereader import TableRow
from test_tablereader import TableStub
import unittest
import os.path

# Java imports.
from java.util import HashSet


class TestImportModuleBuilder(unittest.TestCase):
    """
    Tests the ImportModuleBuilder class.
    """
    def setUp(self):
        self.baseIRI = 'https://a.sample.iri/for/'
        self.mod_suffix = '_import_module.owl'
        self.td_path = os.path.abspath('test_data/')

        self.imb = ImportModuleBuilder(
            self.baseIRI, self.mod_suffix, self.td_path + '/imports'
        )

    def test_init(self):
        """
        Tests the constructor.
        """
        builddir = os.path.join(self.td_path, 'build')
        outputdir = os.path.join(self.td_path, 'imports')

        imb = ImportModuleBuilder(self.baseIRI, self.mod_suffix, builddir)
        self.assertEqual(builddir, imb.builddir)
        self.assertEqual(builddir, imb.outputdir)

        imb = ImportModuleBuilder(self.baseIRI, self.mod_suffix, builddir, outputdir)
        self.assertEqual(builddir, imb.builddir)
        self.assertEqual(outputdir, imb.outputdir)

    def test_getOutputFileName(self):
        # Define the list of test values.  Each tuple is in the order
        # (expected_module_name, import_IRI).
        testvals = [
            ('ontfile_import_module.owl', 'http://import.ontology/iri/ontfile.owl'),
            ('ontfile_import_module.owl', 'http://import.ontology/iri/ontfile'),
            ('_import_module.owl', 'http://import.ontology/iri/ontfile/')
        ]

        for testval in testvals:
            self.assertEqual(
                testval[0], self.imb._getOutputFileName(testval[1])
            )

    def test_getModulePath(self):
        outputdir = os.path.join(self.td_path, 'imports')

        # Define the list of test values.  Each tuple is in the order
        # (expected_path, import_IRI).
        testvals = [
            (
                os.path.join(outputdir, 'ontfile_import_module.owl'),
                'http://import.ontology/iri/ontfile.owl'
            ),
            (
                os.path.join(outputdir, 'ontfile_import_module.owl'),
                'http://import.ontology/iri/ontfile'
            ),
            (
                os.path.join(outputdir, '_import_module.owl'),
                'http://import.ontology/iri/ontfile/'
            )
        ]

        for testval in testvals:
            self.assertEqual(
                testval[0], self.imb.getModulePath(testval[1])
            )

    def test_getModuleIRIStr(self):
        # Define the list of test values.  Each tuple is in the order
        # (expected_module_IRI, base_IRI, import_IRI).
        testvals = [
            (
                'https://a.sample.iri/for/ontfile_import_module.owl',
                'https://a.sample.iri/for/',
                'http://import.ontology/iri/ontfile.owl'
            ),
            (
                'https://a.sample.iri/for/ontfile_import_module.owl',
                'https://a.sample.iri/for',
                'http://import.ontology/iri/ontfile.owl'
            )
        ]

        for testval in testvals:
            self.imb.base_IRI = testval[1]
            self.assertEqual(
                testval[0], self.imb.getModuleIRIStr(testval[2])
        )

        # Test that an invalid base IRI is handled correctly.
        self.imb.base_IRI = '/invalid IRI'
        with self.assertRaisesRegexp(
            RuntimeError, 'is not a valid base IRI'
        ):
            self.imb.getModuleIRIStr('http://import.ontology/iri/ontfile.owl')

