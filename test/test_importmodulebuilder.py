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
from ontobuilder.importmodulebuilder import ImportModuleBuilder
from ontobuilder.ontology import Ontology
from ontobuilder.tablereader import TableRow
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
        builddir = self.td_path + '/build'
        outputdir = self.td_path + '/imports'

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
        outputdir = self.td_path + '/imports'

        # Define the list of test values.  Each tuple is in the order
        # (expected_path, import_IRI).
        testvals = [
            (
                outputdir + '/ontfile_import_module.owl',
                'http://import.ontology/iri/ontfile.owl'
            ),
            (
                outputdir + '/ontfile_import_module.owl',
                'http://import.ontology/iri/ontfile'
            ),
            (
                outputdir + '/_import_module.owl',
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

    def test_addEntityToSignature(self):
        tr = TableRow(1, TableStub())
        ont = Ontology('test_data/ontology.owl')
        signature = HashSet()
        owlclass = ont.getExistingClass('obo:OBTO_0010').getOWLAPIObj()

        # Test adding a class to the signature without also adding its
        # descendants.
        tr['Seed descendants'] = 'N'
        self.imb._addEntityToSignature(owlclass, signature, tr, ont)
        self.assertEqual(1, signature.size())
        self.assertTrue(signature.iterator().next().equals(owlclass))

        # Test adding a class and its descendants to the signature.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0010',
            'http://purl.obolibrary.org/obo/OBTO_0012'
        }

        tr['Seed descendants'] = 'Y'
        tr['Reasoner'] = 'HermiT'
        signature.clear()

        self.imb._addEntityToSignature(owlclass, signature, tr, ont)
        actualIRIs = set()
        for ent in signature:
            actualIRIs.add(ent.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Test adding an object property and its descendants to the signature.
        owlprop = ont.getExistingObjectProperty('obo:OBTO_0001').getOWLAPIObj()
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0001'
        }

        signature.clear()

        self.imb._addEntityToSignature(owlprop, signature, tr, ont)
        actualIRIs = set()
        for ent in signature:
            actualIRIs.add(ent.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Test adding a data property and its descendants to the signature.
        owlprop = ont.getExistingDataProperty('obo:OBTO_0020').getOWLAPIObj()
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0020'
        }

        signature.clear()

        self.imb._addEntityToSignature(owlprop, signature, tr, ont)
        actualIRIs = set()
        for ent in signature:
            actualIRIs.add(ent.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

