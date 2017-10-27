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
from ontopilot.tablereader import TableRow
from ontopilot.owlontologybuilder import (
    OWLOntologyBuilder, EntityDescriptionError
)
from ontopilot.ontology_entities import (
    CLASS_ENTITY, DATAPROPERTY_ENTITY, OBJECTPROPERTY_ENTITY,
    ANNOTATIONPROPERTY_ENTITY, INDIVIDUAL_ENTITY
)
import unittest
from test_tablereader import TableStub
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


LABEL_IRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#label')
COMMENT_IRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#comment')

# An IRI that is not used in the test ontology.
NEW_IRI = 'http://purl.obolibrary.org/obo/OBTO_9999'


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
        self.tr = TableRow(1, TableStub())
        self.tr['ID'] = NEW_IRI
        self.tr['Label'] = 'new test entity'
        self.tr['Text definition'] = 'The definition!'
        self.tr['Comments'] = '"The first comment."; The second\; comment.'
        self.tr['Annotations'] = """
            'annotation property 1' "Annotation text 1.";
            'annotation property 1' "Annotation text 2."
        """
        self.tr["@'annotation property 1'"] = "Annotation text 3."

        # If we define custom failure messages, append them to the end of the
        # default failure message.
        self.longMessage = True

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
            [self.tr['Text definition']],
            entity.getAnnotationValues(entity.DEFINITION_IRI)
        )

        # Check the comments.
        self.assertEqual(
            sorted(['The first comment.', 'The second; comment.']),
            sorted(entity.getAnnotationValues(COMMENT_IRI))
        )

        # Check the annotations.
        annotpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0030')
        self.assertEqual(
            sorted([
                'Annotation text 1.', 'Annotation text 2.',
                'Annotation text 3.'
            ]),
            sorted(entity.getAnnotationValues(annotpropIRI))
        )

    def test_addClass(self):
        # Define additional row values.
        self.tr['Parent'] = 'OBTO:1003'
        self.tr['Subclass of'] = "'test class 1'; OBITO:0001"
        self.tr['Superclass of'] = 'OBTO:0011'
        self.tr['Equivalent to'] = 'OBTO:1001; obo:OBTO_1002'
        self.tr['Disjoint with'] = 'OBTO:1000'

        # Create some additional classes for use in axioms.
        self.test_ont.createNewClass('OBTO:1003')
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
            'http://purl.obolibrary.org/obo/OBTO_1003',
            'http://purl.obolibrary.org/obo/OBITO_0001'
            }
        actualIRIs = set()
        for axiom in self.owlont.getSubClassAxiomsForSubClass(new_oaent):
            actualIRIs.add(axiom.getSuperClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the superclass axiom.
        expIRIs = {'http://purl.obolibrary.org/obo/OBTO_0011'}
        actualIRIs = set()
        for axiom in self.owlont.getSubClassAxiomsForSuperClass(new_oaent):
            actualIRIs.add(axiom.getSubClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the equivalency axioms.
        expIRIs = {
            NEW_IRI,
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
            NEW_IRI,
            'http://purl.obolibrary.org/obo/OBTO_1000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDisjointClassesAxioms(new_oaent):
            for cl_exp in axiom.getClassExpressions():
                actualIRIs.add(cl_exp.asOWLClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

    def _do_addOrUpdateEntity(self, enttype, entdesc):
        """
        A supporting method for _test_addOrUpdateEntity() that runs the
        appropriate addOrUpdateEntity() method in OOWLOntologyBuilder according
        to the constant enttype.
        """
        if enttype == CLASS_ENTITY:
            self.oob.addOrUpdateClass(entdesc)
        elif enttype == DATAPROPERTY_ENTITY:
            self.oob.addOrUpdateDataProperty(entdesc)
        elif enttype == OBJECTPROPERTY_ENTITY:
            self.oob.addOrUpdateObjectProperty(entdesc)
        elif enttype == ANNOTATIONPROPERTY_ENTITY:
            self.oob.addOrUpdateAnnotationProperty(entdesc)
        elif enttype == INDIVIDUAL_ENTITY:
            self.oob.addOrUpdateIndividual(entdesc)

    def _test_addOrUpdateEntity(self, enttype, mismatch_id):
        """
        Generic method for testing addOrUpdateEntity() methods in
        OWLOntologyBuilder.

        enttype: The type constant for the entity to add/update.
        mismatch_id: The ID of an extant entity of a different type.
        """
        # Verify that a new entity (with no label or definition) is created.
        self.tr['Label'] = ''
        self.tr['Text definition'] = ''
        self._do_addOrUpdateEntity(enttype, self.tr)

        newent = self.test_ont.getExistingEntity(self.tr['ID'])
        self.assertIsNotNone(newent)
        self.assertEqual(enttype, newent.getTypeConst())
        self.assertEqual(0, len(newent.getLabels()))

        # Test updating the entity by adding a label and definition.
        self.tr['Label'] = 'label 1'
        self.tr['Text definition'] = 'Update definition.'
        self._do_addOrUpdateEntity(enttype, self.tr)
        # Make all non-required columns optional so we don't get a bunch of
        # warning log messages.
        self.tr.optional = [0]
        self.oob.processDeferredEntityAxioms()

        newent = self.test_ont.getExistingEntity(self.tr['ID'])
        self.assertIsNotNone(newent)
        self.assertEqual(enttype, newent.getTypeConst())
        self.assertEqual(['label 1'], newent.getLabels())
        self.assertEqual(
            ['Update definition.'],
            newent.getAnnotationValues(newent.DEFINITION_IRI)
        )

        # Check that mismatched labels are correctly handled.
        self.tr['Label'] = 'incorrect label'
        with self.assertRaisesRegexp(
            EntityDescriptionError,
            'does not match the label in the current source row'
        ):
            self._do_addOrUpdateEntity(enttype, self.tr)

        # Check that mismatched entity types are correctly handled.
        # Use the ID of an existing object property.
        self.tr['ID'] = mismatch_id
        with self.assertRaisesRegexp(
            EntityDescriptionError,
            'An entity with the ID {0} already exists in the ontology'.format(
                mismatch_id
            )
        ):
            self._do_addOrUpdateEntity(enttype, self.tr)

    def test_addOrUpdateClass(self):
        # OBTO:0001 is an object property.
        self._test_addOrUpdateEntity(CLASS_ENTITY, 'OBTO:0001')

    def test_addDataProperty(self):
        # Define additional row values.
        self.tr['Parent'] = 'obo:OBTO_2001'
        self.tr['Subproperty of'] = 'OBTO:1002'
        self.tr['Superproperty of'] = 'OBTO:1003'
        self.tr['Domain'] = "'test class 1'; OBITO:0001"
        self.tr['Range'] = 'xsd:float'
        self.tr['Disjoint with'] = 'OBTO:1000;OBTO:1001'
        self.tr['Characteristics'] = 'functional'

        # Create some additional properties for use in axioms.
        self.test_ont.createNewDataProperty('obo:OBTO_1000')
        self.test_ont.createNewDataProperty('obo:OBTO_1001')
        self.test_ont.createNewDataProperty('obo:OBTO_1002')
        self.test_ont.createNewDataProperty('obo:OBTO_1003')
        self.test_ont.createNewDataProperty('obo:OBTO_2001')

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
            'http://purl.obolibrary.org/obo/OBTO_2001',
            'http://purl.obolibrary.org/obo/OBTO_1002'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDataSubPropertyAxiomsForSubProperty(new_oaent):
            actualIRIs.add(axiom.getSuperProperty().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the superproperty axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_1003'
        }
        actualIRIs = set()
        for axiom in self.owlont.getDataSubPropertyAxiomsForSuperProperty(new_oaent):
            actualIRIs.add(axiom.getSubProperty().getIRI().toString())

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
            NEW_IRI,
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

    def test_addOrUpdateDataProperty(self):
        # OBTO:0001 is an object property.
        self._test_addOrUpdateEntity(DATAPROPERTY_ENTITY, 'OBTO:0001')

    def test_addObjectProperty(self):
        # Define additional row values.
        self.tr['Parent'] = 'obo:OBTO_2001'
        self.tr['Subproperty of'] = 'OBTO:1002'
        self.tr['Superproperty of'] = 'OBTO:1003'
        self.tr['Domain'] = 'obo:OBTO_3000'
        self.tr['Range'] = "'test class 1'; OBITO:0001"
        self.tr['Inverse'] = 'OBTO:1000'
        self.tr['Disjoint with'] = 'OBTO:1001'
        self.tr['Characteristics'] = 'functional, transitive'

        # Create some additional entities for use in axioms.
        self.test_ont.createNewObjectProperty('obo:OBTO_1000')
        self.test_ont.createNewObjectProperty('obo:OBTO_1001')
        self.test_ont.createNewObjectProperty('obo:OBTO_1002')
        self.test_ont.createNewObjectProperty('obo:OBTO_1003')
        self.test_ont.createNewObjectProperty('obo:OBTO_2001')
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
            'http://purl.obolibrary.org/obo/OBTO_2001',
            'http://purl.obolibrary.org/obo/OBTO_1002'
        }
        actualIRIs = set()
        for axiom in self.owlont.getObjectSubPropertyAxiomsForSubProperty(new_oaent):
            actualIRIs.add(axiom.getSuperProperty().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the superproperty axioms.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_1003'
        }
        actualIRIs = set()
        for axiom in self.owlont.getObjectSubPropertyAxiomsForSuperProperty(new_oaent):
            actualIRIs.add(axiom.getSubProperty().getIRI().toString())

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
            NEW_IRI,
            'http://purl.obolibrary.org/obo/OBTO_1000'
        }
        actualIRIs = set()
        for axiom in self.owlont.getInverseObjectPropertyAxioms(new_oaent):
            for dprop in axiom.getProperties():
                actualIRIs.add(dprop.getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the disjointness axiom.
        expIRIs = {
            NEW_IRI,
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

    def test_addOrUpdateObjectProperty(self):
        # OBTO:0020 is a data property.
        self._test_addOrUpdateEntity(OBJECTPROPERTY_ENTITY, 'OBTO:0020')

    def test_addAnnotationProperty(self):
        # Define additional row values.
        self.tr['Parent'] = 'obo:OBTO_2001'
        self.tr['Subproperty of'] = 'OBTO:1002'
        self.tr['Superproperty of'] = 'OBTO:1003'

        # Create additional properties for use in axioms.
        self.test_ont.createNewAnnotationProperty('obo:OBTO_2001')
        self.test_ont.createNewAnnotationProperty('obo:OBTO_1002')
        self.test_ont.createNewAnnotationProperty('obo:OBTO_1003')

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
            'http://purl.obolibrary.org/obo/OBTO_2001',
            'http://purl.obolibrary.org/obo/OBTO_1002'
        }
        actualIRIs = set()
        for axiom in self.owlont.getSubAnnotationPropertyOfAxioms(new_oaent):
            actualIRIs.add(axiom.getSuperProperty().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the superproperty axiom.
        expIRIs = {NEW_IRI}
        actualIRIs = set()
        subprop = self.test_ont.getExistingAnnotationProperty('OBTO:1003').getOWLAPIObj()
        for axiom in self.owlont.getSubAnnotationPropertyOfAxioms(subprop):
            actualIRIs.add(axiom.getSuperProperty().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

    def test_addOrUpdateAnnotationProperty(self):
        # OBTO:0020 is a data property.
        self._test_addOrUpdateEntity(ANNOTATIONPROPERTY_ENTITY, 'OBTO:0020')

    def test_addIndividual(self):
        # Define additional row values.
        self.tr['Instance of'] = 'obo:OBTO_0010; OBTO:0012'
        self.tr['Relations'] = """
            'test object property 1' 'test individual 1';
            not 'test object property 1' 'test individual 2'
        """
        self.tr['Data facts'] = """
            'test data property 1' "litval"^^xsd:string;
            not 'test data property 1' "litval3"^^xsd:string;
            'test data property 1' "litval2"^^xsd:string
        """

        self.oob.addIndividual(self.tr)

        # Process all deferred named individual axioms.
        self.oob.processDeferredEntityAxioms()

        # Check that the new individual exists.
        newindv = self.test_ont.getExistingIndividual(self.tr['ID'])
        self.assertIsNotNone(newindv)
        new_oaent = newindv.getOWLAPIObj()

        self._checkGenericAxioms(newindv)

        # Check the types of the individual.
        expIRIs = {
            'http://purl.obolibrary.org/obo/OBTO_0010',
            'http://purl.obolibrary.org/obo/OBTO_0012'
        }
        actualIRIs = set()
        for axiom in self.owlont.getClassAssertionAxioms(new_oaent):
            classexp = axiom.getClassExpression()
            actualIRIs.add(classexp.asOWLClass().getIRI().toString())

        self.assertEqual(expIRIs, actualIRIs)

        # Check the object property assertions.
        # Create a set with the expected subject, property, object IRI tuples.
        expected = {
            (
                str(new_oaent.getIRI()),
                'http://purl.obolibrary.org/obo/OBTO_0001',
                'http://purl.obolibrary.org/obo/OBTO_8000'
            )
        }

        axioms = self.owlont.getObjectPropertyAssertionAxioms(new_oaent)
        results = set()
        for axiom in axioms:
            factparts = (
                str(axiom.getSubject().getIRI()),
                str(axiom.getProperty().getIRI()),
                str(axiom.getObject().getIRI())
            )
            results.add(factparts)

        self.assertEqual(expected, results)

        # Check the negative object property assertions.
        # Create a set with the expected subject, property, object IRI tuples.
        expected = {
            (
                str(new_oaent.getIRI()),
                'http://purl.obolibrary.org/obo/OBTO_0001',
                'http://purl.obolibrary.org/obo/OBTO_8001'
            )
        }

        axioms = self.owlont.getNegativeObjectPropertyAssertionAxioms(
            new_oaent
        )
        results = set()
        for axiom in axioms:
            factparts = (
                str(axiom.getSubject().getIRI()),
                str(axiom.getProperty().getIRI()),
                str(axiom.getObject().getIRI())
            )
            results.add(factparts)

        self.assertEqual(expected, results)

        # Check the data property assertions.
        # Create a set with the expected subject, property, literal tuples.
        expected = {
            (
                str(new_oaent.getIRI()),
                'http://purl.obolibrary.org/obo/OBTO_0020',
                'litval'
            ),
            (
                str(new_oaent.getIRI()),
                'http://purl.obolibrary.org/obo/OBTO_0020',
                'litval2'
            )
        }

        axioms = self.owlont.getDataPropertyAssertionAxioms(new_oaent)
        results = set()
        for axiom in axioms:
            factparts = (
                str(axiom.getSubject().getIRI()),
                str(axiom.getProperty().getIRI()),
                str(axiom.getObject().getLiteral())
            )
            results.add(factparts)

        self.assertEqual(expected, results)

        # Check the negative data property assertions.
        # Create a set with the expected subject, property, literal tuples.
        expected = {
            (
                str(new_oaent.getIRI()),
                'http://purl.obolibrary.org/obo/OBTO_0020',
                'litval3'
            )
        }

        axioms = self.owlont.getNegativeDataPropertyAssertionAxioms(new_oaent)
        results = set()
        for axiom in axioms:
            factparts = (
                str(axiom.getSubject().getIRI()),
                str(axiom.getProperty().getIRI()),
                str(axiom.getObject().getLiteral())
            )
            results.add(factparts)

        self.assertEqual(expected, results)

    def test_addOrUpdateIndividual(self):
        # OBTO:0020 is a data property.
        self._test_addOrUpdateEntity(INDIVIDUAL_ENTITY, 'OBTO:0020')

    def test_expandDefinition(self):
        # Test an expansion that includes the label text.  Express the label in
        # all four different formats that should be supported, plus test cases
        # with a single missing quote around the label text.
        unprefixed_testvals = [
            "An example definition for {'test class 1'}.",
            'An example definition for {test class 1}.',
            "An example definition for {'test class 1}.",
            "An example definition for {test class 1'}."
        ]
        prefixed_testvals = [
            'An example definition for {OBTO:test class 1}.',
            "An example definition for {OBTO:'test class 1'}.",
            "An example definition for {OBTO:'test class 1}.",
            "An example definition for {OBTO:test class 1'}."
        ]

        for testval in unprefixed_testvals:
            self.assertEqual(
                "An example definition for 'test class 1' (OBTO:0010).",
                self.oob._expandDefinition(testval)
            )

        for testval in prefixed_testvals:
            self.assertEqual(
                "An example definition for OBTO:'test class 1' (OBTO:0010).",
                self.oob._expandDefinition(testval)
            )

        # Test an expansion for which the label text is suppressed.
        sourcestr = 'An example definition for {$test class 1}.'
        expstr = 'An example definition for (OBTO:0010).'
        self.assertEqual(expstr, self.oob._expandDefinition(sourcestr))

        # Test an expansion where the definition contains nothing but a label
        # text element.
        self.assertEqual(
            "'test class 1' (OBTO:0010)",
            self.oob._expandDefinition('{test class 1}')
        )

        # Test an expansion with multiple label text elements.
        sourcestr = 'An example with {test class 1} and {test class 2}.'
        expstr = (
            "An example with 'test class 1' (OBTO:0010) and 'test class 2' "
            "(OBTO:0011)."
        )
        self.assertEqual(
            expstr, self.oob._expandDefinition(sourcestr)
        )

        # Test an expansion with an empty set of braces.
        self.assertEqual(
            "An {} example definition.",
            self.oob._expandDefinition('An {} example definition.')
        )

        # Test an expansion with an empty set of braces followed by a label
        # element.
        self.assertEqual(
            "An {} example 'test class 1' (OBTO:0010).",
            self.oob._expandDefinition('An {} example {test class 1}.')
        )

        # Test an expansion where the definition does not contain any label
        # text elements.
        self.assertEqual(
            "An example definition.",
            self.oob._expandDefinition('An example definition.')
        )

        # Define a new, fake IRI prefix.
        ontman = self.test_ont.getOntologyManager()
        prefix_df = ontman.getOntologyFormat(self.owlont).asPrefixOWLOntologyFormat()
        prefix_df.setPrefix('fake:', 'http://this.is/a/fake/root/')

        # Define a new class with the fake root IRI and give it a label.
        newclass = self.test_ont.createNewClass('fake:ID_0001')
        newclass.addLabel('new fake class')

        # Test an expansion where the label does not resolve to an OBO IRI but
        # does map to a prefix IRI.
        self.assertEqual(
            "An example 'new fake class' (fake:ID_0001).",
            self.oob._expandDefinition("An example {'new fake class'}.")
        )

        # Define a new class with an IRI that does not map to either an OBO ID
        # or a prefix IRI and give it a label.
        newclass = self.test_ont.createNewClass('http://another.fake/ID_0001')
        newclass.addLabel('new fake class 2')

        # Test an expansion where the label does not map to either an OBO IRI
        # or a prefix IRI.
        self.assertEqual(
            "An example 'new fake class 2' (http://another.fake/ID_0001).",
            self.oob._expandDefinition("An example {'new fake class 2'}.")
        )

