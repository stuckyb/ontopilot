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
from ontobuilder.ontology import CLASS_ENTITY, DATAPROPERTY_ENTITY
from ontobuilder.ontology import OBJECTPROPERTY_ENTITY, ANNOTATIONPROPERTY_ENTITY
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


class Test_OntologyClass(unittest.TestCase):
    """
    Tests _OntologyClass.
    """
    def setUp(self):
        self.test_ont = Ontology('test_data/ontology.owl')
        self.owlont = self.test_ont.getOWLOntology()
        self.tclass = self.test_ont.createNewClass(
                'http://purl.obolibrary.org/obo/OBTO_0011'
        )

    def _checkAnnotation(self, propIRI, valuestr):
        """
        Checks that the test class is the subject of an annotation axiom with
        the specified property and value.
        """
        # Check that the class has the required annotation and that the text
        # value is correct.
        found_annot = False
        for annot_ax in self.owlont.getAnnotationAssertionAxioms(self.tclass.classIRI):
            if annot_ax.getProperty().getIRI().equals(propIRI):
                found_annot = True
                self.assertEqual(valuestr, annot_ax.getValue().getLiteral())

        self.assertTrue(found_annot)

    def test_getTypeConst(self):
        self.assertEqual(CLASS_ENTITY, self.tclass.getTypeConst())

    def test_addDefinition(self):
        defstr = 'A new definition.'

        self.tclass.addDefinition(defstr)

        # Test that the definition annotation exists and has the correct value.
        self._checkAnnotation(self.tclass.DEFINITION_IRI, defstr)

    def test_addLabel(self):
        labelstr = 'term label!'

        self.tclass.addLabel(labelstr)

        # Test that the label annotation exists and has the correct value.
        self._checkAnnotation(
            IRI.create('http://www.w3.org/2000/01/rdf-schema#label'), labelstr
        )

    def test_addComment(self):
        commentstr = 'A useful comment.'

        self.tclass.addComment(commentstr)

        # Test that the comment annotation exists and has the correct value.
        self._checkAnnotation(
            IRI.create('http://www.w3.org/2000/01/rdf-schema#comment'),
            commentstr
        )

    def test_addSubclassOf(self):
        superclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.tclass.addSubclassOf("'test class 1'")

        # Check that the class has the correct superclass.
        found_superclass = False
        for axiom in self.owlont.getSubClassAxiomsForSubClass(self.tclass.classobj):
            if axiom.getSuperClass().getIRI().equals(superclassIRI):
                found_superclass = True

        self.assertTrue(found_superclass)

    def test_addEquivalentTo(self):
        equivclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.tclass.addEquivalentTo("'test class 1'")

        # Check that the class has the correct equivalency relationship.
        found_eqclass = False
        for axiom in self.owlont.getEquivalentClassesAxioms(self.tclass.classobj):
            for eqclass in axiom.getNamedClasses():
                if eqclass.getIRI().equals(equivclassIRI):
                    found_eqclass = True

        self.assertTrue(found_eqclass)

    def test_addDisjointWith(self):
        classIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')

        # Test a simple class expression that is only a class label.
        self.tclass.addDisjointWith("'test class 1'")

        # Check that the class has the correct disjointness relationship.
        found_class = False
        for axiom in self.owlont.getDisjointClassesAxioms(self.tclass.classobj):
            for cl_exp in axiom.getClassExpressions():
                if not(cl_exp.isAnonymous()):
                    if cl_exp.asOWLClass().getIRI().equals(classIRI):
                        found_class = True

        self.assertTrue(found_class)

