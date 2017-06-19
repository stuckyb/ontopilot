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
# Provides writer classes that convert abstract Document data structures to
# documentation files.  Each writer class must provide a single public method,
# called write(), that accepts a Document object and a writable file object as
# its arguments.
#

# Python imports.
from __future__ import unicode_literals
import codecs
import re
from xml.etree import ElementTree as ET
import markdown
from doc_document import MarkdownSection, EntitiesSection


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
        if isinstance(section, MarkdownSection):
            fileout.write(section.content)
        else:
            if len(section.docnodes) > 0:
                self._writeNodeList(section.docnodes, fileout, 0)
    
            fileout.write('\n')
        
    def write(self, document, fileout):
        """
        Generates a markdown representation of a Document data structure.

        document: A Document instance.
        fileout: A writable file object.
        """
        for section in document.sections:
            self._writeSection(section, fileout)


class _HTMLSectionDetails:
    """
    A data structure used by HTMLWriter that stores a pre-rendered HTML version
    of a Markdown section and a list of header texts and header IDs from the
    section.
    """
    def __init__(self):
        # For pre-rendered HTML text.
        self.htmltext = ''

        # A list of (header_text, header_ID) pairs.
        self.headers = []


class HTMLWriter:
    def __init__(self, include_ToC=True):
        """
        include_ToC (boolean): Whether to generate a table of contents for the
            documentation.
        """
        self.include_ToC = include_ToC

        # A list of _HTMLSectionDetails objects.
        self.html_sds = []

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

    def _assignHeaderIDsToMarkdown(self, mdtext, usedIDs):
        """
        Assigns header IDs to a Markdown document section.  Returns an
        _HTMLSectionDetails object that contain the resulting HTML with ID
        attributes and a list of header texts and IDs for the Markdown text.
        """
        html_sd = _HTMLSectionDetails()
        html_sd.htmltext = ''

        # Convert the Markdown text to unicode, if needed (assuming UTF-8).
        if isinstance(mdtext, str):
            u_mdtext = mdtext.decode('utf-8')
        else:
            u_mdtext = mdtext

        # Convert the Markdown to HTML and parse it to a document tree.
        htmltxt = markdown.markdown(u_mdtext, output_format='xhtml5')
        htmltxt = (
            '<?xml version="1.0" encoding="UTF-8"?><body>' + htmltxt +
            '</body>'
        )
        root = ET.fromstring(htmltxt.encode('utf-8'))

        # Find all level 2 headers and generate IDs for each.
        for child in root:
            # For now, only level 2 headers in Markdown sections will be
            # included in tables of contents.
            if child.tag in ('h2', 'H2'):
                innertext = ''.join(child.itertext())
                idtext = self._getIDText(innertext, usedIDs)

                child.set('id', idtext)

                html_sd.headers.append((innertext, idtext))

        # Convert the document tree back to XHTML.
        for child in root:
            # Serialize the XML as UTF-8, but then convert it back to Python's
            # internal unicode representation.  This is necessary because the
            # string will automatically be serialized again as UTF-8 when
            # writing to the output destination.  It also avoids problems cause
            # by concatenating 8-bit strings and unicode strings.
            xhtmlstr = ET.tostring(child, encoding='utf-8', method='html')
            html_sd.htmltext += xhtmlstr.decode('utf-8')
            html_sd.htmltext += '\n'

        return html_sd

    def _assignHeaderIDs(self, document):
        usedIDs = set()

        for section in document.sections:
            if isinstance(section, EntitiesSection):
                self._assignHeaderIDsToNodeList(section.docnodes, usedIDs)
            elif isinstance(section, MarkdownSection):
                html_sd = self._assignHeaderIDsToMarkdown(
                    section.content, usedIDs
                )

                self.html_sds.append(html_sd)

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

        md_section_cnt = 0
        md_li_open = False

        for section in document.sections:
            if isinstance(section, MarkdownSection):
                for h_txt, h_id in self.html_sds[md_section_cnt].headers:
                    if md_li_open:
                        fileout.write('</li>\n')
                    li_str = '<li><a href="#{0}">{1}</a>\n'.format(h_id, h_txt)
                    fileout.write(li_str)
                    md_li_open = True

                md_section_cnt += 1

            elif isinstance(section, EntitiesSection):
                if len(section.docnodes) > 0:
                    self._writeToCNodeList(section.docnodes, fileout, 1)

                if md_li_open:
                    fileout.write('</li>\n')
                    md_li_open = False

        if md_li_open:
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

    def _writeSections(self, sections, fileout):
        md_section_cnt = 0

        for section in sections:
            if isinstance(section, MarkdownSection):
                fileout.write(self.html_sds[md_section_cnt].htmltext)
                md_section_cnt += 1
            else:
                if len(section.docnodes) > 0:
                    self._writeNodeList(section.docnodes, fileout, 0)
        
                fileout.write('\n')
        
    def write(self, document, fileout):
        """
        Generates an XHTML5 representation of a Document data structure.

        document: A Document instance.
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

        ufileout = codecs.getwriter('utf-8')(fileout)

        self.html_sds = []
        self._assignHeaderIDs(document)

        # If the first document section is a MarkdownSection with a level 1
        # header, use it as the document's title.
        titlestr = ''
        if (
            (len(document.sections) > 0) and
            isinstance(document.sections[0], MarkdownSection)
        ):
            for line in document.sections[0].content.splitlines():
                if line.startswith('# ') and len(line) > 2:
                    titlestr = line[2:]

        ufileout.write(header.format(titlestr))

        if self.include_ToC:
            self._writeToC(document, ufileout)

        self._writeSections(document.sections, ufileout)

        ufileout.write(footer)

