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
from ontopilot.obohelper import isOboID, termIRIToOboID, oboIDToIRI
from ontopilot.obohelper import getIRIForOboPrefix, OBO_BASE_IRI
from ontopilot.obohelper import OBOIdentiferError
import unittest

# Java imports.


# Define test values that are valid OBO IDs.
valid_id_testvals = [
    'a:0',
    'abcABC:0123',
    'a_b:0',
    'ABCabc_defDEF:01234'
]

# Define test values that are invalid OBO IDs.
invalid_id_testvals = [
    '',
    'a',
    ':',
    '0',
    'a:',
    ':0',
    'a_:0',
    'a_b_:0',
    'a_b_c:0',
    'a_b:0123 a'
]

# Define test values that map valid OBO IDs to valid OBO Foundry IRIs.
id_iri_testvals = [
    {'id': 'a:0', 'iri': 'a_0'},
    {'id': 'abcABC:0123', 'iri': 'abcABC_0123'},
    {'id': 'a_b:0', 'iri': 'a_b_0'},
    {'id': 'ABCabc_defDEF:01234', 'iri': 'ABCabc_defDEF_01234'},
]

# Add the OBO base IRI to each test IRI string.
for testval in id_iri_testvals:
    testval['iri'] = OBO_BASE_IRI + testval['iri']


class TestOboHelper(unittest.TestCase):
    """
    Tests the functions in the obohelper module.
    """
    def setUp(self):
        pass

    def test_isOboID(self):
        """
        Tests that various OBO IDs are recognized and that invalid OBO IDs are
        rejected, with valid OBO IDs interpreted as described at
        http://www.obofoundry.org/id-policy.html.
        """
        for testval in valid_id_testvals:
            self.assertTrue(isOboID(testval))

        for testval in invalid_id_testvals:
            self.assertFalse(isOboID(testval))

    def test_termIRIToOboID(self):
        for testval in id_iri_testvals:
            self.assertEqual(testval['id'], termIRIToOboID(testval['iri']))

        # Define test values with invalid OBO IRIs.
        testvals = [
            '',
            'a_0',
            'http://some.other/domain/a_0',
            OBO_BASE_IRI,
            OBO_BASE_IRI + 'a',
            OBO_BASE_IRI + '0',
            OBO_BASE_IRI + 'a:0',
            OBO_BASE_IRI + 'a_b:0',
            OBO_BASE_IRI + 'abc_0123a'
        ]

        for testval in testvals:
            with self.assertRaisesRegexp(
                OBOIdentiferError, 'is not an OBO Foundry-compliant IRI'
            ):
                termIRIToOboID(testval)

    def test_oboIDToIRI(self):
        # Test valid OBO IDs.
        for testval in id_iri_testvals:
            self.assertEqual(
                testval['iri'], oboIDToIRI(testval['id']).toString()
            )

        # Test invalid OBO IDs.
        for testval in invalid_id_testvals:
            with self.assertRaisesRegexp(
                OBOIdentiferError, 'is not a valid OBO ID'
            ):
                oboIDToIRI(testval)

    def test_getIRIForOboPrefix(self):
        # Define valid test values.
        testvals = [
            {'prefix': 'a', 'iri': OBO_BASE_IRI + 'a'},
            {'prefix': 'ABCabc', 'iri': OBO_BASE_IRI + 'ABCabc'},
            {'prefix': 'abc_def', 'iri': OBO_BASE_IRI + 'abc_def'},
        ]

        for testval in testvals:
            self.assertEqual(
                testval['iri'], getIRIForOboPrefix(testval['prefix'])
            )

        # Define invalid test values.
        testvals = [
            '',
            '0',
            'a:0',
            'a_',
            'a_b_c'
        ]

        for testval in testvals:
            with self.assertRaisesRegexp(
                OBOIdentiferError, 'is not a valid OBO prefix'
            ):
                getIRIForOboPrefix(testval)

