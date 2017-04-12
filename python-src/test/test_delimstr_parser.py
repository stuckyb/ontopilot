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
from ontopilot.delimstr_parser import DelimStrParser
import unittest

# Java imports.


class Test_DelimtrParser(unittest.TestCase):
    """
    Tests the delimiter-separated string parser.
    """
    def setUp(self):
        # If we define custom failure messages, append them to the end of the
        # default failure message.
        self.longMessage = True

    def test_parseString(self):
        """
        Tests a bunch of strings to verify that different edge cases and
        character combinations all parse correctly.
        """
        parser = DelimStrParser(delimchars=';', quotechars='"')

        testvals = (
            ('', []),
            (' ', []),
            ('   \t   ', []),
            ('   \t  \n\t\n   \t ', []),
            (';', []),
            ('\;', [';']),
            (';\n  \t  \t\n;\n  ;\n\t  \n;\n   \t', []),
            (r'\"', [r'\"']),
            ('test string!!', ['test string!!']),
            (r'test \string\"!!', [r'test \string\"!!']),
            (';;multiple string;; ; values;', ['multiple string', 'values']),
            ('"test string!!"', ['"test string!!"']),
            (r'"test \string\"!!"', [r'"test \string\"!!"']),
            ('a "string; with" delimiters', ['a "string; with" delimiters']),
            ('a "string; with" ; delimiters', ['a "string; with"', 'delimiters']),
            (r'"with; delimiters"; and \; escapes', ['"with; delimiters"', 'and ; escapes']),
            ('"includes;\ncarriage";\n;\nret-\nurns', ['"includes;\ncarriage"', 'ret-\nurns']),

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
                testval[1], parser.parseString(testval[0]),
                msg='Input string: "{0}"'.format(testval[0])
            )

        # Test multiple delimiter characters and multiple quote characters.
        parser = DelimStrParser(delimchars=',;', quotechars='\'"')

        new_testvals = (
            # Test values for mixed delimiters.
            (',;', []),
            (', ;; ,; ,,', []),
            ('different; delimiter, chars', ['different', 'delimiter', 'chars']),
            ('different\;\, delimiter\, chars', ['different;, delimiter, chars']),
            ('"different;, delimiter,"; chars', ['"different;, delimiter,"', 'chars']),

            # Test values for mixed quote characters.
            ('";", \',\'', ['";"', "','"]),
            ('"quotes \';inside\'"', ['"quotes \';inside\'"']),
            ("'quotes \";inside'", ["'quotes \";inside'"]),
            ('"in,; quote", \'in;quote, 2\'', ['"in,; quote"', "'in;quote, 2'"]),
            ('"\\""; \'\\\'\'', ['"\\""', "'\\\''"])
        )

        testvals = testvals + new_testvals
        for testval in testvals:
            self.assertEqual(
                testval[1], parser.parseString(testval[0]),
                msg='Input string: "{0}"'.format(testval[0])
            )

        # Test that the parser works as expected if we use whitespace
        # characters as the delimiters.
        parser = DelimStrParser(delimchars=' \t', quotechars='\'"')

        testvals = (
            ('', []),
            ('  \t', []),
            ('two strings', ['two', 'strings']),
            ('two  \tstrings', ['two', 'strings']),
            ('"one  \tstring"', ['"one  \tstring"'])
        )

        for testval in testvals:
            self.assertEqual(
                testval[1], parser.parseString(testval[0]),
                msg='Input string: "{0}"'.format(testval[0])
            )

    def test_parseError(self):
        """
        Tests that parse errors are detected and reported.
        """
        parser = DelimStrParser(delimchars=';', quotechars='\'"')

        # Define a set of test values that all contain unbalanced quotes.
        testvals = [
            '"',
            "'",
            '"unbalanced',
            "unbalanced'",
            '"\'',
            "'\"",
            '"unbalanced\'',
            "'unbalanced\""
        ]

        for testval in testvals:
            with self.assertRaisesRegexp(
                RuntimeError, 'Closing quote missing in input string'
            ):
                parser.parseString(testval)

    def test_unquoteStr(self):
        parser = DelimStrParser(delimchars=';', quotechars='\'"')

        # Define a set of test values as tuples of (inputstr, resultstr).
        testvals = [
            ('', ''),
            ('"', '"'),
            ('""', ''),
            (r'\"', r'\"'),
            (r'"\"', r'"\"'),
            (r'"\""', '"'),
            ('"\'"', "'"),
            ("'\"'", '"'),
            (r'"\"test\" val"', '"test" val'),
            ('"test" val', '"test" val')
        ]

        for inputstr, resultstr in testvals:
            self.assertEqual(
                resultstr, parser.unquoteStr(inputstr),
                msg='Input string: "{0}"'.format(inputstr)
            )

