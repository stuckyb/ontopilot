
#
# Provides a simple parser for strings that contain comma-separated string
# values.  Supports quoted strings, escaped quote characters, and line returns
# inside component strings.
#


class CSStrParser:
    r"""
    Parses strings that optionally contain comma-separated string values.  The
    strings are parsed according to the simple grammar below.

    str_list => string {',' string}
    string => strpart {strpart}
    strpart => (char - '"' - ',' | '\"') {char - ',' - '"' | '\"'}
               | '"' {char - '"' | '\"'} '"'
    char = all characters

    In words, input strings are expected to contain 0 or more characters, with
    commas separating different string values within the input string.
    Component strings can be quoted with double quotes if they contain commas,
    and literal double quote characters are escaped with a backslash.

    In addition, leading and trailing whitespace is removed from all strings,
    and empty strings are never returned.
    """
    def __init__(self):
        pass

    def parseString(self, strval):
        """
        Parses a single input string and returns a list containing the strings
        parsed from the input.
        """
        strlist = []

        currstrval = ''
        prevchar = ''
        inquotes = False
        for char in strval:
            if char == '"':
                if prevchar == '\\':
                    # We have an escaped quote, so remove the escape character
                    # from the output string and replace it with the quote.
                    currstrval = currstrval[:len(currstrval) - 1] + '"'
                elif inquotes:
                    inquotes = False
                else:
                    inquotes = True
            elif char == ',':
                if inquotes:
                    currstrval += char
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

