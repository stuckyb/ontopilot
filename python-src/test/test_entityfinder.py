# Copyright (C) 2018 Brian J. Stucky
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
import unittest
import operator
from ontopilot.ontology import Ontology
from ontopilot.entityfinder import EntityFinder
from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import IRI


class TestEntityFinder(unittest.TestCase):
    """
    Tests the EntityFinder class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology-entityfinder.owl')
        self.ef = EntityFinder()

    def test_findEntities(self):
        # Define all test search strings and results.
        PRE = 'http://purl.obolibrary.org/obo/'
        testpairs = [
            {
                'searchstr': 'has object',
                'matches': [
                    (PRE + 'TOEF_0001', 'rdfs:label', 'has object')
                ]
            },
            {
                'searchstr': 'has datum',
                'matches': [
                    (PRE + 'TOEF_0020', 'rdfs:label', 'has datum')
                ]
            },
            {
                'searchstr': 'has annotation',
                'matches': [
                    (PRE + 'TOEF_0030', 'rdfs:label', 'has annotation')
                ]
            },
            {
                'searchstr': 'something else',
                'matches': [
                    (PRE + 'TOEF_0011', 'rdfs:label', 'something else')
                ]
            },
            {
                'searchstr': 'an individual',
                'matches': [
                    (PRE + 'TOEF_8000', 'rdfs:label', 'an individual')
                ]
            },
            # TOEF_0010 has synonyms specified in various ways.
            {
                'searchstr': 'something',
                'matches': [
                    (PRE + 'TOEF_0010', 'rdfs:label', 'something')
                ]
            },
            {
                'searchstr': 'alternative name',
                'matches': [
                    (PRE + 'TOEF_0010', 'rdfs:label', 'alternative name')
                ]
            },
            {
                'searchstr': 'another name',
                'matches': [
                    (PRE + 'TOEF_0010', 'skos:altLabel', 'another name')
                ]
            },
            {
                'searchstr': 'synonymous name',
                'matches': [
                    (PRE + 'TOEF_0010', 'oboInOwl:hasSynonym', 'synonymous name')
                ]
            },
            # The single imported entity.
            {
                'searchstr': 'imported test class 1',
                'matches': [
                    (PRE + 'OBITO_0001', 'rdfs:label', 'imported test class 1')
                ]
            },
            # A search term with no matches that does not correspond with an
            # actual annotation.
            {
                'searchstr': 'invalid',
                'matches': []
            },
            # A search term with no matches that does match the text of a
            # non-relevant annotation.
            {
                'searchstr': 'should be ignored',
                'matches': []
            }
        ]

        # Confirm that no search strings return results prior to loading the
        # ontology entities.
        for testpair in testpairs:
            self.assertEqual([], self.ef.findEntities(testpair['searchstr']))

        self.ef.addOntologyEntities(self.ont)

        # Check all search strings.
        for testpair in testpairs:
            results = self.ef.findEntities(testpair['searchstr'])

            # Convert all of the results _OntologyEntity objects to IRI
            # strings and sort by IRI.
            results = [
                (str(result[0].getIRI()), result[1], result[2]) for result in results
            ]
            results.sort(key=operator.itemgetter(0))

            self.assertEqual(testpair['matches'], results)
