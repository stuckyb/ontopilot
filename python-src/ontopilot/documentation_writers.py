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
import re
from ontopilot import logger

# Java imports.


class MarkdownWriter:
    def __init__(self):
        pass

    def _writeNodeList(self, nodelist, fileout, indent_level):
        for node in nodelist:
            nname = node.getName()
            indentstr = '    ' * indent_level
    
            fileout.write('{0}* ### {1}\n'.format(indentstr, nname))
    
            if node.entOBO_ID != nname and node.entOBO_ID != '':
                fileout.write(
                    '{0}  OBO ID: {1}  \n'.format(indentstr, node.entOBO_ID)
                )

            fileout.write('{0}  IRI: {1}'.format(indentstr, node.entIRI))
    
            if node.entdef != '':
                fileout.write(
                    '  \n{0}  Definition: {1}\n\n'.format(indentstr, node.entdef)
                )
            else:
                fileout.write('\n\n')
    
            if len(node.children) > 0:
                self._writeNodeList(node.children, fileout, indent_level + 1)

    def _writeSection(self, section, fileout):
        if section.title != '':
            fileout.write('## {0}\n\n'.format(section.title))

        if len(section.docnodes) > 0:
            self._writeNodeList(section.docnodes, fileout, 0)

        fileout.write('\n')
        
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
    def __init__(self, include_ToC=True):
        """
        include_ToC (boolean): Whether to generate a table of contents for the
            documentation.
        """
        self.include_ToC = include_ToC

    def _getIDText(self, text, usedIDs):
        """
        Generates ID attribute text from the raw inner text of an HTML header.
        The returned text should be suitable for use in URLs.
        """
        text = text.lower()

        # Encode the string as 8-bit ASCII text, which will eliminate any
        # unicode code points that might cause problems in URL strings.
        text = text.encode('ascii', 'ignore').decode('ascii')

        # Replace all runs of one or more whitespace characters (or
        # hyphens) with single hyphens.
        text = re.sub('[-\s]+', '-', text)
        
        # Eliminate all characters that are not alphanumeric,
        # underscore, or a hyphen.
        basetext = re.sub('[^\w-]', '', text)

        idtext = self._getUniqueValue(basetext, usedIDs)

        usedIDs.add(idtext)

        return idtext

    def _getUniqueValue(self, strval, collection):
        """
        Given a string value and a collection that supports the "in" operator,
        returns a derivative of strval (which might be unchanged) that is not
        already in the collection.  The returned string is guaranteed to be
        non-empty.
        """
        finalstr = strval
        counter = 1
        while finalstr in collection or finalstr == '':
            finalstr = strval + '-{0}'.format(counter)
            counter += 1

        return finalstr

    def _assignHeaderIDsToNodeList(self, nodelist, usedIDs):
        for node in nodelist:
            nname = node.getName()

            node.custom_id = self._getIDText(nname, usedIDs)

            self._assignHeaderIDsToNodeList(node.children, usedIDs)

    def _assignHeaderIDs(self, document):
        usedIDs = set()

        for section in document.sections:
            section.custom_id = self._getIDText(section.title, usedIDs)

            self._assignHeaderIDsToNodeList(section.docnodes, usedIDs)

    def _writeToCNodeList(self, nodelist, fileout, indent_level):
        indentstr = '    ' * indent_level

        fileout.write('{0}<ul>\n'.format(indentstr))

        for node in nodelist:
            nname = node.getName()
    
            fileout.write('{0}<li><a href="#{1}">{2}</a>'.format(
                indentstr, node.custom_id, nname
            ))
        
            if len(node.children) > 0:
                fileout.write('\n')

                self._writeToCNodeList(
                    node.children, fileout, indent_level + 1
                )

                fileout.write('{0}</li>\n'.format(indentstr))
            else:
                fileout.write('</li>\n')

        fileout.write('{0}</ul>\n'.format(indentstr))

    def _writeToC(self, document, fileout):
        fileout.write('<div class="toc">\n<ul>\n')

        for section in document.sections:
            fileout.write('<li><a href="#{0}">{1}</a>\n'.format(
                section.custom_id, section.title
            ))

            if len(section.docnodes) > 0:
                self._writeToCNodeList(section.docnodes, fileout, 1)

            fileout.write('</li>\n')

        fileout.write('</ul>\n</div>\n\n')

    def _writeNodeList(self, nodelist, fileout, indent_level):
        indentstr = '    ' * indent_level
        subindentstr = '    ' * (indent_level + 1)

        fileout.write('{0}<ul>\n'.format(indentstr))

        for node in nodelist:
            nname = node.getName()
    
            fileout.write('{0}<li>\n'.format(indentstr))
            fileout.write('{0}<h3 id="{1}">{2}</h3>\n'.format(
                subindentstr, node.custom_id, nname
            ))
    
            if node.entOBO_ID != nname and node.entOBO_ID != '':
                fileout.write('{0}<p>OBO ID: {1}</p>\n'.format(
                        subindentstr, node.entOBO_ID
                ))

            fileout.write('{0}<p>IRI: {1}</p>\n'.format(
                subindentstr, node.entIRI
            ))

            if node.entdef != '':
                fileout.write('{0}<p>Definition: {1}</p>\n'.format(
                        subindentstr, node.entdef
                ))
    
            if len(node.children) > 0:
                self._writeNodeList(node.children, fileout, indent_level + 1)

            fileout.write('{0}</li>\n'.format(indentstr))

        fileout.write('{0}</ul>\n'.format(indentstr))

    def _writeSection(self, section, fileout):
        if section.title != '':
            fileout.write('<h2 id="{0}">{1}</h2>\n\n'.format(
                section.custom_id, section.title
            ))

        if len(section.docnodes) > 0:
            self._writeNodeList(section.docnodes, fileout, 0)

        fileout.write('\n')
        
    def write(self, document, fileout):
        """
        Generates an XHTML5 representation of a _Document data structure.

        document: A _Document instance.
        fileout: A writable file object.
        """
        header = """<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8" />
    <title>{0}</title>
    <link rel="stylesheet" type="text/css" href="documentation_styles.css" />
</head>
<body>
"""

        footer = '</body>\n</html>'

        self._assignHeaderIDs(document)

        fileout.write(header.format(document.title))

        if document.title != '':
            fileout.write('<h1>{0}</h1>\n\n'.format(document.title))

        if self.include_ToC:
            self._writeToC(document, fileout)

        for section in document.sections:
            self._writeSection(section, fileout)

        fileout.write(footer)

