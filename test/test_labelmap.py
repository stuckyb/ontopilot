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
from ontobuilder import LabelMap, Ontology
import unittest
from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


class TestLabelMap(unittest.TestCase):
    """
    Tests the LabelMap class.
    """
    def setUp(self):
        self.lm = Ontology('test_data/ontology.owl').labelmap

    def test_makeMap(self):
        """
        Tests that making a label map from an ontology and its imports closure
        works as expected.
        """
        # Check all labels in the directly loaded ontology.
        self.assertEqual(str(self.lm.lookupIRI('test object property 1')), 'http://purl.obolibrary.org/obo/OBTO_0001')
        self.assertEqual(str(self.lm.lookupIRI('test class 1')), 'http://purl.obolibrary.org/obo/OBTO_0010')

        # Check all labels in the imported OWL file.
        self.assertEqual(str(self.lm.lookupIRI('imported test class 1')), 'http://purl.obolibrary.org/obo/OBITO_0001')

    def test_ambiguous(self):
        """
        Tests handling of ambiguous labels.
        """
        # Add an ambiguous label.  This should raise a warning.
        with LogCapture() as lc:
            self.lm.add('test class 1', IRI.create('http://purl.obolibrary.org/obo/OBTO_0200'))

        # Don't use LogCapture's check() method here becuase it doesn't support
        # substring matching.
        self.assertTrue('The label "test class 1" is used for more than one IRI in the ontology' in str(lc))

        # Attempt to dereference an ambiguous label.  This should raise an
        # exception.
        with self.assertRaisesRegexp(RuntimeError, 'Attempted to use an ambiguous label'):
            self.lm.lookupIRI('test class 1')

