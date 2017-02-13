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
from ontobuilder.inferred_axiom_adder import InferredAxiomAdder
from test_ontology import INDIVIDUAL_IRI
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


class Test_InferredAxiomAdder(unittest.TestCase):
    """
    Tests the InferredAxiomAdder class.
    """
    def setUp(self):
        ont = Ontology('test_data/ontology.owl')
        self.ont = ont
        self.owlont = self.ont.getOWLOntology()
        self.iaa = InferredAxiomAdder(ont, 'hermit')

    def test_getGeneratorsList(self):
        # For now, just test that we're getting back the expected number of
        # generators for each reasoner type, rather than trying to check the
        # types of all returned generators.
        self.iaa.setReasoner('elk')
        self.assertEqual(
            4, len(self.iaa._getGeneratorsList(True))
        )

        self.iaa.setReasoner('hermit')
        self.assertEqual(
            6, len(self.iaa._getGeneratorsList(True))
        )

    def test_addInferredAxioms(self):
        testclassIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0012')
        testclass = self.ont.df.getOWLClass(testclassIRI)

        parentIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')
        grandparentIRI = IRI.create('http://purl.obolibrary.org/obo/OBITO_0001')

        individualIRI = IRI.create(INDIVIDUAL_IRI)
        individual = self.ont.df.getOWLNamedIndividual(individualIRI)

        # Prior to running the reasoner, OBTO_0012 should only have OBITO_0001
        # as an asserted superclass.
        axioms = self.owlont.getSubClassAxiomsForSubClass(testclass)
        self.assertEqual(1, axioms.size())
        superclass = axioms.iterator().next().getSuperClass().asOWLClass()
        self.assertTrue(superclass.getIRI().equals(grandparentIRI))

        # Individual individual_002 should only have OBTO_0010 as its type.
        axioms = self.owlont.getClassAssertionAxioms(individual)
        self.assertEqual(1, axioms.size())
        typeclass = axioms.iterator().next().getClassExpression().asOWLClass()
        self.assertTrue(typeclass.getIRI().equals(parentIRI))

        # Class OBTO_0012 should not have any disjointness axioms.
        self.assertTrue(
            self.owlont.getDisjointClassesAxioms(testclass).isEmpty()
        )

        # Run the reasoner.  Include disjointness axioms.
        self.iaa.addInferredAxioms(True)
        self.ont.saveOntology('blah.owl')

        # Make sure that there are no trivial axioms in the ontology (e.g.,
        # axioms that involve owl:Thing).
        self.assertFalse(
            self.owlont.containsEntityInSignature(self.ont.df.getOWLThing())
        )

        # After running the reasoner and removing redundant "subclass of"
        # axioms, OBTO_0012 should only have OBTO_0010 as an asserted
        # superclass.
        axioms = self.owlont.getSubClassAxiomsForSubClass(testclass)
        self.assertEqual(1, axioms.size())
        superclass = axioms.iterator().next().getSuperClass().asOWLClass()
        self.assertTrue(superclass.getIRI().equals(parentIRI))

        # Individual individual_002 should now have OBTO_0010, OBTO_0012, and
        # OBITO_0001 as its types.
        axioms = self.owlont.getClassAssertionAxioms(individual)
        self.assertEqual(3, axioms.size())
        expected_typeiri_strs = {
            testclassIRI.toString(), parentIRI.toString(),
            grandparentIRI.toString()
        }
        typeiri_strs = set()
        for axiom in axioms:
            typeiri_strs.add(
                axiom.getClassExpression().asOWLClass().getIRI().toString()
            )
        self.assertEqual(expected_typeiri_strs, typeiri_strs)

        # Class OBTO_0012 should now be disjoint with OBTO_0011.
        disjointIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0011')
        disjointclass = self.ont.df.getOWLClass(disjointIRI)
        axioms = self.owlont.getDisjointClassesAxioms(testclass)
        self.assertEqual(1, axioms.size())
        self.assertTrue(
            axioms.iterator().next().containsEntityInSignature(disjointclass)
        )
