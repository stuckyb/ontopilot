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
from ontobuilder.delimstr_parser import DelimStrParser
import unittest

# Java imports.


class Test_DelimtrParser(unittest.TestCase):
    """
    Tests the delimiter-separated string parser.
    """
    def setUp(self):
        self.parser = DelimStrParser(';')

    def test_parseString(self):
        """
        Tests a bunch of strings to verify that different edge cases and
        character combinations all parse correctly.
        """
        testvals = (
            ('', []),
            (' ', []),
            ('   \t   ', []),
            ( """   \t  
\t
   \t """, []),
            (';', []),
            (""";
  \t  \t
;
  ;
\t  
;
   \t""", []),
            (r'\"', ['"']),
            ('test string!!', ['test string!!']),
            (r'test \string\"!!', [r'test \string"!!']),
            (';;multiple string;; ; values;', ['multiple string', 'values']),
            ('""', []),
            ('"test string!!"', ['test string!!']),
            (r'"test \string\"!!"', [r'test \string"!!']),
            ('te"st" "string!!"', ['test string!!']),
            ('a "string; with" delimiters', ['a string; with delimiters']),
            ('a "string; with" ; delimiters', ['a string; with', 'delimiters']),
            (r'"with;;delimiters\"";\""and \" escapes"', ['with;;delimiters"', '"and " escapes']),
            ('"includes\ncarriage";\n;\nret-\nurns', ['includes\ncarriage', 'ret-\nurns']),

            # Also include a variety of test cases for parsing Manchester
            # Syntax class expressions.
            ("'test class 1' AND 'imported test class 1'", ["'test class 1' AND 'imported test class 1'"]),
            # A single expression with multiple lines, extra blank lines,
            # semicolon separators, and white space.
            ("""
;
   'test class 1' AND
 'imported test class 1'    
 
;

\t  

 """, ["""'test class 1' AND
 'imported test class 1'"""]),
            # Multiple expressions with multiple lines, extra blank lines,
            # semicolon separators, and white space.
            ("""
;
   'test class 1' AND
 'imported test class 1'    
 
;

\t  
'test class 1'
;
 """, ["""'test class 1' AND
 'imported test class 1'""", "'test class 1'"])
        )

        for testval in testvals:
            self.assertEqual(
                testval[1], self.parser.parseString(testval[0])
            )

    def test_parseError(self):
        """
        Tests that parse errors are detected and reported.
        """
        # Verify that unbalanced quotes are correctly detected.
        with self.assertRaisesRegexp(RuntimeError, 'Closing quote missing in input string'):
            self.parser.parseString('"unbalanced"; "quotes')

