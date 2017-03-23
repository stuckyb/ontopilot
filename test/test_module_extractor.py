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
from ontopilot.module_extractor import ModuleExtractor
from ontopilot.module_extractor import methods as me_methods
import unittest

# Java imports.
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum


# IRIs of entities in the test ontology.
OBJPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0001'
DATAPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0020'
ANNOTPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0030'
CLASS_IRI = 'http://purl.obolibrary.org/obo/OBTO_0010'
INDIVIDUAL_IRI = 'https://github.com/stuckyb/ontopilot/raw/master/test/test_data/ontology.owl#individual_002'

# IRI that is not used in the test ontology.
NULL_IRI = 'http://purl.obolibrary.org/obo/OBTO_9999'


class Test_ModuleExtractor(unittest.TestCase):
    """
    Tests the ModuleExtractor class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.owlont = self.ont.getOWLOntology()

        self.me = ModuleExtractor(self.ont)

    def test_extractSingleTerms(self):
        """
        Tests building an import module using only the single-term extraction
        method.
        """
        # Add 'test class 1'.
        self.me.addEntity('OBTO:0010', me_methods.SINGLE)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE)

        module = self.me.extractModule('http://test.mod/id')

        # Verify that all expected entities are present in the module.  Use at
        # least one label reference to verify that labels are mapped correctly
        # in the module ontology.
        self.assertIsNotNone(module.getExistingClass("'test class 1'"))
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0001'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))

        # Verify that there are no unexpected entities.  Note that the
        # annotation properties in the signature will include rdfs:label and
        # dc:source.
        owlont = module.getOWLOntology()
        self.assertEqual(1, owlont.getClassesInSignature(True).size())
        self.assertEqual(1, owlont.getObjectPropertiesInSignature(True).size())
        self.assertEqual(0, owlont.getDataPropertiesInSignature(True).size())
        self.assertEqual(3, owlont.getAnnotationPropertiesInSignature(False).size())
        self.assertEqual(0, owlont.getIndividualsInSignature(True).size())

    def test_extractHierarchy(self):
        """
        Tests building an import module using only the hierarchy extraction
        method.
        """
        # Add 'test class 1'.
        self.me.addEntity('OBTO:0010', me_methods.HIERARCHY)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.HIERARCHY)

        module = self.me.extractModule('http://test.mod/id')

        # Verify that all expected entities are present in the module.  Use at
        # least one label reference to verify that labels are mapped correctly
        # in the module ontology.
        self.assertIsNotNone(module.getExistingClass("'test class 1'"))
        self.assertIsNotNone(module.getExistingClass("'imported test class 1'"))
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0001'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))

        # Verify that there are no unexpected entities.  Note that the
        # annotation properties in the signature will include rdfs:label and
        # dc:source.
        owlont = module.getOWLOntology()
        self.assertEqual(2, owlont.getClassesInSignature(True).size())
        self.assertEqual(1, owlont.getObjectPropertiesInSignature(True).size())
        self.assertEqual(0, owlont.getDataPropertiesInSignature(True).size())
        self.assertEqual(3, owlont.getAnnotationPropertiesInSignature(False).size())
        self.assertEqual(0, owlont.getIndividualsInSignature(True).size())

        # Verify that the parent/child axioms are present.
        ent = module.getExistingClass('OBTO:0010')
        axioms = owlont.getSubClassAxiomsForSubClass(ent.getOWLAPIObj())
        self.assertTrue(1, axioms.size())

        #--------
        # Create a new module to test parent/child relationships for all
        # other possible entity types (the previous tests checked classes).
        #--------

        # Create a superproperty for 'test object property 1'.
        ent = self.ont.getExistingObjectProperty('OBTO:0001')
        newent = self.ont.createNewObjectProperty('OBTO:0002')
        ent.addSuperproperty('OBTO:0002')

        # Create a superproperty for 'test data property 1'.
        ent = self.ont.getExistingDataProperty('OBTO:0020')
        newent = self.ont.createNewDataProperty('OBTO:0021')
        ent.addSuperproperty('OBTO:0021')

        # Create a superproperty for 'annotation property 1'.
        ent = self.ont.getExistingAnnotationProperty('OBTO:0030')
        newent = self.ont.createNewAnnotationProperty('OBTO:0031')
        ent.addSuperproperty('OBTO:0031')

        self.me.clearSignatures()

        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.HIERARCHY)
        # Add 'test data property 1'.
        self.me.addEntity('OBTO:0020', me_methods.HIERARCHY)
        # Add 'annotation property 1'.
        self.me.addEntity('OBTO:0030', me_methods.HIERARCHY)

        module = self.me.extractModule('http://test.mod/id2')

        # Verify that all expected entities are present in the module.
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0001'))
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0002'))
        self.assertIsNotNone(module.getExistingDataProperty('OBTO:0020'))
        self.assertIsNotNone(module.getExistingDataProperty('OBTO:0021'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0031'))

        # Verify that there are no unexpected entities.  Note that the
        # annotation properties in the signature will include rdfs:label and
        # dc:source.
        owlont = module.getOWLOntology()
        self.assertEqual(0, owlont.getClassesInSignature(True).size())
        self.assertEqual(2, owlont.getObjectPropertiesInSignature(True).size())
        self.assertEqual(2, owlont.getDataPropertiesInSignature(True).size())
        self.assertEqual(4, owlont.getAnnotationPropertiesInSignature(False).size())
        self.assertEqual(0, owlont.getIndividualsInSignature(True).size())

        # Verify that the parent/child axioms are present.
        # Check 'test object property 1'.
        ent = module.getExistingObjectProperty('OBTO:0001')
        axioms = owlont.getObjectSubPropertyAxiomsForSubProperty(ent.getOWLAPIObj())
        self.assertTrue(1, axioms.size())
        # Check 'test data property 1'.
        ent = module.getExistingDataProperty('OBTO:0020')
        axioms = owlont.getDataSubPropertyAxiomsForSubProperty(ent.getOWLAPIObj())
        self.assertTrue(1, axioms.size())
        # Check 'annotation property 1'.
        ent = module.getExistingAnnotationProperty('OBTO:0030')
        axioms = owlont.getSubAnnotationPropertyOfAxioms(ent.getOWLAPIObj())
        self.assertTrue(1, axioms.size())

        #--------
        # Create a new module to test that cyclic parent/child relationships
        # are properly handled.
        #--------

        # Make a cyclic parent/child relationship for 'test class 1'.
        ent = self.ont.getExistingClass('OBTO:0010')
        newent = self.ont.createNewClass('OBTO:9999')
        ent.addSubclassOf('OBTO:9999')
        newent.addSubclassOf('OBTO:0010')

        self.me.clearSignatures()

        # Add 'test class 1'.
        self.me.addEntity("'test class 1'", me_methods.HIERARCHY)

        module = self.me.extractModule('http://test.mod/id3')

        # Verify that all expected entities are present in the module.
        self.assertIsNotNone(module.getExistingClass('OBTO:0010'))
        self.assertIsNotNone(module.getExistingClass('OBTO:9999'))
        self.assertIsNotNone(module.getExistingClass("'imported test class 1'"))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))

        # Verify that there are no unexpected entities.  Note that the
        # annotation properties in the signature will include rdfs:label and
        # dc:source.
        owlont = module.getOWLOntology()
        self.assertEqual(3, owlont.getClassesInSignature(True).size())
        self.assertEqual(0, owlont.getObjectPropertiesInSignature(True).size())
        self.assertEqual(0, owlont.getDataPropertiesInSignature(True).size())
        self.assertEqual(3, owlont.getAnnotationPropertiesInSignature(False).size())
        self.assertEqual(0, owlont.getIndividualsInSignature(True).size())

        # Verify that the parent/child axioms are present.
        ent = module.getExistingClass('OBTO:0010')
        axioms = owlont.getSubClassAxiomsForSubClass(ent.getOWLAPIObj())
        self.assertTrue(2, axioms.size())
        ent = module.getExistingClass('OBTO:9999')
        axioms = owlont.getSubClassAxiomsForSubClass(ent.getOWLAPIObj())
        self.assertTrue(1, axioms.size())

        module.saveOntology('blah.owl')

