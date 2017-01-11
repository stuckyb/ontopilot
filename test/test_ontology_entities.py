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
from ontobuilder.ontology_entities import (
    CLASS_ENTITY, DATAPROPERTY_ENTITY, OBJECTPROPERTY_ENTITY,
    ANNOTATIONPROPERTY_ENTITY
)
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


class _TestOntologyEntity:
    """
    Defines tests that apply to all ontology entities.  This class should not
    be instantiated directly; only its subclasses that target specific ontology
    entities should be run.  To help reinforce this, _TestOntologyEntity does
    not inherit from unittest.TestCase.  All subclasses of _TestOntologyEntity
    should inherit from unittest.TestCase and treat _TestOntologyEntity as a
    sort of "mixin" class that provides standard testing routines.
    """
    def setUp(self):
        self.test_ont = Ontology('test_data/ontology.owl')
        self.owlont = self.test_ont.getOWLOntology()

        # A test entity instance and IRI should be provided by child classes.
        self.t_ent = None
        self.t_entIRI = None

    def _checkAnnotation(self, annot_propIRI, valuestr):
        """
        Checks that the test entity is the subject of an annotation axiom with
        the specified property and value.
        """
        # Check that the entity has the required annotation and that the text
        # value is correct.
        found_annot = False
        for annot_ax in self.owlont.getAnnotationAssertionAxioms(self.t_entIRI):
            if annot_ax.getProperty().getIRI().equals(annot_propIRI):
                if annot_ax.getValue().getLiteral() == valuestr:
                    found_annot = True

        self.assertTrue(found_annot)

    def test_addDefinition(self):
        defstr = 'A new definition.'

        self.t_ent.addDefinition(defstr)

        # Test that the definition annotation exists and has the correct value.
        self._checkAnnotation(self.t_ent.DEFINITION_IRI, defstr)

    def test_addLabel(self):
        labelstr = 'term label!'

        self.t_ent.addLabel(labelstr)

        # Test that the label annotation exists and has the correct value.
        self._checkAnnotation(
            IRI.create('http://www.w3.org/2000/01/rdf-schema#label'), labelstr
        )

    def test_addComment(self):
        commentstr = 'A useful comment.'

        self.t_ent.addComment(commentstr)

        # Test that the comment annotation exists and has the correct value.
        self._checkAnnotation(
            IRI.create('http://www.w3.org/2000/01/rdf-schema#comment'),
            commentstr
        )


class Test_OntologyClass(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyClass.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        self.t_ent = self.test_ont.createNewClass(
                'http://purl.obolibrary.org/obo/OBTO_0011'
        )
        self.t_entIRI = self.t_ent.entityIRI

    def test_getTypeConst(self):
        self.assertEqual(CLASS_ENTITY, self.t_ent.getTypeConst())

    def test_addSubclassOf(self):
        superclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.t_ent.addSubclassOf("'test class 1'")

        # Check that the class has the correct superclass.
        found_superclass = False
        for axiom in self.owlont.getSubClassAxiomsForSubClass(self.t_ent.classobj):
            if axiom.getSuperClass().getIRI().equals(superclassIRI):
                found_superclass = True

        self.assertTrue(found_superclass)

    def test_addEquivalentTo(self):
        equivclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.t_ent.addEquivalentTo("'test class 1'")

        # Check that the class has the correct equivalency relationship.
        found_eqclass = False
        for axiom in self.owlont.getEquivalentClassesAxioms(self.t_ent.classobj):
            for eqclass in axiom.getNamedClasses():
                if eqclass.getIRI().equals(equivclassIRI):
                    found_eqclass = True

        self.assertTrue(found_eqclass)

    def test_addDisjointWith(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.t_ent.addDisjointWith("'test class 1'")

        # Check that the class has the correct disjointness relationship.
        found_class = False
        for axiom in self.owlont.getDisjointClassesAxioms(self.t_ent.classobj):
            for cl_exp in axiom.getClassExpressions():
                if not(cl_exp.isAnonymous()):
                    if cl_exp.asOWLClass().getIRI().equals(classIRI):
                        found_class = True

        self.assertTrue(found_class)


class Test_OntologyDataProperty(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyDataProperty.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        self.t_ent = self.test_ont.createNewDataProperty(
                'http://purl.obolibrary.org/obo/OBTO_0011'
        )
        self.t_entIRI = self.t_ent.entityIRI

    def test_getTypeConst(self):
        self.assertEqual(DATAPROPERTY_ENTITY, self.t_ent.getTypeConst())

    def test_addSuperproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0012')
        newprop = self.test_ont.createNewDataProperty(newpropIRI)

        self.t_ent.addSuperproperty('http://purl.obolibrary.org/obo/OBTO_0012')

        # Check that the property has the correct superproperty.
        found_prop = False
        for axiom in self.owlont.getDataSubPropertyAxiomsForSubProperty(self.t_ent.propobj):
            if axiom.getSuperProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

    def test_addDomain(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        self.t_ent.addDomain('http://purl.obolibrary.org/obo/OBTO_0010')

        # Check that the property has the correct domain.
        found_class = False
        for axiom in self.owlont.getDataPropertyDomainAxioms(self.t_ent.propobj):
            cl_exp = axiom.getDomain()
            if not(cl_exp.isAnonymous()):
                if cl_exp.asOWLClass().getIRI().equals(classIRI):
                    found_class = True

        self.assertTrue(found_class)

    def test_addRange(self):
        # Test a simple datatype data range.
        self.t_ent.addRange('xsd:float')

        # Check that the property has the correct range.
        found_drange = False
        for axiom in self.owlont.getDataPropertyRangeAxioms(self.t_ent.propobj):
            drange = axiom.getRange()
            if drange.isDatatype():
                if drange.asOWLDatatype().isFloat():
                    found_drange = True

        self.assertTrue(found_drange)

    def test_addDisjointWith(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0012')
        newprop = self.test_ont.createNewDataProperty(newpropIRI)

        self.t_ent.addDisjointWith('http://purl.obolibrary.org/obo/OBTO_0012')

        # Check that the property has the correct disjointness relationship.
        found_prop = False
        for axiom in self.owlont.getDisjointDataPropertiesAxioms(self.t_ent.propobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)

    def test_makeFunctional(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getFunctionalDataPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeFunctional()
        axioms = self.owlont.getFunctionalDataPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())


class Test_OntologyObjectProperty(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyDataProperty.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        self.t_ent = self.test_ont.createNewObjectProperty(
                'http://purl.obolibrary.org/obo/OBTO_0011'
        )
        self.t_entIRI = self.t_ent.entityIRI

    def test_getTypeConst(self):
        self.assertEqual(OBJECTPROPERTY_ENTITY, self.t_ent.getTypeConst())

    def test_addSuperproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0012')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addSuperproperty('http://purl.obolibrary.org/obo/OBTO_0012')

        # Check that the property has the correct superproperty.
        found_prop = False
        for axiom in self.owlont.getObjectSubPropertyAxiomsForSubProperty(self.t_ent.propobj):
            if axiom.getSuperProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

    def test_addDomain(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        self.t_ent.addDomain('http://purl.obolibrary.org/obo/OBTO_0010')

        # Check that the property has the correct domain.
        found_class = False
        for axiom in self.owlont.getObjectPropertyDomainAxioms(self.t_ent.propobj):
            cl_exp = axiom.getDomain()
            if not(cl_exp.isAnonymous()):
                if cl_exp.asOWLClass().getIRI().equals(classIRI):
                    found_class = True

        self.assertTrue(found_class)

    def test_addRange(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        self.t_ent.addRange('http://purl.obolibrary.org/obo/OBTO_0010')

        # Check that the property has the correct range.
        found_class = False
        for axiom in self.owlont.getObjectPropertyRangeAxioms(self.t_ent.propobj):
            cl_exp = axiom.getRange()
            if not(cl_exp.isAnonymous()):
                if cl_exp.asOWLClass().getIRI().equals(classIRI):
                    found_class = True

        self.assertTrue(found_class)

    def test_addInverse(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0012')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addInverse('http://purl.obolibrary.org/obo/OBTO_0012')

        # Check that the property has the correct inverse.
        found_prop = False
        for axiom in self.owlont.getInverseObjectPropertyAxioms(self.t_ent.propobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)


    def test_addDisjointWith(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0012')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addDisjointWith('http://purl.obolibrary.org/obo/OBTO_0012')

        # Check that the property has the correct disjointness relationship.
        found_prop = False
        for axiom in self.owlont.getDisjointObjectPropertiesAxioms(self.t_ent.propobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)

    def test_makeFunctional(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getFunctionalObjectPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeFunctional()
        axioms = self.owlont.getFunctionalObjectPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())

    def test_makeInverseFunctional(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getInverseFunctionalObjectPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property inverse functional and check the result.
        self.t_ent.makeInverseFunctional()
        axioms = self.owlont.getInverseFunctionalObjectPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())

    def test_makeReflexive(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getReflexiveObjectPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeReflexive()
        axioms = self.owlont.getReflexiveObjectPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())

    def test_makeIrreflexive(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getIrreflexiveObjectPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeIrreflexive()
        axioms = self.owlont.getIrreflexiveObjectPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())

    def test_makeSymmetric(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getSymmetricObjectPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeSymmetric()
        axioms = self.owlont.getSymmetricObjectPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())

    def test_makeAsymmetric(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getAsymmetricObjectPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeAsymmetric()
        axioms = self.owlont.getAsymmetricObjectPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())

    def test_makeTransitive(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getTransitiveObjectPropertyAxioms(self.t_ent.propobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeTransitive()
        axioms = self.owlont.getTransitiveObjectPropertyAxioms(self.t_ent.propobj)
        self.assertEqual(1, axioms.size())


class Test_OntologyAnnotationProperty(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyAnnotationProperty.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        self.t_ent = self.test_ont.createNewAnnotationProperty(
                'http://purl.obolibrary.org/obo/OBTO_0011'
        )
        self.t_entIRI = self.t_ent.entityIRI

    def test_getTypeConst(self):
        self.assertEqual(ANNOTATIONPROPERTY_ENTITY, self.t_ent.getTypeConst())

    def test_addSuperproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0012')
        newprop = self.test_ont.createNewAnnotationProperty(newpropIRI)

        self.t_ent.addSuperproperty('http://purl.obolibrary.org/obo/OBTO_0012')

        # Check that the property has the correct superproperty.
        found_prop = False
        for axiom in self.owlont.getSubAnnotationPropertyOfAxioms(self.t_ent.propobj):
            if axiom.getSuperProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

