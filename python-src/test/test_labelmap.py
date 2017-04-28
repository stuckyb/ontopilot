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
from ontopilot.labelmap import LabelMap
from ontopilot.labelmap import InvalidLabelError, AmbiguousLabelError
import unittest
from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


class TestLabelMap(unittest.TestCase):
    """
    Tests the LabelMap class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.lm = LabelMap(self.ont)

    def test_makeMap(self):
        """
        Tests that making a label map from an ontology and its imports closure
        works as expected.
        """
        # Define all IRI/label pairings in the main test ontology.
        testpairs = [
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_0001',
                'label': 'test object property 1'
            },
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_0020',
                'label': 'test data property 1'
            },
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_0030',
                'label': 'annotation property 1'
            },
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_0010',
                'label': 'test class 1'
            },
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_0011',
                'label': 'test class 2'
            },
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_0012',
                'label': 'test class 3'
            },
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_8000',
                'label': 'test individual 1'
            },
            {
                'iri': 'http://purl.obolibrary.org/obo/OBTO_8001',
                'label': 'test individual 2'
            }
        ]

        # Check all labels in the main, directly loaded ontology.
        for testpair in testpairs:
            self.assertEqual(
                testpair['iri'], str(self.lm.lookupIRI(testpair['label'])),
            )

        # Check all labels in the imported OWL file.
        self.assertEqual(
            str(self.lm.lookupIRI('imported test class 1')),
            'http://purl.obolibrary.org/obo/OBITO_0001'
        )

    def test_add_lookupIRI(self):
        """
        Tests both add() and lookupIRI().
        """
        # Test basic lookup without a root IRI string.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0001',
            str(self.lm.lookupIRI('test object property 1'))
        )

        # Test lookup of an invalid label.
        with self.assertRaisesRegexp(
            InvalidLabelError,
            'The provided label, "invalid label", does not match'
        ):
            self.lm.lookupIRI('invalid label')

        #
        # Test using a root IRI string to check the value of a retrieved IRI.
        #
        # First use a matching root IRI string.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0001',
            str(self.lm.lookupIRI(
                'test object property 1', 'http://purl.obolibrary.org/obo/OBTO_')
            )
        )

        # Then use an incorrect root IRI string.
        with self.assertRaisesRegexp(
            InvalidLabelError, 'The provided IRI root, .*, does not match'
        ):
            self.lm.lookupIRI(
                'test object property 1',
                'http://purl.obolibrary.org/obo/OBLAH_'
            )

        #
        # Test handling of ambiguous labels.
        #
        # Add an ambiguous label.  This should raise a warning.
        with LogCapture() as lc:
            self.lm.add(
                'test class 1',
                IRI.create('http://purl.obolibrary.org/obo/OBITO_0200')
            )

        # Don't use LogCapture's check() method here because it doesn't support
        # substring matching.
        self.assertTrue(
            'The label "test class 1" is used for more than one IRI in the ontology' in str(lc)
        )

        # Attempt to dereference an ambiguous label.  This should raise an
        # exception.
        with self.assertRaisesRegexp(
            AmbiguousLabelError, 'Attempted to use an ambiguous label'
        ):
            self.lm.lookupIRI('test class 1')

        # Attempt to dereference an ambiguous label with an IRI root string.
        # This should work without error.
        self.assertEqual(
            str(self.lm.lookupIRI('test class 1', 'http://purl.obolibrary.org/obo/OBTO_')),
            'http://purl.obolibrary.org/obo/OBTO_0010'
        )

        # Attempt to dereference an ambiguous label with an IRI root string
        # that is non-unique.  This should raise an exception.
        with self.assertRaisesRegexp(
            AmbiguousLabelError, 'Attempted to use an ambiguous label'
        ):
            self.lm.lookupIRI(
                'test class 1', 'http://purl.obolibrary.org/obo/'
            )

        # Attempt to dereference an ambiguous label with an IRI root string
        # that is invalid.  This should raise an exception.
        with self.assertRaisesRegexp(
            InvalidLabelError, 'The IRI root <.*> did not match any entities'
        ):
            self.lm.lookupIRI(
                'test class 1', 'http://invalid.root/iri/'
            )

    def test_update_notification(self):
        """
        Verifies that LabelMap correctly follows changes to its source
        ontology.
        """
        # The new label should not yet exist.
        with self.assertRaisesRegexp(
            InvalidLabelError, 'The provided label, ".*", does not match'
        ):
            self.lm.lookupIRI('new test class')

        # Create a new class and give it a label.
        newclass = self.ont.createNewClass('OBTO:0013')
        newclass.addLabel('new test class')

        # The LabelMap should automatically have the new label.
        self.assertEqual(
            'http://purl.obolibrary.org/obo/OBTO_0013',
            str(self.lm.lookupIRI('new test class'))
        )

