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
from ontopilot.ontology_entities import (
    CLASS_ENTITY, DATAPROPERTY_ENTITY, OBJECTPROPERTY_ENTITY,
    ANNOTATIONPROPERTY_ENTITY, INDIVIDUAL_ENTITY
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
    # Annotation IRIs.
    LABEL_IRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#label')
    COMMENT_IRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#comment')

    def setUp(self):
        self.test_ont = Ontology('test_data/ontology.owl')
        self.owlont = self.test_ont.getOWLOntology()

        # A test entity instance, OWL API object, and IRI should be provided by
        # child classes by calling _setEntityObject().
        self.t_ent = None
        self.t_owlapiobj = None
        self.t_entIRI = None

    def _setEntityObject(self, entityobj):
        self.t_ent = entityobj
        self.t_owlapiobj = self.t_ent.getOWLAPIObj()
        self.t_entIRI = self.t_ent.getIRI()

    def _checkAnnotation(self, annot_propIRI, valuestrs):
        """
        Checks that the test entity is the subject of an annotation axiom with
        the specified property and value(s).
        """
        if isinstance(valuestrs, basestring):
            strlist = [valuestrs]
        else:
            strlist = valuestrs

        # Check that the entity has the required annotation and that the text
        # value is correct.
        annotvals = self.t_ent.getAnnotationValues(annot_propIRI)
        self.assertEqual(sorted(strlist), sorted(annotvals))

    def test_addDefinition(self):
        defstr = 'A new definition.'

        self.t_ent.addDefinition(defstr)

        # Test that the definition annotation exists and has the correct value.
        self._checkAnnotation(self.t_ent.DEFINITION_IRI, defstr)

    def test_getDefinitions(self):
        # Test the case of no definitions.
        self.assertEqual(0, len(self.t_ent.getDefinitions()))

        # Test a single definition.
        self.t_ent.addDefinition('Definition 1.')
        defvals = self.t_ent.getDefinitions()
        self.assertEqual(['Definition 1.'], defvals)

        # Test multiple definitions.
        self.t_ent.addDefinition('Definition 2.')
        defvals = self.t_ent.getDefinitions()
        self.assertEqual(['Definition 1.', 'Definition 2.'], sorted(defvals))

    def test_addLabel(self):
        labelstr = 'term label!'

        self.t_ent.addLabel(labelstr)

        # Test that the label annotation exists and has the correct value.
        self._checkAnnotation(self.LABEL_IRI, labelstr)

        # Check a label string enclosed in single quotes.
        self.t_ent.addLabel("'another label'")
        self._checkAnnotation(self.LABEL_IRI, ['another label', labelstr])

    def test_getLabels(self):
        # Test the case of no labels.
        self.assertEqual(0, len(self.t_ent.getLabels()))

        # Test a single label.
        self.t_ent.addLabel('Label 1')
        labelvals = self.t_ent.getLabels()
        self.assertEqual(['Label 1'], labelvals)

        # Test multiple labels.
        self.t_ent.addLabel('Label 2')
        labelvals = self.t_ent.getLabels()
        self.assertEqual(['Label 1', 'Label 2'], sorted(labelvals))

    def test_addComment(self):
        commentstr = 'A useful comment.'

        self.t_ent.addComment(commentstr)

        # Test that the comment annotation exists and has the correct value.
        self._checkAnnotation(self.COMMENT_IRI, commentstr)

    def test_getComments(self):
        # Test the case of no comments.
        self.assertEqual(0, len(self.t_ent.getComments()))

        # Test a single comment.
        self.t_ent.addComment('Comment 1.')
        vals = self.t_ent.getComments()
        self.assertEqual(['Comment 1.'], vals)

        # Test multiple comments.
        self.t_ent.addComment('Comment 2.')
        vals = self.t_ent.getComments()
        self.assertEqual(['Comment 1.', 'Comment 2.'], sorted(vals))

    def test_addAnnotation(self):
        annotprop_iri = IRI.create('http://purl.obolibrary.org/obo/OBTO_0030')
        annot_txt = 'Test annotation text.'

        self.t_ent.addAnnotation(annotprop_iri, annot_txt)

        self._checkAnnotation(annotprop_iri, annot_txt)

    def test_getAnnotationValues(self):
        # Test the case of no annotations.
        self.assertEqual(
            0, len(self.t_ent.getAnnotationValues(self.LABEL_IRI))
        )

        # Test a single annotation value.
        self.t_ent.addLabel('A label!!')
        annotvals = self.t_ent.getAnnotationValues(self.LABEL_IRI)
        self.assertEqual(['A label!!'], annotvals)

        # Test multiple annotation values.
        commentvals = ['Comment 1', 'Comment 2']
        for commentval in commentvals:
            self.t_ent.addComment(commentval)

        annotvals = self.t_ent.getAnnotationValues(self.COMMENT_IRI)
        self.assertEqual(sorted(commentvals), sorted(annotvals))

    def test_hash(self):
        """
        Tests that entities will behave as expected when they are hashed.  Two
        entity instances that point to the same ontology entity should produce
        equal hashes.
        """
        # Get another instance of the same entity.
        entcpy = self.test_ont.getExistingEntity(self.t_entIRI)

        # Verify that the instances are not the same.
        self.assertFalse(self.t_entIRI is entcpy)

        # Check the hash values.
        self.assertEqual(hash(self.t_ent), hash(entcpy))
        self.assertEqual(hash(self.t_owlapiobj), hash(entcpy.getOWLAPIObj()))

        # Check the equality operator.
        self.assertTrue(self.t_ent == entcpy)

        # Check the inequality operator.
        self.assertFalse(self.t_ent != entcpy)


class Test_OntologyClass(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyClass.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        t_ent = self.test_ont.createNewClass(
                'http://purl.obolibrary.org/obo/OBTO_0013'
        )

        self._setEntityObject(t_ent)

    def test_getTypeConst(self):
        self.assertEqual(CLASS_ENTITY, self.t_ent.getTypeConst())

    def test_addSuperclass(self):
        superclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.t_ent.addSuperclass("'test class 1'")

        # Check that the class has the correct superclass.
        found_superclass = False
        for axiom in self.owlont.getSubClassAxiomsForSubClass(self.t_owlapiobj):
            if axiom.getSuperClass().getIRI().equals(superclassIRI):
                found_superclass = True

        self.assertTrue(found_superclass)

    def test_addSubclass(self):
        subclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.t_ent.addSubclass("'test class 1'")

        # Check that the class has the correct subclass.
        found_subclass = False
        for axiom in self.owlont.getSubClassAxiomsForSuperClass(self.t_owlapiobj):
            if axiom.getSubClass().getIRI().equals(subclassIRI):
                found_subclass = True

        self.assertTrue(found_subclass)

    def test_addEquivalentTo(self):
        equivclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.t_ent.addEquivalentTo("'test class 1'")

        # Check that the class has the correct equivalency relationship.
        found_eqclass = False
        for axiom in self.owlont.getEquivalentClassesAxioms(self.t_owlapiobj):
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
        for axiom in self.owlont.getDisjointClassesAxioms(self.t_owlapiobj):
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

        t_ent = self.test_ont.createNewDataProperty(
                'http://purl.obolibrary.org/obo/OBTO_0021'
        )

        self._setEntityObject(t_ent)

    def test_getTypeConst(self):
        self.assertEqual(DATAPROPERTY_ENTITY, self.t_ent.getTypeConst())

    def test_addSuperproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0022')
        newprop = self.test_ont.createNewDataProperty(newpropIRI)

        self.t_ent.addSuperproperty('http://purl.obolibrary.org/obo/OBTO_0022')

        # Check that the property has the correct superproperty.
        found_prop = False
        for axiom in self.owlont.getDataSubPropertyAxiomsForSubProperty(self.t_owlapiobj):
            if axiom.getSuperProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

    def test_addSubproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0022')
        newprop = self.test_ont.createNewDataProperty(newpropIRI)

        self.t_ent.addSubproperty('http://purl.obolibrary.org/obo/OBTO_0022')

        # Check that the property has the correct subproperty.
        found_prop = False
        for axiom in self.owlont.getDataSubPropertyAxiomsForSuperProperty(self.t_owlapiobj):
            if axiom.getSubProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

    def test_addDomain(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        self.t_ent.addDomain('http://purl.obolibrary.org/obo/OBTO_0010')

        # Check that the property has the correct domain.
        found_class = False
        for axiom in self.owlont.getDataPropertyDomainAxioms(self.t_owlapiobj):
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
        for axiom in self.owlont.getDataPropertyRangeAxioms(self.t_owlapiobj):
            drange = axiom.getRange()
            if drange.isDatatype():
                if drange.asOWLDatatype().isFloat():
                    found_drange = True

        self.assertTrue(found_drange)

    def test_addEquivalentTo(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0022')
        newprop = self.test_ont.createNewDataProperty(newpropIRI)

        self.t_ent.addEquivalentTo('http://purl.obolibrary.org/obo/OBTO_0022')

        # Check that the property has the correct equivalency relationship.
        found_prop = False
        for axiom in self.owlont.getEquivalentDataPropertiesAxioms(self.t_owlapiobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)

    def test_addDisjointWith(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0022')
        newprop = self.test_ont.createNewDataProperty(newpropIRI)

        self.t_ent.addDisjointWith('http://purl.obolibrary.org/obo/OBTO_0022')

        # Check that the property has the correct disjointness relationship.
        found_prop = False
        for axiom in self.owlont.getDisjointDataPropertiesAxioms(self.t_owlapiobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)

    def test_makeFunctional(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getFunctionalDataPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeFunctional()
        axioms = self.owlont.getFunctionalDataPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())


class Test_OntologyObjectProperty(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyDataProperty.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        t_ent = self.test_ont.createNewObjectProperty(
                'http://purl.obolibrary.org/obo/OBTO_0002'
        )

        self._setEntityObject(t_ent)

    def test_getTypeConst(self):
        self.assertEqual(OBJECTPROPERTY_ENTITY, self.t_ent.getTypeConst())

    def test_addSuperproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0003')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addSuperproperty('http://purl.obolibrary.org/obo/OBTO_0003')

        # Check that the property has the correct superproperty.
        found_prop = False
        for axiom in self.owlont.getObjectSubPropertyAxiomsForSubProperty(self.t_owlapiobj):
            if axiom.getSuperProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

    def test_addSubproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0003')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addSubproperty('http://purl.obolibrary.org/obo/OBTO_0003')

        # Check that the property has the correct subproperty.
        found_prop = False
        for axiom in self.owlont.getObjectSubPropertyAxiomsForSuperProperty(self.t_owlapiobj):
            if axiom.getSubProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

    def test_addDomain(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        self.t_ent.addDomain('http://purl.obolibrary.org/obo/OBTO_0010')

        # Check that the property has the correct domain.
        found_class = False
        for axiom in self.owlont.getObjectPropertyDomainAxioms(self.t_owlapiobj):
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
        for axiom in self.owlont.getObjectPropertyRangeAxioms(self.t_owlapiobj):
            cl_exp = axiom.getRange()
            if not(cl_exp.isAnonymous()):
                if cl_exp.asOWLClass().getIRI().equals(classIRI):
                    found_class = True

        self.assertTrue(found_class)

    def test_addInverse(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0003')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addInverse('http://purl.obolibrary.org/obo/OBTO_0003')

        # Check that the property has the correct inverse.
        found_prop = False
        for axiom in self.owlont.getInverseObjectPropertyAxioms(self.t_owlapiobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)


    def test_addEquivalentTo(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0003')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addEquivalentTo('http://purl.obolibrary.org/obo/OBTO_0003')

        # Check that the property has the correct equivalency relationship.
        found_prop = False
        for axiom in self.owlont.getEquivalentObjectPropertiesAxioms(self.t_owlapiobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)

    def test_addDisjointWith(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0003')
        newprop = self.test_ont.createNewObjectProperty(newpropIRI)

        self.t_ent.addDisjointWith('http://purl.obolibrary.org/obo/OBTO_0003')

        # Check that the property has the correct disjointness relationship.
        found_prop = False
        for axiom in self.owlont.getDisjointObjectPropertiesAxioms(self.t_owlapiobj):
            for dprop in axiom.getProperties():
                if dprop.getIRI().equals(newpropIRI):
                    found_prop = True

        self.assertTrue(found_prop)

    def test_makeFunctional(self):
        # Verify that the property is not functional by default.
        axioms = self.owlont.getFunctionalObjectPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property functional and check the result.
        self.t_ent.makeFunctional()
        axioms = self.owlont.getFunctionalObjectPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())

    def test_makeInverseFunctional(self):
        # Verify that the property is not inverse functional by default.
        axioms = self.owlont.getInverseFunctionalObjectPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property inverse functional and check the result.
        self.t_ent.makeInverseFunctional()
        axioms = self.owlont.getInverseFunctionalObjectPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())

    def test_makeReflexive(self):
        # Verify that the property is not reflexive by default.
        axioms = self.owlont.getReflexiveObjectPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property reflexive and check the result.
        self.t_ent.makeReflexive()
        axioms = self.owlont.getReflexiveObjectPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())

    def test_makeIrreflexive(self):
        # Verify that the property is not irreflexive by default.
        axioms = self.owlont.getIrreflexiveObjectPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property irreflexive and check the result.
        self.t_ent.makeIrreflexive()
        axioms = self.owlont.getIrreflexiveObjectPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())

    def test_makeSymmetric(self):
        # Verify that the property is not symmetric by default.
        axioms = self.owlont.getSymmetricObjectPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property symmetric and check the result.
        self.t_ent.makeSymmetric()
        axioms = self.owlont.getSymmetricObjectPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())

    def test_makeAsymmetric(self):
        # Verify that the property is not asymmetric by default.
        axioms = self.owlont.getAsymmetricObjectPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property asymmetric and check the result.
        self.t_ent.makeAsymmetric()
        axioms = self.owlont.getAsymmetricObjectPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())

    def test_makeTransitive(self):
        # Verify that the property is not transitive by default.
        axioms = self.owlont.getTransitiveObjectPropertyAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Make the property transitive and check the result.
        self.t_ent.makeTransitive()
        axioms = self.owlont.getTransitiveObjectPropertyAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())


class Test_OntologyAnnotationProperty(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyAnnotationProperty.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        t_ent = self.test_ont.createNewAnnotationProperty(
                'http://purl.obolibrary.org/obo/OBTO_0031'
        )

        self._setEntityObject(t_ent)

    def test_getTypeConst(self):
        self.assertEqual(ANNOTATIONPROPERTY_ENTITY, self.t_ent.getTypeConst())

    def test_addSuperproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0032')
        newprop = self.test_ont.createNewAnnotationProperty(newpropIRI)

        self.t_ent.addSuperproperty('http://purl.obolibrary.org/obo/OBTO_0032')

        # Check that the property has the correct superproperty.
        found_prop = False
        for axiom in self.owlont.getSubAnnotationPropertyOfAxioms(self.t_owlapiobj):
            if axiom.getSuperProperty().getIRI().equals(newpropIRI):
                found_prop = True

        self.assertTrue(found_prop)

    def test_addSubproperty(self):
        newpropIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0032')
        newprop = self.test_ont.createNewAnnotationProperty(newpropIRI)

        self.t_ent.addSubproperty('http://purl.obolibrary.org/obo/OBTO_0032')

        # Check that the property has the correct subproperty.
        found_prop = False
        subprop = self.test_ont.getExistingAnnotationProperty(newpropIRI).getOWLAPIObj()
        for axiom in self.owlont.getSubAnnotationPropertyOfAxioms(subprop):
            if axiom.getSuperProperty().getIRI().equals(self.t_entIRI):
                found_prop = True

        self.assertTrue(found_prop)


class Test_OntologyIndividual(_TestOntologyEntity, unittest.TestCase):
    """
    Tests _OntologyIndividual.
    """
    def setUp(self):
        _TestOntologyEntity.setUp(self)

        t_ent = self.test_ont.createNewIndividual(
                'http://purl.obolibrary.org/obo/OBTO_0042'
        )

        self._setEntityObject(t_ent)

    def test_getTypeConst(self):
        self.assertEqual(INDIVIDUAL_ENTITY, self.t_ent.getTypeConst())

    def test_addType(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Verify that the individual does not yet have any type information.
        axioms = self.owlont.getClassAssertionAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        # Add a type for the individual, using a simple class expression that
        # is only a class label.
        self.t_ent.addType("'test class 1'")

        # Check that the individual has the correct type.
        axioms = self.owlont.getClassAssertionAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())
        found_typeclass = False
        for axiom in axioms:
            classexp = axiom.getClassExpression()
            if not(classexp.isAnonymous()):
                if classexp.asOWLClass().getIRI().equals(classIRI):
                    found_typeclass = True

        self.assertTrue(found_typeclass)

    def test_addObjectPropertyFact(self):
        objprop = self.test_ont.getExistingObjectProperty('OBTO:0001')
        indv = self.test_ont.getExistingIndividual("'test individual 1'")

        # Verify that there are not yet any object property facts for this
        # individual.
        axioms = self.owlont.getObjectPropertyAssertionAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        self.t_ent.addObjectPropertyFact(
            'OBTO:0001', "'test individual 1'", is_negative=False
        )

        # Check that the correct object property assertion now exists.
        axioms = self.owlont.getObjectPropertyAssertionAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(objprop.getOWLAPIObj()))
        self.assertTrue(axiom.getSubject().equals(self.t_owlapiobj))
        self.assertTrue(axiom.getObject().equals(indv.getOWLAPIObj()))

        # Verify that there are not yet any negative object property facts for
        # this individual.
        axioms = self.owlont.getNegativeObjectPropertyAssertionAxioms(
            self.t_owlapiobj
        )
        self.assertTrue(axioms.isEmpty())

        self.t_ent.addObjectPropertyFact(
            'OBTO:0001', "'test individual 2'", is_negative=True
        )

        # Check that the correct negative object property assertion now exists.
        indv = self.test_ont.getExistingIndividual("'test individual 2'")
        axioms = self.owlont.getNegativeObjectPropertyAssertionAxioms(
            self.t_owlapiobj
        )
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(objprop.getOWLAPIObj()))
        self.assertTrue(axiom.getSubject().equals(self.t_owlapiobj))
        self.assertTrue(axiom.getObject().equals(indv.getOWLAPIObj()))

    def test_addDataPropertyFact(self):
        dataprop = self.test_ont.getExistingDataProperty('OBTO:0020')

        # Verify that there are not yet any data property facts for this
        # individual.
        axioms = self.owlont.getDataPropertyAssertionAxioms(self.t_owlapiobj)
        self.assertTrue(axioms.isEmpty())

        self.t_ent.addDataPropertyFact(
            'OBTO:0020', '"literal"^^xsd:string', is_negative=False
        )

        # Check that the correct data property assertion now exists.
        axioms = self.owlont.getDataPropertyAssertionAxioms(self.t_owlapiobj)
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(dataprop.getOWLAPIObj()))
        self.assertTrue(axiom.getSubject().equals(self.t_owlapiobj))
        self.assertEqual('literal', axiom.getObject().getLiteral())

        # Verify that there are not yet any negative data property facts for
        # this individual.
        axioms = self.owlont.getNegativeDataPropertyAssertionAxioms(
            self.t_owlapiobj
        )
        self.assertTrue(axioms.isEmpty())

        self.t_ent.addDataPropertyFact(
            'OBTO:0020', '"literal2"^^xsd:string', is_negative=True
        )

        # Check that the correct data property assertion now exists.
        axioms = self.owlont.getNegativeDataPropertyAssertionAxioms(
            self.t_owlapiobj
        )
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(dataprop.getOWLAPIObj()))
        self.assertTrue(axiom.getSubject().equals(self.t_owlapiobj))
        self.assertEqual('literal2', axiom.getObject().getLiteral())

