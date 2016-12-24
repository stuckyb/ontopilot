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
        test_ont = Ontology('test_data/ontology.owl')

        self.msph = ManchesterSyntaxParserHelper(test_ont)

    def _checkMultiExpStr(self, exps_str, expected):
        """
        Checks the result of parsing a string that potentially contains one or
        more MS class expressions.  This method is used by
        test_splitClassExpressions().
        """
        actual = self.msph._splitClassExpressions(exps_str)

        self.assertEqual(len(actual), len(expected))
        for cnt in range(len(expected)):
            self.assertEqual(actual[cnt], expected[cnt])

    def test_splitClassExpressions(self):
        """
        Tests splitting strings that contain multiple MS class expressions.
        """
        # Test an empty string.
        exps_str = ""
        expected = []
        self._checkMultiExpStr(exps_str, expected)

        # Test a string with only whitespace.
        exps_str = "   \t  "
        expected = []
        self._checkMultiExpStr(exps_str, expected)

        # Test a string with multiple lines of only whitespace.
        exps_str = """   \t  
\t
   \t 
"""
        expected = []
        self._checkMultiExpStr(exps_str, expected)

        # Test a string with only a semicolon (the MS class expression
        # separator character).
        exps_str = ";"
        expected = []
        self._checkMultiExpStr(exps_str, expected)

        # Test a string with multiple lines, semicolon separators, and
        # whitespace.
        exps_str = """;
  \t  \t
;
  ;
\t  
;
   \t
"""
        expected = []
        self._checkMultiExpStr(exps_str, expected)

        # Test a string containing a single expression.
        exps_str = "'test class 1' AND 'imported test class 1'"
        expected = [
                "'test class 1' AND 'imported test class 1'"
        ]
        self._checkMultiExpStr(exps_str, expected)

        # Test a string containing a single expression with multiple lines,
        # extra blank lines, semicolon separators, and white space.
        exps_str = """
;
   'test class 1' AND
 'imported test class 1'    
 
;

\t  

 """
        expected = [
            """'test class 1' AND
 'imported test class 1'"""
        ]
        self._checkMultiExpStr(exps_str, expected)

        # Test a string containing multiple expressions with multiple lines,
        # extra blank lines, semicolon separators, and white space.
        exps_str = """
;
   'test class 1' AND
 'imported test class 1'    
 
;

\t  
'test class 1'
;
 """
        expected = [
            """'test class 1' AND
 'imported test class 1'""",
            """'test class 1'"""
        ]
        self._checkMultiExpStr(exps_str, expected)

    def test_parseClassExpressions(self):
        """
        Tests parsing strings that contain multiple MS class expressions.  The
        tests here are currently not very thorough in that they do not actually
        test the values of the returned OWLClassExpression objects.  This is
        probably reasonable, though, because the correctness of the returned
        OWLClassExpression objects depends on the OWLAPI implementation.
        """
        # Test a string containing a single expression.
        exps_str = "'test class 1' AND 'imported test class 1'"
        actual = self.msph.parseClassExpressions(exps_str)
        self.assertEqual(len(actual), 1)

        # Test a string containing multiple expressions.
        exps_str = """'test class 1' AND
'imported test class 1'    
;
'test class 1'
 """
        actual = self.msph.parseClassExpressions(exps_str)
        self.assertEqual(len(actual), 2)

