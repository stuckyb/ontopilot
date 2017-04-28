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
from ontopilot.inferred_axiom_adder import InferredAxiomAdder
from ontopilot.inferred_axiom_adder import INFERENCE_TYPES
from test_ontology import INDIVIDUAL_IRI
import unittest
#from testfixtures import LogCapture

# Java imports.
from java.lang import UnsupportedOperationException
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model import AxiomType


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

    def test_addInversePropAssertions(self):
        # Create a pair of inverse object properties.
        ent = self.ont.createNewObjectProperty('OBTO:0002')
        prop_2 = ent.getOWLAPIObj()
        ent2 = self.ont.createNewObjectProperty('OBTO:0003')
        prop_3 = ent2.getOWLAPIObj()
        ent.addInverse('OBTO:0003')

        # Create a symmetric object property.
        ent = self.ont.createNewObjectProperty('OBTO:0004')
        prop_4 = ent.getOWLAPIObj()
        ent.makeSymmetric()

        # Create a pair of individuals related by the inverse properties as
        # OBTO:0001.
        ent = self.ont.createNewIndividual('OBTO:0042')
        indv_42 = ent.getOWLAPIObj()
        ent2 = self.ont.createNewIndividual('OBTO:0043')
        indv_43 = ent2.getOWLAPIObj()
        ent.addObjectPropertyFact('OBTO:0002', 'OBTO:0043')

        # Create a pair of individuals related by the inverse properties as
        # OBTO:0002.
        ent = self.ont.createNewIndividual('OBTO:0044')
        indv_44 = ent.getOWLAPIObj()
        ent2 = self.ont.createNewIndividual('OBTO:0045')
        indv_45 = ent2.getOWLAPIObj()
        ent.addObjectPropertyFact('OBTO:0003', 'OBTO:0045')

        # Create a pair of individuals related by the symmetric property.
        ent = self.ont.createNewIndividual('OBTO:0046')
        indv_46 = ent.getOWLAPIObj()
        ent2 = self.ont.createNewIndividual('OBTO:0047')
        indv_47 = ent2.getOWLAPIObj()
        ent.addObjectPropertyFact('OBTO:0004', 'OBTO:0047')

        # Create a pair of individuals related by the inverse properties as
        # OBTO:0001 in a negative object property assertion.
        ent = self.ont.createNewIndividual('OBTO:0048')
        indv_48 = ent.getOWLAPIObj()
        ent2 = self.ont.createNewIndividual('OBTO:0049')
        indv_49 = ent2.getOWLAPIObj()
        ent.addObjectPropertyFact('OBTO:0002', 'OBTO:0049', is_negative=True)

        # Get the total number of initial object property assertion axioms.
        axioms = self.owlont.getAxioms(AxiomType.OBJECT_PROPERTY_ASSERTION)
        init_axiom_cnt = axioms.size()

        # Get the total number of initial negative object property assertion
        # axioms.
        axioms = self.owlont.getAxioms(
            AxiomType.NEGATIVE_OBJECT_PROPERTY_ASSERTION
        )
        init_neg_axiom_cnt = axioms.size()

        # Check the starting state of the ontology by confirming that the
        # inverse property assertions are absent.
        axioms = self.owlont.getObjectPropertyAssertionAxioms(indv_43)
        self.assertEqual(0, axioms.size())
        axioms = self.owlont.getObjectPropertyAssertionAxioms(indv_45)
        self.assertEqual(0, axioms.size())
        axioms = self.owlont.getObjectPropertyAssertionAxioms(indv_47)
        self.assertEqual(0, axioms.size())

        # Generate the inverse object property assertions.
        self.iaa._addInversePropAssertions()

        # Verify that the correct number of new axioms have been created.
        axioms = self.owlont.getAxioms(AxiomType.OBJECT_PROPERTY_ASSERTION)
        new_axiom_cnt = axioms.size()
        self.assertEqual(3, new_axiom_cnt - init_axiom_cnt)

        axioms = self.owlont.getAxioms(
            AxiomType.NEGATIVE_OBJECT_PROPERTY_ASSERTION
        )
        new_neg_axiom_cnt = axioms.size()
        self.assertEqual(1, new_neg_axiom_cnt - init_neg_axiom_cnt)

        # Verify that the inverse property assertions were created.
        axioms = self.owlont.getObjectPropertyAssertionAxioms(indv_43)
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(prop_3))
        self.assertTrue(axiom.getSubject().equals(indv_43))
        self.assertTrue(axiom.getObject().equals(indv_42))

        axioms = self.owlont.getObjectPropertyAssertionAxioms(indv_45)
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(prop_2))
        self.assertTrue(axiom.getSubject().equals(indv_45))
        self.assertTrue(axiom.getObject().equals(indv_44))

        axioms = self.owlont.getObjectPropertyAssertionAxioms(indv_47)
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(prop_4))
        self.assertTrue(axiom.getSubject().equals(indv_47))
        self.assertTrue(axiom.getObject().equals(indv_46))

        # Verify that the inverse negative property assertion was created.
        axioms = self.owlont.getNegativeObjectPropertyAssertionAxioms(indv_49)
        self.assertEqual(1, axioms.size())
        axiom = axioms.iterator().next()
        self.assertTrue(axiom.getProperty().equals(prop_3))
        self.assertTrue(axiom.getSubject().equals(indv_49))
        self.assertTrue(axiom.getObject().equals(indv_48))

    def test_loadExcludedTypes(self):
        exp_iris = {
            'http://purl.obolibrary.org/obo/OBTO_0011',
            'http://purl.obolibrary.org/obo/OBITO_0001',
            'http://www.w3.org/2002/07/owl#Thing',
            'http://purl.obolibrary.org/obo/OBTO_0012'
        }

        exctypes = self.iaa._getExcludedTypesFromFile(
            'test_data/excluded_types.csv'
        )
        exctype_iris = set(
            [classobj.getIRI().toString() for classobj in exctypes]
        )

        self.assertEqual(exp_iris, exctype_iris)

    def test_excludeTypes(self):
        """
        Tests the functionality of specifying classes to exclude from inferred
        class/type assertions.  The tests in this method confirm that 1)
        inferred axioms about excluded classes are deleted; 2) explicit axioms
        about excluded classes are *not* deleted; 3) inferred axioms about
        non-excluded classes are not deleted; and 4) explicit axioms about
        non-excluded classes are not deleted.
        """
        # Create a new class that is a subclass of OBTO:0010 and create an
        # individual of the new class.  This is to test that inferred type
        # assertions that should *not* be excluded are preserved.
        newclass = self.ont.createNewClass('OBTO:0013')
        newclass.addSuperclass('OBTO:0010')
        newindv = self.ont.createNewIndividual('OBTO:8002')
        newindv.addType('OBTO:0013')

        self.iaa.loadExcludedTypes('test_data/excluded_types.csv')

        # Run the reasoner.
        inftypes = ['subclasses', 'types', 'disjoint classes']
        self.iaa.addInferredAxioms(inftypes)
        #self.ont.saveOntology('test_inferred-2.owl')

        # Individual OBTO:8000 should only have OBTO:0011 as its type.
        # (OBTO:0011 is excluded in the CSV file, but in this case the type
        # assertion is not inferred so it should remain.)
        indv = self.ont.getExistingIndividual('OBTO:8000').getOWLAPIObj()
        axioms = self.owlont.getClassAssertionAxioms(indv)
        self.assertEqual(1, axioms.size())
        typeclass = axioms.iterator().next().getClassExpression().asOWLClass()
        self.assertTrue(typeclass.getIRI().equals(
            IRI.create('http://purl.obolibrary.org/obo/OBTO_0011')
        ))

        # Individual OBTO:8001 should only have OBTO:0010 as its type.
        indv = self.ont.getExistingIndividual('OBTO:8001').getOWLAPIObj()
        axioms = self.owlont.getClassAssertionAxioms(indv)
        self.assertEqual(1, axioms.size())
        typeclass = axioms.iterator().next().getClassExpression().asOWLClass()
        self.assertTrue(typeclass.getIRI().equals(
            IRI.create('http://purl.obolibrary.org/obo/OBTO_0010')
        ))

        # Individual OBTO:8002 should have OBTO:0013 (explicit) and OBTO:0010
        # (inferred) as its types.
        expectedIRIs = {
            IRI.create('http://purl.obolibrary.org/obo/OBTO_0010'),
            IRI.create('http://purl.obolibrary.org/obo/OBTO_0013')
        }
        axioms = self.owlont.getClassAssertionAxioms(newindv.getOWLAPIObj())
        self.assertEqual(2, axioms.size())
        typeIRIs = set(
            [ax.getClassExpression().asOWLClass().getIRI() for ax in axioms]
        )
        self.assertEqual(expectedIRIs, typeIRIs)

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

        # Individual 'test individual 2' should only have OBTO_0010 as its
        # type.
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

        # Individual 'test individual 2' should now have OBTO_0010, OBTO_0012,
        # and OBITO_0001 as its types.
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

