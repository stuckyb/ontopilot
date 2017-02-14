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
from ontobuilder.inferred_axiom_adder import INFERENCE_TYPES
from test_ontology import INDIVIDUAL_IRI
import unittest
#from testfixtures import LogCapture

# Java imports.
from java.lang import UnsupportedOperationException
from org.semanticweb.owlapi.model import IRI


class NoOpReasoner:
    """
    This is a simple mock reasoner class that implements the OWLReasoner
    interface by throwing an UnsupportedOperationException for each reasoner
    method.  In addition, it tracks which methods have been called and the
    total number of calls.  Note that we do not explicitly subclass
    OWLReasoner, because doing so would cause the method call interception to
    fail.  Calls to required interface methods would generate
    NotImplementedError exceptions and would never hit the __getattr__()
    method.
    """
    def __init__(self):
        self.total_calls = 0
        self.methods_called = set()

    def __getattr__(self, name):
        def stub(*args, **kwargs):
            self.total_calls += 1
            self.methods_called.add(name)
            raise UnsupportedOperationException()

        return stub


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
        # Check all supported inference types.  There are 8 total.
        inftypes = INFERENCE_TYPES

        # First, test a mock reasoner with no inference support.  This will
        # confirm that all inference types are covered by the code for testing
        # inference support.
        noopr = NoOpReasoner()
        self.iaa.reasoner = noopr
        gens_list = self.iaa._getGeneratorsList(inftypes)

        # Check that the number of reasoner calls and the number of methods
        # called both match the total number of inference types.
        self.assertEqual(0, len(gens_list))
        self.assertEqual(len(INFERENCE_TYPES), noopr.total_calls)
        self.assertEqual(len(INFERENCE_TYPES), len(noopr.methods_called))

        # With real reasoners, just test that we're getting back the expected
        # number of unique generators for each combination of reasoner type and
        # set of inference type strings, rather than trying to check the types
        # of all returned generators.

        # HermiT should support all types of inferences.
        self.iaa.setReasoner('hermit')
        gens_list = self.iaa._getGeneratorsList(inftypes)
        # Convert the generators list to a set to ensure we are only counting
        # unique values.
        self.assertEqual(8, len(set(gens_list)))

        # ELK only supports a few inference types.
        self.iaa.setReasoner('elk')
        gens_list = self.iaa._getGeneratorsList(inftypes)
        self.assertEqual(3, len(set(gens_list)))

    def test_addInferredAxioms(self):
        """
        This does not attempt to exhaustively test every available type of
        inference.  Instead, it only tests the most commonly used inference
        types when generating inferred axioms for an ontology: class hierarchy,
        individual types, and class disjointness.  Furthermore, the tests
        implemented here are also designed to test important supporting
        algorithms, including identifying and removing duplicate axioms,
        finding and removing redundant subclass axioms, and removing trivial
        axioms.  Actually generating the inferred axioms is the responsibility
        of OWL API objects, so this approach to testing should be reasonable.
        """
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

        # Run the reasoner.
        inftypes = ['subclasses', 'types', 'disjoint classes']
        self.iaa.addInferredAxioms(inftypes)
        #self.ont.saveOntology('test_inferred.owl')

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

    def test_inconsistent(self):
        """
        Tests that attempts to add inferred axioms to an inconsistent ontology
        are handled correctly.
        """
        testont = Ontology('test_data/inconsistent.owl')
        testiaa = InferredAxiomAdder(testont, 'hermit')

        with self.assertRaisesRegexp(
            RuntimeError, 'The ontology is inconsistent'
        ):
            testiaa.addInferredAxioms(['subclasses'])

