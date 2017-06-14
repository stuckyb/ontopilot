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
from ontopilot.documenter import Documenter
from ontopilot.documentation_writers import MarkdownWriter, HTMLWriter
from ontopilot.ontology import Ontology
import unittest
import StringIO
#from testfixtures import LogCapture

# Java imports.


class Test_MarkdownWriter(unittest.TestCase):
    """
    Tests the MarkdownWriter class.  No attempt is made to cover every possible
    input data structure variation, or even most of them.  Instead, it
    basically just confirms that the converter is working and producing correct
    output for a sample input document.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.doc = Documenter(self.ont)

    def test_write(self):
        docspec = """
Test documentation
---
Classes:
    - ID: OBITO:0001
      descendants: 1
"""
        expected = """
# Test documentation

## Classes

* ### imported test class 1
  OBO ID: OBITO:0001  
  IRI: http://purl.obolibrary.org/obo/OBITO_0001

    * ### test class 1
      OBO ID: OBTO:0010  
      IRI: http://purl.obolibrary.org/obo/OBTO_0010

    * ### test class 2
      OBO ID: OBTO:0011  
      IRI: http://purl.obolibrary.org/obo/OBTO_0011

    * ### test class 3
      OBO ID: OBTO:0012  
      IRI: http://purl.obolibrary.org/obo/OBTO_0012


"""

        self.doc.setWriter(MarkdownWriter())

        strbuf = StringIO.StringIO()
        self.doc.document(docspec, strbuf)
        result = strbuf.getvalue()
        strbuf.close()

        self.assertEqual(expected[1:], result)


class Test_HTMLWriter(unittest.TestCase):
    """
    Tests the HTMLWriter class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.doc = Documenter(self.ont)

        self.hw = HTMLWriter()

    def test_getUniqueValue(self):
        coll = ['a', 'b', 'b-1', 'c-']

        testvals = [
            {
                'text': '',
                'expected': '-1'
            },
            {
                'text': 'd',
                'expected': 'd'
            },
            {
                'text': 'a',
                'expected': 'a-1'
            },
            {
                'text': 'b',
                'expected': 'b-2'
            },
            {
                'text': 'c-',
                'expected': 'c--1'
            }
        ]

        for testval in testvals:
            self.assertEqual(
                testval['expected'],
                self.hw._getUniqueValue(testval['text'], coll)
            )

    def test_getIDText(self):
        # String conversion tests.
        testvals = [
            {
                'text': '',
                'expected': '-1'
            },
            {
                'text': '- -- \t\n',
                'expected': '-'
            },
            {
                'text': 'will-not_be-changed',
                'expected': 'will-not_be-changed'
            },
            {
                'text': '(w*&il|}[]l be\tch@anged',
                'expected': 'will-be-changed'
            },
            {
                'text': 'Case-Will-Change',
                'expected': 'case-will-change'
            },
            {
                # Includes a unicode lower-case Greek alpha.
                'text': unicode('unicode: \xce\xb1', 'utf-8'),
                'expected': 'unicode-'
            }
        ]

        for testval in testvals:
            self.assertEqual(
                testval['expected'], self.hw._getIDText(testval['text'], set())
            )

        # Test unique ID generation.
        usedIDs = {
            'ida', 'idb', 'idb-1', 'idc', 'idc-2', 'idd', 'idd-1', 'idd-2'
        }

        testvals = [
            {
                'text': 'ide',
                'expected': 'ide'
            },
            {
                'text': 'ida',
                'expected': 'ida-1'
            },
            {
                'text': 'idb',
                'expected': 'idb-2'
            },
            {
                'text': 'idc',
                'expected': 'idc-1'
            },
            {
                'text': 'idd',
                'expected': 'idd-3'
            }
        ]

        for testval in testvals:
            self.assertEqual(
                testval['expected'],
                self.hw._getIDText(testval['text'], usedIDs)
            )

    def test_write(self):
        pass

