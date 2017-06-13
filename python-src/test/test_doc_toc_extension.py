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
from ontopilot.doc_toc_extension import _ToCGenerator
import unittest
#from testfixtures import LogCapture

# Java imports.


class Test_ToCGenerator(unittest.TestCase):
    """
    Tests the _ToCGenerator class.  The DocToCExtension class doesn't do much
    beyond instantiating a _ToCGenerator instance, so we don't bother with
    formally testing DocToCExtension.
    Testing is currently limited to _getIDText(), which is probably sufficient,
    because the overall functionality is covered in the unit tests for
    HTMLWriter.
    """
    def setUp(self):
        self.tg = _ToCGenerator(None, None, 2)

    def test_headerLevelError(self):
        testvals = ['2', 0, 7]

        for testval in testvals:
            with self.assertRaisesRegexp(
                RuntimeError, 'Invalid HTML header level'
            ):
                _ToCGenerator(None, None, testval)

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
                self.tg._getUniqueValue(testval['text'], coll)
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
                testval['expected'], self.tg._getIDText(testval['text'])
            )

        # Test unique ID generation.
        self.tg.usedIDs.update(
            {'ida', 'idb', 'idb-1', 'idc', 'idc-2', 'idd', 'idd-1', 'idd-2'}
        )

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
                testval['expected'], self.tg._getIDText(testval['text'])
            )

