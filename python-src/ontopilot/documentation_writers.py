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

#
# Provides writer classes that convert abstract _Document data structures to
# documentation files.  Each writer class must provide a single public method,
# called write(), that accepts a _Document object and a writable file object as
# its arguments.
#

# Python imports.
from __future__ import unicode_literals
import StringIO
import markdown
from ontopilot import logger

# Java imports.


class MarkdownWriter:
    def __init__(self):
        pass

    def _writeNode(self, node, fileout, indent_level):
        nname = node.getName()
        indentstr = '    ' * indent_level

        fileout.write('{0}* ### {1}\n'.format(indentstr, nname))

        if node.entOBO_ID != nname:
            fileout.write(
                '{0}* OBO ID: {1}\n'.format(indentstr, node.entOBO_ID)
            )
        if node.entIRI != nname:
            fileout.write('{0}* IRI: {1}\n'.format(indentstr, node.entIRI))

        if node.entdef != '':
            fileout.write(
                '{0}* Definition: {1}\n'.format(indentstr, node.entdef)
            )

        for childnode in node.children:
            self._writeNode(childnode, fileout, indent_level + 1)

    def _writeSection(self, section, fileout):
        if section.title != '':
            fileout.write('## {0}\n\n'.format(section.title))

        for node in section.docnodes:
            self._writeNode(node, fileout, 0)

        fileout.write('\n\n')
        
    def write(self, document, fileout):
        """
        Generates a markdown representation of a _Document data structure.

        document: A _Document instance.
        fileout: A writable file object.
        """
        if document.title != '':
            fileout.write('# {0}\n\n'.format(document.title))

        for section in document.sections:
            self._writeSection(section, fileout)


class HTMLWriter:
    def __init__(self):
        pass

    def write(self, document, fileout):
        """
        Generates an XHTML5 representation of a _Document data structure.

        document: A _Document instance.
        fileout: A writable file object.
        """
        # Use MarkdownWriter to get the Markdown representation of the
        # document, then convert that to HTML.
        mdwriter = MarkdownWriter()
        strbuf = StringIO.StringIO()
        mdwriter.write(document, strbuf)
        mdtext = strbuf.getvalue()
        strbuf.close()

        header = """<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
    <head>
        <meta charset="utf-8" />
        <title>{0}</title>
        <!--link rel="stylesheet" type="text/css" href="style.css" /-->
    </head>
    <body>
"""

        footer = '\n    </body>\n</html>'

        htmltext = markdown.markdown(mdtext, output_format='xhtml5')

        fileout.write(header.format(document.title))
        fileout.write(htmltext)
        fileout.write(footer)

