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
from ontopilot.mshelper import (
    ManchesterSyntaxParserHelper, _BasicShortFormProvider
)
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.model import DataRangeType


class Test_BasicShortFormProvider(unittest.TestCase):
    """
    Tests the _BasicShortFormProvider "private" helper class.
    """
    def setUp(self):
        self.test_ont = Ontology('test_data/ontology.owl')
        self.bsfp = _BasicShortFormProvider()

    def test_getShortForm(self):
        entity = self.test_ont.getExistingClass('OBTO:0010').getOWLAPIObj()

        self.assertEqual('OBTO_0010', self.bsfp.getShortForm(entity))


class TestManchesterSyntaxParserHelper(unittest.TestCase):
    """
    Tests the ManchesterSyntaxParserHelper class.  This also indirectly tests
    the functionality of _MoreAdvancedEntityChecker.
    """
    def setUp(self):
        self.test_ont = Ontology('test_data/ontology.owl')

        self.msph = ManchesterSyntaxParserHelper(self.test_ont)

    def test_parseLiteral(self):
        litval = self.msph.parseLiteral('"test"')
        self.assertTrue(litval.isRDFPlainLiteral())
        self.assertEqual('test', litval.getLiteral())

        litval = self.msph.parseLiteral('"test"^^xsd:string')
        self.assertTrue(litval.getDatatype().isString())
        self.assertEqual('test', litval.getLiteral())

        litval = self.msph.parseLiteral('1')
        self.assertTrue(litval.isInteger())
        self.assertEqual(1, litval.parseInteger())

        litval = self.msph.parseLiteral('"1"^^xsd:float')
        self.assertTrue(litval.isFloat())
        self.assertEqual(1.0, litval.parseFloat())
 
        litval = self.msph.parseLiteral('1.0f')
        self.assertTrue(litval.getDatatype().isFloat())
        self.assertEqual(1.0, litval.parseFloat())

        litval = self.msph.parseLiteral('true')
        self.assertTrue(litval.isBoolean())
        self.assertTrue(litval.parseBoolean())

    def test_parseDataRange(self):
        drange = self.msph.parseDataRange('xsd:integer')
        self.assertTrue(drange.isDatatype())
        self.assertTrue(drange.asOWLDatatype().isInteger())

        drange = self.msph.parseDataRange('xsd:integer[>0]')
        self.assertFalse(drange.isDatatype())
        self.assertEqual(
            DataRangeType.DATATYPE_RESTRICTION, drange.getDataRangeType()
        )

        drange = self.msph.parseDataRange('{1,2,3}')
        self.assertFalse(drange.isDatatype())
        self.assertEqual(
            DataRangeType.DATA_ONE_OF, drange.getDataRangeType()
        )

    def test_parseClassExpressions(self):
        """
        Tests parsing strings that contain MS class expressions.
        """
        # Test strings containing simple, single-class expressions that all
        # refer to the same class.
        test_exps = [
            "'test class 1'",
            "obo:'test class 1'",
            "OBTO:'test class 1'",
            'obo:OBTO_0010',
            'http://purl.obolibrary.org/obo/OBTO_0010',
            '<http://purl.obolibrary.org/obo/OBTO_0010>',
            'OBTO:0010'
        ]
        expIRI = self.test_ont.getExistingClass('OBTO:0010').getIRI()

        for test_exp in test_exps:
            cl_exp = self.msph.parseClassExpression(test_exp)
            # Make sure the returned class expression is correct.
            self.assertFalse(cl_exp.isAnonymous())
            self.assertTrue(cl_exp.asOWLClass().getIRI().equals(expIRI))

        # Test a more complex expression.  In this case, we just verify that
        # the call completes and returns a value.  The check could be more
        # thorough at some point, but that is probably not necessary for now
        # since the correctness of the return value depends mostly on the
        # correctness of the OWL API.
        exps_str = "'test class 1' AND 'imported test class 1'"
        actual = self.msph.parseClassExpression(exps_str)
        self.assertIsNotNone(actual)

