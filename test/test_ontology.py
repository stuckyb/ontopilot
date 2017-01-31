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
from ontobuilder.ontology import Ontology
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum


class Test_Ontology(unittest.TestCase):
    """
    Tests the Ontology convenience class.
    """
    # IRIs of entities in the test ontology.
    OBJPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0001'
    DATAPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0020'
    ANNOTPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0030'
    CLASS_IRI = 'http://purl.obolibrary.org/obo/OBTO_0010'
    INDIVIDUAL_IRI = 'https://github.com/stuckyb/ontobuilder/raw/master/test/test_data/ontology.owl#individual_001'

    # IRI that is not used in the test ontology.
    NULL_IRI = 'http://purl.obolibrary.org/obo/OBTO_9999'

    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.owlont = self.ont.getOWLOntology()

    def test_labelToIRI(self):
        expIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')
        self.assertTrue(
            expIRI.equals(self.ont.labelToIRI('test class 1'))
        )

    def test_expandIRI(self):
        expIRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#label')

        # Test full IRIs, prefix IRIs, and IRI objects.
        testvals = [
            'http://www.w3.org/2000/01/rdf-schema#label',
            'rdfs:label',
            IRI.create('http://www.w3.org/2000/01/rdf-schema#label')
        ]

        for testval in testvals:
            self.assertTrue(
                expIRI.equals(self.ont.expandIRI(testval))
            )

        # Also test a relative IRI.
        expIRI = IRI.create('https://github.com/stuckyb/ontobuilder/raw/master/test/test_data/ontology.owl#blah')
        self.assertTrue(
            expIRI.equals(self.ont.expandIRI('blah'))
        )

        # Make sure invalid IRI strings are detected.
        with self.assertRaisesRegexp(RuntimeError, 'Invalid IRI string'):
            self.ont.expandIRI('BL\nAH')

    def test_expandIdentifier(self):
        expIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0001')
        
        testvals = [
            'http://purl.obolibrary.org/obo/OBTO_0001',
            'obo:OBTO_0001',
            'OBTO:0001',
            IRI.create('http://purl.obolibrary.org/obo/OBTO_0001')
        ]

        for testval in testvals:
            self.assertTrue(
                expIRI.equals(self.ont.expandIdentifier(testval))
            )

    def test_getExistingClass(self):
        self.assertIsNotNone(
            self.ont.getExistingClass(self.CLASS_IRI)
        )

        # Check a class in the imports closure.
        self.assertIsNotNone(
            self.ont.getExistingClass('http://purl.obolibrary.org/obo/OBITO_0001')
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingClass(self.NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingClass(self.OBJPROP_IRI)
        )

    def test_getExistingDataProperty(self):
        self.assertIsNotNone(
            self.ont.getExistingDataProperty(self.DATAPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingDataProperty(self.NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingDataProperty(self.OBJPROP_IRI)
        )

    def test_getExistingObjectProperty(self):
        self.assertIsNotNone(
            self.ont.getExistingObjectProperty(self.OBJPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingObjectProperty(self.NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingObjectProperty(self.DATAPROP_IRI)
        )

    def test_getExistingAnnotationProperty(self):
        self.assertIsNotNone(
            self.ont.getExistingAnnotationProperty(self.ANNOTPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingAnnotationProperty(self.NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingAnnotationProperty(self.OBJPROP_IRI)
        )

    def test_getExistingProperty(self):
        # Check each property type.
        self.assertIsNotNone(
            self.ont.getExistingProperty(self.OBJPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingProperty(self.DATAPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingProperty(self.ANNOTPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingProperty(self.NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingProperty(self.CLASS_IRI)
        )

    def test_getExistingEntity(self):
        # Check each entity type.
        self.assertIsNotNone(
            self.ont.getExistingEntity(self.OBJPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingEntity(self.DATAPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingEntity(self.ANNOTPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingEntity(self.CLASS_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingEntity(self.NULL_IRI)
        )

    def test_getExistingIndividual(self):
        self.assertIsNotNone(
            self.ont.getExistingIndividual(self.INDIVIDUAL_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingIndividual(self.NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingIndividual(self.CLASS_IRI)
        )

    def test_createNewClass(self):
        entIRI = 'http://purl.obolibrary.org/obo/OBTO_0011'

        self.ont.createNewClass(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingClass(entIRI)
        )

    def test_createNewDataProperty(self):
        entIRI = 'http://purl.obolibrary.org/obo/OBTO_0011'

        self.ont.createNewDataProperty(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingDataProperty(entIRI)
        )

    def test_createNewObjectProperty(self):
        entIRI = 'http://purl.obolibrary.org/obo/OBTO_0011'

        self.ont.createNewObjectProperty(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingObjectProperty(entIRI)
        )

    def test_createNewAnnotationProperty(self):
        entIRI = 'http://purl.obolibrary.org/obo/OBTO_0011'

        self.ont.createNewAnnotationProperty(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingAnnotationProperty(entIRI)
        )

    def test_removeEntity(self):
        classobj = self.ont.getExistingClass(self.CLASS_IRI)
        self.assertIsNotNone(classobj)

        # First, delete the class but not its annotations.
        self.ont.removeEntity(classobj.getOWLAPIObj(), False)

        # Make sure the class has been deleted.
        self.assertIsNone(
            self.ont.getExistingClass(self.CLASS_IRI)
        )

        # Make sure annotations for the target entity have not been deleted.
        IRIobj = IRI.create(self.CLASS_IRI)
        annot_ax_set = self.owlont.getAnnotationAssertionAxioms(IRIobj)
        self.assertEqual(1, annot_ax_set.size())

        # Run the deletion command again, this time deleting annotations.
        self.ont.removeEntity(classobj.getOWLAPIObj(), True)

        # Make sure annotations for the target entity have been deleted.
        IRIobj = IRI.create(self.CLASS_IRI)
        annot_ax_set = self.owlont.getAnnotationAssertionAxioms(IRIobj)
        self.assertTrue(annot_ax_set.isEmpty())

    def test_addImport(self):
        importIRI = IRI.create('http://test.import/iri/ont.owl')

        # Verify that the import is not yet included in the ontology.
        self.assertFalse(
            self.owlont.getDirectImportsDocuments().contains(importIRI)
        )

        self.ont.addImport(importIRI, False)

        # Verify that the import declaration was added.
        self.assertTrue(
            self.owlont.getDirectImportsDocuments().contains(importIRI)
        )

    def test_mergeOntology(self):
        mergeiri_str = 'https://github.com/stuckyb/ontobuilder/raw/master/test/test_data/ontology-import.owl'
        mergeIRI = IRI.create(mergeiri_str)

        mergeclassiri_str = 'http://purl.obolibrary.org/obo/OBITO_0001'
        mergeclassIRI = IRI.create(mergeclassiri_str)
        mergeclass = self.ont.df.getOWLClass(mergeclassIRI)

        # Verify that the source IRI is in the target ontology's imports list
        # and that the class defined in the source ontology is not in the
        # target ontology.
        self.assertTrue(
            self.owlont.getDirectImportsDocuments().contains(mergeIRI)
        )
        self.assertFalse(
            self.owlont.getSignature(ImportsEnum.EXCLUDED).contains(mergeclass)
        )

        # Merge the axioms from the source ontology.
        self.ont.mergeOntology(mergeiri_str)

        # Verify that the source IRI is *not* in the target ontology's imports
        # list and that the class defined in the source ontology *is* in the
        # target ontology.
        self.assertFalse(
            self.owlont.getDirectImportsDocuments().contains(mergeIRI)
        )
        self.assertTrue(
            self.owlont.getSignature(ImportsEnum.EXCLUDED).contains(mergeclass)
        )

