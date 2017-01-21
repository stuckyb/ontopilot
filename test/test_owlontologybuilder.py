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
from ontobuilder.tablereader import TableRow
from ontobuilder.owlontologybuilder import OWLOntologyBuilder
from ontobuilder.ontology_entities import (
    CLASS_ENTITY, DATAPROPERTY_ENTITY, OBJECTPROPERTY_ENTITY,
    ANNOTATIONPROPERTY_ENTITY
)
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


LABEL_IRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#label')
COMMENT_IRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#comment')

class Test_OWLOntologyBuilder(unittest.TestCase):
    """
    Tests OWLOntologyBuilder.
    """
    def setUp(self):
        self.oob = OWLOntologyBuilder('test_data/ontology.owl')
        self.test_ont = self.oob.getOntology()
        self.owlont = self.test_ont.getOWLOntology()

        # Define a test row.  In setUp(), we define row values that are shared
        # among all entities.  Remaining entity-specific values should be
        # defined in the entity-specific test methods.
        self.tr = TableRow(1, None)
        self.tr['ID'] = 'http://purl.obolibrary.org/obo/OBTO_0011'
        self.tr['Label'] = 'new test entity'
        self.tr['Text definition'] = 'The definition!'
        self.tr['Comments'] = 'The first comment.;"The second; comment."'

    def _checkGenericAxioms(self, entity):
        """
        Checks the values of all entity axioms that are shared among all entity
        types.
        """
        # Check that the label is correct.
        self.assertEqual(
            [self.tr['Label']], entity.getAnnotationValues(LABEL_IRI)
        )

        # Check the definition.
        self.assertEqual(
            [self.tr['Text definition']], entity.getAnnotationValues(entity.DEFINITION_IRI)
        )

        # Check the comments.
        self.assertEqual(
            sorted(['The first comment.', 'The second; comment.']),
            sorted(entity.getAnnotationValues(COMMENT_IRI))
        )

    def test_addClass(self):
        # Define additional row values.
        self.tr['Parent'] = 'obo:OBTO_2000'
        self.tr['Subclass of'] = "'test class 1'; OBITO:0001"
        self.tr['Equivalent to'] = 'OBTO:1001; obo:OBTO_1002'
        self.tr['Disjoint with'] = 'OBTO:1000'

        # Create some additional classes for use in axioms.
        self.test_ont.createNewClass('obo:OBTO_2000')
        self.test_ont.createNewClass('obo:OBTO_1000')
        self.test_ont.createNewClass('obo:OBTO_1001')
        self.test_ont.createNewClass('obo:OBTO_1002')

        self.oob.addClass(self.tr)

        # Process all deferred class axioms.
        self.oob.processDeferredEntityAxioms()

        # Check that the new class exists.
        newclass = self.test_ont.getExistingClass(self.tr['ID'])
        new_oaent = newclass.getOWLAPIObj()
        self.assertIsNotNone(newclass)

        self._checkGenericAxioms(newclass)

        # Check the "subclass of" axioms.  One will come from the value of the
        # "parent" field.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0010',
            'http://purl.obolibrary.org/obo/OBTO_2000',
            'http://purl.obolibrary.org/obo/OBITO_0001'
            }
        actualIRIs = set()
        for axiom in self.owlont.getSubClassAxiomsForSubClass(new_oaent):
            actualIRIs.add(axiom.getSuperClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the equivalency axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0011',
            'http://purl.obolibrary.org/obo/OBTO_1001',
            'http://purl.obolibrary.org/obo/OBTO_1002'
            }
        actualIRIs = set()
        for axiom in self.owlont.getEquivalentClassesAxioms(new_oaent):
            for eqclass in axiom.getNamedClasses():
                actualIRIs.add(eqclass.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the disjointness axiom.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0011',
            'http://purl.obolibrary.org/obo/OBTO_1000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDisjointClassesAxioms(new_oaent):
            for cl_exp in axiom.getClassExpressions():
                actualIRIs.add(cl_exp.asOWLClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

    def test_addDataProperty(self):
        # Define additional row values.
        self.tr['Parent'] = 'obo:OBTO_2000'
        self.tr['Domain'] = "'test class 1'; OBITO:0001"
        self.tr['Range'] = 'xsd:float'
        self.tr['Disjoint with'] = 'OBTO:1000;OBTO:1001'
        self.tr['Characteristics'] = 'functional'

        # Create some additional properties for use in axioms.
        self.test_ont.createNewDataProperty('obo:OBTO_1000')
        self.test_ont.createNewDataProperty('obo:OBTO_1001')
        self.test_ont.createNewDataProperty('obo:OBTO_2000')

        self.oob.addDataProperty(self.tr)

        # Process all deferred property axioms.
        self.oob.processDeferredEntityAxioms()

        # Check that the new property exists.
        newprop = self.test_ont.getExistingDataProperty(self.tr['ID'])
        new_oaent = newprop.getOWLAPIObj()
        self.assertIsNotNone(newprop)

        self._checkGenericAxioms(newprop)

        # Check the "subproperty of" axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_2000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDataSubPropertyAxiomsForSubProperty(new_oaent):
            actualIRIs.add(axiom.getSuperProperty().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the domain axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0010',
            'http://purl.obolibrary.org/obo/OBITO_0001'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDataPropertyDomainAxioms(new_oaent):
            cl_exp = axiom.getDomain()
            actualIRIs.add(cl_exp.asOWLClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the range axiom.
        found_drange = False
        axioms = self.owlont.getDataPropertyRangeAxioms(new_oaent)
        self.assertEqual(1, axioms.size())
        for axiom in axioms:
            if axiom.getRange().asOWLDatatype().isFloat():
                found_drange = True

        self.assertTrue(found_drange)

        # Check the disjointness axiom.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0011',
            'http://purl.obolibrary.org/obo/OBTO_1000',
            'http://purl.obolibrary.org/obo/OBTO_1001'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDisjointDataPropertiesAxioms(new_oaent):
            for dprop in axiom.getProperties():
                actualIRIs.add(dprop.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)
        
        # Verify that the property is functional.
        axioms = self.owlont.getFunctionalDataPropertyAxioms(new_oaent)
        self.assertEqual(1, axioms.size())

    def test_addObjectProperty(self):
        # Define additional row values.
        self.tr['Parent'] = 'obo:OBTO_2000'
        self.tr['Domain'] = 'obo:OBTO_3000'
        self.tr['Range'] = "'test class 1'; OBITO:0001"
        self.tr['Inverse'] = 'OBTO:1000'
        self.tr['Disjoint with'] = 'OBTO:1001'
        self.tr['Characteristics'] = 'functional, transitive'

        # Create some additional entities for use in axioms.
        self.test_ont.createNewObjectProperty('obo:OBTO_1000')
        self.test_ont.createNewObjectProperty('obo:OBTO_1001')
        self.test_ont.createNewObjectProperty('obo:OBTO_2000')
        self.test_ont.createNewClass('OBTO:3000')

        self.oob.addObjectProperty(self.tr)

        # Process all deferred property axioms.
        self.oob.processDeferredEntityAxioms()

        # Check that the new property exists.
        newprop = self.test_ont.getExistingObjectProperty(self.tr['ID'])
        new_oaent = newprop.getOWLAPIObj()
        self.assertIsNotNone(newprop)

        self._checkGenericAxioms(newprop)

        # Check the "subproperty of" axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_2000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getObjectSubPropertyAxiomsForSubProperty(new_oaent):
            actualIRIs.add(axiom.getSuperProperty().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the domain axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_3000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getObjectPropertyDomainAxioms(new_oaent):
            cl_exp = axiom.getDomain()
            actualIRIs.add(cl_exp.asOWLClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the range axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0010',
            'http://purl.obolibrary.org/obo/OBITO_0001'
        }
        actualIRIs = set()
        for axiom in self.owlont.getObjectPropertyRangeAxioms(new_oaent):
            cl_exp = axiom.getRange()
            actualIRIs.add(cl_exp.asOWLClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the "inverse of" axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0011',
            'http://purl.obolibrary.org/obo/OBTO_1000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getInverseObjectPropertyAxioms(new_oaent):
            for dprop in axiom.getProperties():
                actualIRIs.add(dprop.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the disjointness axiom.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0011',
            'http://purl.obolibrary.org/obo/OBTO_1001'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDisjointObjectPropertiesAxioms(new_oaent):
            for dprop in axiom.getProperties():
                actualIRIs.add(dprop.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)
        
        # Verify that the property is functional.
        axioms = self.owlont.getFunctionalObjectPropertyAxioms(new_oaent)
        self.assertEqual(1, axioms.size())

        # Verify that the property is transitive.
        axioms = self.owlont.getTransitiveObjectPropertyAxioms(new_oaent)
        self.assertEqual(1, axioms.size())

    def test_addAnnotationProperty(self):
        # Define additional row values.
        self.tr['Parent'] = 'obo:OBTO_1000'

        # Create an additional property for use in axioms.
        self.test_ont.createNewAnnotationProperty('obo:OBTO_1000')

        self.oob.addAnnotationProperty(self.tr)

        # Process all deferred property axioms.
        self.oob.processDeferredEntityAxioms()

        # Check that the new property exists.
        newprop = self.test_ont.getExistingAnnotationProperty(self.tr['ID'])
        new_oaent = newprop.getOWLAPIObj()
        self.assertIsNotNone(newprop)

        self._checkGenericAxioms(newprop)

        # Check the "subproperty of" axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_1000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getSubAnnotationPropertyOfAxioms(new_oaent):
            actualIRIs.add(axiom.getSuperProperty().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

    def test_expandDefinition(self):
        # Test an expansion that includes the label text.
        sourcestr = 'An example definition for {test class 1}.'
        expstr = 'An example definition for test class 1 (OBTO:0010).'

        self.assertEqual(expstr, self.oob._expandDefinition(sourcestr))

        # Test an expansion for which the label text is suppressed.
        sourcestr = 'An example definition for {$test class 1}.'
        expstr = 'An example definition for (OBTO:0010).'

        self.assertEqual(expstr, self.oob._expandDefinition(sourcestr))

