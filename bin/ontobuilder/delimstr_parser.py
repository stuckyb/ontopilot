

class DelimStrParser:
    r"""
    Parses strings that optionally contain delimiter-separated string values.
    The strings are parsed according to the simple grammar below.  Two rules
    not captured by the grammar are: 1) Quoted components must begin and end
    with the same quote character; and 2) Inside a quoted components,
    alternative quote characters can be used unescaped.

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

