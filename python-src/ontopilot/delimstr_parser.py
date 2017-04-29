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
from __future__ import unicode_literals


class DelimStrParser:
    r"""
    Parses strings that optionally contain delimiter-separated string values.
    The strings are parsed according to the simple grammar below.  Two rules
    not captured by the grammar are: 1) Quoted components must begin and end
    with the same quote character; and 2) Inside quoted components, alternative
    quote characters can be used unescaped.

    str_list => [string {delimchar string}]
    string => strpart {strpart}
    strpart => unquoted_str | quoted_str
    unquoted_str => {nonreserved | escaped_quote | escaped_delim}+
    quoted_str => quotechar {nonquote | escaped_quote}+ quotechar
    escaped_quote = '\' quotechar
    escaped_delim = '\' delimchar
    char = all characters
    delimchar = delimiter characters
    quotechar = quote characters
    nonquote = char - quotechar
    nonreserved = nonquote - delimchar

    In words, input strings are expected to contain 0 or more characters, with
    some delimiter or delimiters (comma by default) separating different string
    values within the input string.  Delimiters inside quotes are ignored.
    Escaped delimiters will be replaced only if they are not inside of quotes.

    In addition, leading and trailing whitespace is removed from all strings,
    and empty strings are never returned.  This means that, effectively, runs
    of delimiter characters are merged into a single delimiter.
    """
    def __init__(self, delimchars=',', quotechars='"'):
        self.delimchars = delimchars
        self.quotechars = quotechars

    def parseString(self, strval):
        """
        Parses a single input string and returns a list containing the strings
        parsed from the input.
        """
        strlist = []

        currstrval = ''
        prevchar = ''
        inquotes = False
        open_quotechar = ''
        for char in strval:
            if (char in self.quotechars) and (prevchar != '\\'):
                if inquotes and (char == open_quotechar):
                    # This quote character is not escaped, so it closes the
                    # quoted portion.
                    inquotes = False
                elif not(inquotes):
                    inquotes = True
                    open_quotechar = char

                currstrval += char
            elif char in self.delimchars:
                if inquotes:
                    currstrval += char
                elif prevchar == '\\':
                    # We have an escaped delimiter, so remove the escape
                    # character from the output string and replace it with the
                    # delimiter.
                    currstrval = currstrval[:len(currstrval) - 1] + char
                else:
                    if currstrval.strip() != '':
                        strlist.append(currstrval.strip())
                        currstrval = ''
            else:
                currstrval += char

            prevchar = char

        if inquotes:
            raise RuntimeError(
                'String parsing error: Closing quote missing in input string "'
                + strval + '".'
            )

        if currstrval.strip() != '':
            strlist.append(currstrval.strip())

        return strlist

    def unquoteStr(self, strval):
        """
        Removes enclosing quotes from a string.  Any escaped quote characters
        inside the string will be replaced with their non-escaped equivalent.
        If the *entire* string is not enclosed in quotes, the string is
        returned unaltered.  That is, a string is only considered to be quoted
        if the first and last character are a matching quote character.
        """
        if len(strval) < 2:
            return strval

        if (strval[0] != strval[-1]) or (strval[0] not in self.quotechars):
            return strval

        # If the end quote is an escaped quote character, then the string is
        # not actually quoted.
        if strval[-2] == '\\':
            return strval

        # Replace escaped quote characters.
        newstrval = strval.replace('\\' + strval[0], strval[0])

        return newstrval[1:-1]

