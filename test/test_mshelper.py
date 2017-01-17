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
from ontobuilder import Ontology
from ontobuilder.mshelper import ManchesterSyntaxParserHelper
import unittest
#from testfixtures import LogCapture

# Java imports.
#from org.semanticweb.owlapi.model import IRI


class TestManchesterSyntaxParserHelper(unittest.TestCase):
    """
    Tests the ManchesterSyntaxParserHelper class.
    """
    def setUp(self):
        self.test_ont = Ontology('test_data/ontology.owl')

        self.msph = ManchesterSyntaxParserHelper(self.test_ont)

    def test_parseClassExpressions(self):
        """
        Tests parsing strings that contain MS class expressions.
        """
        # Test strings containing simple, single-class expressions.
        test_exps = [
            "'test class 1'",
            'obo:OBTO_0010',
            'http://purl.obolibrary.org/obo/OBTO_0010'
        ]
        expIRI = self.test_ont.getExistingClass('OBTO:0010').getIRI()

        for test_exp in test_exps:
            cl_exp = self.msph.parseClassExpression(test_exp)
            self.assertFalse(cl_exp.isAnonymous())
            self.assertTrue(cl_exp.asOWLClass().getIRI().equals(expIRI))

        # Test a more complex expression.  In this case, we just verify that
        # the call completes and returns a value.  The check could be more
        # thorough at some point, but that is probably not necessary for now
        # since the correctness of the return value depends on the OWL API.
        exps_str = "'test class 1' AND 'imported test class 1'"
        actual = self.msph.parseClassExpression(exps_str)
        self.assertIsNotNone(actual)

