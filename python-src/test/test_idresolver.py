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
from ontopilot.idresolver import IDResolver
from ontopilot.labelmap import InvalidLabelError, AmbiguousLabelError
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


class TestIDResolver(unittest.TestCase):
    """
    Tests the IDResolver class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.ir = IDResolver(self.ont)

    def test_isLabel(self):
        # Define strings that should be recognized as labels.
        testvals = [
            "'a'",
            "'0'",
            "'abc def '",
            "a:'b'",
            "Ab_cD:'efg :hij'"
        ]

        for testval in testvals:
            self.assertTrue(self.ir._isLabel(testval))

        # Define strings that should *not* be recognized as labels.
        testvals = [
            "",
            "'",
            "''",
            '"a"',
            "a'bc'",
            "a_:'bc'",
            "a:''"
        ]

        for testval in testvals:
            self.assertFalse(self.ir._isLabel(testval))

    def test_resolveLabel(self):
        # Test a plain label with no prefix.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0010',
            str(self.ir.resolveLabel("'test class 1'"))
        )

        # Test a label that should resolve with the prefix interpreted as an
        # OBO prefix, but not an IRI prefix.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0010',
            str(self.ir.resolveLabel("OBTO:'test class 1'"))
        )

        # Test a label that should resolve with the prefix interpreted as an
        # IRI prefix, but not an OBO prefix.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0010',
            str(self.ir.resolveLabel("obo:'test class 1'"))
        )

        # Define a new IRI prefix for the OBTO root.
        owlont = self.ont.getOWLOntology()
        ontman = self.ont.getOntologyManager()
        prefix_df = ontman.getOntologyFormat(owlont).asPrefixOWLOntologyFormat()
        prefix_df.setPrefix('OBTO:', 'http://purl.obolibrary.org/obo/OBTO')

        # Test a label that should resolve with the prefix interpreted as
        # *either* an OBO prefix or an IRI prefix.  This should still work with
        # error, though, because the resolved IRIs should be identical.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0010',
            str(self.ir.resolveLabel("OBTO:'test class 1'"))
        )

        # Define an IRI prefix, "OBITO:", that resolves to the OBTO root.
        prefix_df.setPrefix('OBITO:', 'http://purl.obolibrary.org/obo/OBTO')

        # Define a new class in the OBTO namespace with a label that collides
        # with an existing class in the OBITO namespace.
        newclass = self.ont.createNewClass('OBTO:0013')
        newclass.addLabel('imported test class 1')

        # Test a label that should resolve with the prefix interpreted as
        # either an OBO prefix or an IRI prefix, but for which the resulting
        # full IRIs should *not* be the same.
        with self.assertRaisesRegexp(
            AmbiguousLabelError, 'Attempted to use an ambiguous label'
        ):
            self.ir.resolveLabel("OBITO:'imported test class 1'")

        # Test an invalid label.
        with self.assertRaisesRegexp(
            InvalidLabelError, 'The provided label, ".*", does not match'
        ):
            self.ir.resolveLabel("OBITO:'invalid label'")

    def test_expandIRI(self):
        expIRI = IRI.create('http://www.w3.org/2000/01/rdf-schema#label')

        # Test full IRIs, prefix IRIs, and IRI objects.
        testvals = [
            'http://www.w3.org/2000/01/rdf-schema#label',
            'rdfs:label',
            IRI.create('http://www.w3.org/2000/01/rdf-schema#label')
        ]

        for testval in testvals:
            self.assertTrue(
                expIRI.equals(self.ir.expandIRI(testval))
            )

        # Also test a relative IRI.
        expIRI = IRI.create(
            'https://github.com/stuckyb/ontopilot/raw/master/python-src/test/test_data/ontology.owl#blah'
        )
        self.assertTrue(
            expIRI.equals(self.ir.expandIRI('blah'))
        )

        # Make sure invalid IRI strings are detected.
        with self.assertRaisesRegexp(RuntimeError, 'Invalid IRI string'):
            self.ir.expandIRI('BL\nAH')

    def test_resolveIdentifier(self):
        expIRI = IRI.create('http://purl.obolibrary.org/obo/OBTO_0001')
        
        # Test identifier inputs that include: plain label, OBO prefix label,
        # IRI prefix label, full IRI string, prefix IRI string, OBO ID, and OWL
        # API IRI object.
        testvals = [
            "'test object property 1'",
            "OBTO:'test object property 1'",
            "obo:'test object property 1'",
            'http://purl.obolibrary.org/obo/OBTO_0001',
            'obo:OBTO_0001',
            'OBTO:0001',
            IRI.create('http://purl.obolibrary.org/obo/OBTO_0001')
        ]

        for testval in testvals:
            self.assertTrue(
                expIRI.equals(self.ir.resolveIdentifier(testval))
            )

    def test_resolveNonlabelIdentifier(self):
        # Test that a non-label identifier resolves as expected.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0001',
            str(self.ir.resolveNonlabelIdentifier('obo:OBTO_0001'))
        )

        # Test that an OWL API object works correctly.
        iriobj = IRI.create('http://purl.obolibrary.org/obo/OBTO_0001')
        self.assertEqual(
            str(iriobj), str(self.ir.resolveNonlabelIdentifier(iriobj))
        )

        # Test that a label throws an exception.
        with self.assertRaisesRegexp(RuntimeError, 'labels are not allowed'):
            self.ir.resolveNonlabelIdentifier("obo:'test object property 1'")

