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
from ontopilot.ontology import Ontology
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum


# IRIs of entities in the test ontology.
OBJPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0001'
DATAPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0020'
ANNOTPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0030'
CLASS_IRI = 'http://purl.obolibrary.org/obo/OBTO_0010'
INDIVIDUAL_IRI = 'http://purl.obolibrary.org/obo/OBTO_8001'

# IRI that is not used in the test ontology.
NULL_IRI = 'http://purl.obolibrary.org/obo/OBTO_9999'


class Test_Ontology(unittest.TestCase):
    """
    Tests the Ontology convenience class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.owlont = self.ont.getOWLOntology()

    def test_getExistingClass(self):
        self.assertIsNotNone(
            self.ont.getExistingClass(CLASS_IRI)
        )

        # Check a class in the imports closure.
        self.assertIsNotNone(
            self.ont.getExistingClass('http://purl.obolibrary.org/obo/OBITO_0001')
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingClass(NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingClass(OBJPROP_IRI)
        )

    def test_getExistingDataProperty(self):
        self.assertIsNotNone(
            self.ont.getExistingDataProperty(DATAPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingDataProperty(NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingDataProperty(OBJPROP_IRI)
        )

    def test_getExistingObjectProperty(self):
        self.assertIsNotNone(
            self.ont.getExistingObjectProperty(OBJPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingObjectProperty(NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingObjectProperty(DATAPROP_IRI)
        )

    def test_getExistingAnnotationProperty(self):
        self.assertIsNotNone(
            self.ont.getExistingAnnotationProperty(ANNOTPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingAnnotationProperty(NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingAnnotationProperty(OBJPROP_IRI)
        )

    def test_getExistingProperty(self):
        # Check each property type.
        self.assertIsNotNone(
            self.ont.getExistingProperty(OBJPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingProperty(DATAPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingProperty(ANNOTPROP_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingProperty(NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingProperty(CLASS_IRI)
        )

    def test_getExistingEntity(self):
        # Check each entity type.
        self.assertIsNotNone(
            self.ont.getExistingEntity(OBJPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingEntity(DATAPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingEntity(ANNOTPROP_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingEntity(CLASS_IRI)
        )
        self.assertIsNotNone(
            self.ont.getExistingEntity(INDIVIDUAL_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingEntity(NULL_IRI)
        )

    def test_getExistingIndividual(self):
        self.assertIsNotNone(
            self.ont.getExistingIndividual(INDIVIDUAL_IRI)
        )

        # Verify that a non-existent entity is not found.
        self.assertIsNone(
            self.ont.getExistingIndividual(NULL_IRI)
        )

        # Verify that an existent entity of the wrong type is not returned.
        self.assertIsNone(
            self.ont.getExistingIndividual(CLASS_IRI)
        )

    def test_createNewClass(self):
        entIRI = NULL_IRI

        self.assertIsNone(self.ont.getExistingEntity(entIRI))

        self.ont.createNewClass(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingClass(entIRI)
        )

    def test_createNewDataProperty(self):
        entIRI = NULL_IRI

        self.assertIsNone(self.ont.getExistingEntity(entIRI))

        self.ont.createNewDataProperty(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingDataProperty(entIRI)
        )

    def test_createNewObjectProperty(self):
        entIRI = NULL_IRI

        self.assertIsNone(self.ont.getExistingEntity(entIRI))

        self.ont.createNewObjectProperty(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingObjectProperty(entIRI)
        )

    def test_createNewAnnotationProperty(self):
        entIRI = NULL_IRI

        self.assertIsNone(self.ont.getExistingEntity(entIRI))

        self.ont.createNewAnnotationProperty(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingAnnotationProperty(entIRI)
        )

    def test_createNewIndividual(self):
        entIRI = NULL_IRI

        self.assertIsNone(self.ont.getExistingEntity(entIRI))

        self.ont.createNewIndividual(entIRI)

        self.assertIsNotNone(
            self.ont.getExistingIndividual(entIRI)
        )

    def test_removeEntity(self):
        classobj = self.ont.getExistingClass(CLASS_IRI)
        self.assertIsNotNone(classobj)

        # First, delete the class but not its annotations.
        self.ont.removeEntity(classobj.getOWLAPIObj(), False)

        # Make sure the class has been deleted.
        self.assertIsNone(
            self.ont.getExistingClass(CLASS_IRI)
        )

        # Make sure annotations for the target entity have not been deleted.
        IRIobj = IRI.create(CLASS_IRI)
        annot_ax_set = self.owlont.getAnnotationAssertionAxioms(IRIobj)
        self.assertEqual(2, annot_ax_set.size())

        # Run the deletion command again, this time deleting annotations.
        # Also, this time, use the _OntologyEntity object directly instead of
        # the OWL API object to make sure entity deletion works either way.
        self.ont.removeEntity(classobj, True)

        # Make sure annotations for the target entity have been deleted.
        IRIobj = IRI.create(CLASS_IRI)
        annot_ax_set = self.owlont.getAnnotationAssertionAxioms(IRIobj)
        self.assertTrue(annot_ax_set.isEmpty())

    def test_hasImport(self):
        import_iri = 'https://github.com/stuckyb/ontopilot/raw/master/python-src/test/test_data/ontology-import.owl'

        self.assertFalse(self.ont.hasImport('http://not.an.import/iri'))
        self.assertTrue(self.ont.hasImport(import_iri))

    def test_getImports(self):
        expected = [
            'https://github.com/stuckyb/ontopilot/raw/master/python-src/test/test_data/ontology-import.owl'
        ]
        imports_IRI_strs = [iri.toString() for iri in self.ont.getImports()]
        self.assertEqual(expected, imports_IRI_strs)

    def test_addImport(self):
        importIRI = IRI.create('file:/local/path/ont.owl')

        # Verify that the import is not yet included in the ontology.
        self.assertFalse(
            self.owlont.getDirectImportsDocuments().contains(importIRI)
        )

        self.ont.addImport(importIRI, False)

        # Verify that the import declaration was added.
        self.assertTrue(
            self.owlont.getDirectImportsDocuments().contains(importIRI)
        )

    def test_updateImportIRI(self):
        old_iri = 'https://github.com/stuckyb/ontopilot/raw/master/python-src/test/test_data/ontology-import.owl'
        new_iri = 'http://a.new.iri/replacement'

        self.assertTrue(self.ont.hasImport(old_iri))
        self.assertFalse(self.ont.hasImport(new_iri))

        self.ont.updateImportIRI(old_iri, new_iri)

        self.assertFalse(self.ont.hasImport(old_iri))
        self.assertTrue(self.ont.hasImport(new_iri))

        # Verify that an attempt to update an IRI for which there is not an
        # import statement is correctly handled.
        with self.assertRaisesRegexp(
            RuntimeError, 'the import IRI could not be updated'
        ):
            self.ont.updateImportIRI('http://iri.with.no/import', old_iri)

    def test_getImportedFromAnnotations(self):
        axioms = self.owlont.getAxioms(ImportsEnum.EXCLUDED)

        if_axioms = self.ont._getImportedFromAnnotations(axioms, self.owlont)

        # Define the IRIs of the entities that should be annotated.
        baseIRI = 'http://purl.obolibrary.org/obo/OBTO_'
        idnums = (
            '0001', '0020', '0030', '0010', '0011', '0012', '8000', '8001'
        )
        ent_IRIs = set([baseIRI + idnum for idnum in idnums])

        self.assertEqual(len(ent_IRIs), len(if_axioms))

        ontIRI = self.owlont.getOntologyID().getOntologyIRI().get()

        res_IRIs = set()
        for if_axiom in if_axioms:
            # Check the annotation property and value of each axiom.
            self.assertTrue(
                Ontology.IMPORTED_FROM_IRI.equals(
                    if_axiom.getProperty().getIRI()
                )
            )

            self.assertTrue(ontIRI.equals(if_axiom.getValue().asIRI().get()))

            res_IRIs.add(if_axiom.getSubject().toString())
        
        # Check all of the annotation subjects.
        self.assertEqual(ent_IRIs, res_IRIs)

    def test_mergeOntology(self):
        mergeiri_str = 'https://github.com/stuckyb/ontopilot/raw/master/python-src/test/test_data/ontology-import.owl'
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
            self.owlont.isDeclared(mergeclass, ImportsEnum.EXCLUDED)
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
            self.owlont.isDeclared(mergeclass, ImportsEnum.EXCLUDED)
        )

    def test_checkEntailmentErrors(self):
        # Check on ontology that is both consistent and coherent.
        report = self.ont.checkEntailmentErrors()
        self.assertTrue(report['is_consistent'])
        self.assertEqual(0, len(report['unsatisfiable_classes']))

        # Check an ontology that is both inconsistent and incoherent.
        testont = Ontology('test_data/inconsistent.owl')
        report = testont.checkEntailmentErrors()
        self.assertFalse(report['is_consistent'])
        self.assertEqual(0, len(report['unsatisfiable_classes']))

        # The ReasonerManager should ensure that reasoner instances track
        # ontology changes, so the following line should not be needed.
        #testont.getReasonerManager().disposeReasoners()

        # Check an ontology that is incoherent but not inconsistent.
        # Remove the instance of the unsatisfiable class 'test class 2' to make
        # the ontology consistent.
        individual = testont.getExistingIndividual('obo:OBTO_9000')
        testont.removeEntity(individual)
        unsatisfiable = testont.getExistingClass('obo:OBTO_0011').getOWLAPIObj()
        report = testont.checkEntailmentErrors()
        self.assertTrue(report['is_consistent'])
        self.assertEqual(1, len(report['unsatisfiable_classes']))
        self.assertTrue(
            unsatisfiable.equals(report['unsatisfiable_classes'][0])
        )

    def test_setOntologyID(self):
        ont_iri = 'http://a.test.iri/main'
        ver_iri = 'http://a.test.iri/version'

        self.ont.setOntologyID(ont_iri)
        ontid = self.owlont.getOntologyID()
        self.assertEqual(ont_iri, str(ontid.getOntologyIRI().get()))
        self.assertIsNone(ontid.getVersionIRI().orNull())

        self.ont.setOntologyID(ont_iri, ver_iri)
        ontid = self.owlont.getOntologyID()
        self.assertEqual(ont_iri, str(ontid.getOntologyIRI().get()))
        self.assertEqual(ver_iri, str(ontid.getVersionIRI().get()))

