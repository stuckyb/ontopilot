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
from doc_document import MarkdownSection, EntitiesSection, NodeStrGenerator


# Java imports.


# Defines string constants for documentation format types.
DOC_FORMAT_TYPES = ('HTML', 'Markdown')


def getDocumentationWriter(docformat):
    """
    A factory function to instantiate a Writer class for a given documentation
    format string constant.
    """
    lc_docformat = docformat.lower()

    if lc_docformat == 'html':
        return HTMLWriter()
    elif lc_docformat == 'markdown':
        return MarkdownWriter()
    else:
        raise RuntimeError(
            'Unrecognized documentation format string: "{0}".  Supported '
            'values are: "{1}".'.format(
                docformat, '", "'.join(DOC_FORMAT_TYPES)
            )
        )


class _BaseWriter(NodeStrGenerator):
    """
    A base class for all writers that implements a generic algorithm for
    generating a text representation of a Document object.  This is not an
    abstract base class because all of the writer methods are implemented (most
    of which do nothing).  Thus, subclasses can choose which writer methods
    they need to implement without having to worry about the others.  It is
    thus similar to Java's adapter classes.
    """
    def __init__(self):
        pass

    def _getNodeOpeningText(self, node, depth, will_traverse):
        """
        This method is from NodeStrGenerator.
        """
        return ''
  
    def _getNodeClosingText(self, node, depth, traversed):
        """
        This method is from NodeStrGenerator.
        """
        return ''
  
    def _writeHeader(self, document, fileout):
        pass

    def _writeMarkdownSection(self, section, sectioncnt, fileout):
        """
        Writes a MarkdownSection of a Document object.

        section: A MarkdownSection object.
        sectioncnt: The 0-based count of MarkdownSections that have been seen.
        fileout: An output file stream.
        """
        pass

    def _writeEntitiesSection(self, section, sectioncnt, fileout):
        """
        Writes an EntitiesSection of a Document object.

        section: An EntitiesSection object.
        sectioncnt: The 0-based count of EntitiesSections that have been seen.
        fileout: An output file stream.
        """
        pass

    def _writeFooter(self, document, fileout):
        pass

    def write(self, document, fileout):
        """
        Generates a UTF-8 representation of a Document data structure.

        document: A Document instance.
        fileout: A writable file object.
        """
        ufileout = codecs.getwriter('utf-8')(fileout)

        self._writeHeader(document, ufileout)

        mdsection_cnt = entsection_cnt = 0

        for section in document.sections:
            if isinstance(section, MarkdownSection):
                self._writeMarkdownSection(section, mdsection_cnt, ufileout)
                mdsection_cnt += 1
            elif isinstance(section, EntitiesSection):
                self._writeEntitiesSection(section, entsection_cnt, ufileout)
                entsection_cnt += 1
            else:
                raise RuntimeError(
                    'Unrecognized document section type: {0}.'.format(
                        type(section)
                    )
                )

        self._writeFooter(document, ufileout)


class MarkdownWriter(_BaseWriter):
    def __init__(self):
        super(MarkdownWriter, self).__init__()

    def _getNodeOpeningText(self, node, depth, will_traverse):
        nname = node.getName()
        indentstr = '    ' * depth

        retstr = '{0}* ### {1}\n\n'.format(indentstr, nname)

        if node.entOBO_ID != nname and node.entOBO_ID != '':
            retstr += '{0}  OBO ID: {1}\n\n'.format(indentstr, node.entOBO_ID)

        retstr += '{0}  IRI: {1}\n\n'.format(indentstr, node.entIRI)

        if node.entdef != '':
            retstr += '{0}  Definition: {1}\n\n'.format(indentstr, node.entdef)
        
        for comment in node.comments:
            retstr += '{0}  Comment: {1}\n\n'.format(indentstr, comment)

        return retstr
  
    def _writeMarkdownSection(self, section, sectioncnt, fileout):
        fileout.write(section.content)

    def _writeEntitiesSection(self, section, sectioncnt, fileout):
        for node in section.docnodes:
            fileout.write(self.getNodeString(node))
    
        fileout.write('\n')


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


class _HTMLToCNodeStrGenerator(NodeStrGenerator):
    """
    A NodeStrGenerator that produces HTML text for the table of contents entry
    for a DocumentNode in an HTML documentation file.
    """
    def _getNodeOpeningText(self, node, depth, will_traverse):
        indentstr = '    ' * (depth + 1)
        subindentstr = '    ' * (depth + 2)

        nname = node.getName()

        retstr = '{0}<li><a href="#{1}">{2}</a>'.format(
            indentstr, node.custom_id, nname
        )
    
        if will_traverse and len(node.children) > 0:
            retstr += '\n'
            retstr += '{0}<ul>\n'.format(subindentstr)

        return retstr

    def _getNodeClosingText(self, node, depth, traversed):
        indentstr = '    ' * (depth + 1)
        subindentstr = '    ' * (depth + 2)
        retstr = ''

        if traversed and len(node.children) > 0:
            retstr += '{0}</ul>\n'.format(subindentstr)
            retstr += '{0}</li>\n'.format(indentstr)
        else:
            retstr += '</li>\n'

        return retstr


class HTMLWriter(_BaseWriter):
    def __init__(self, include_ToC=True):
        """
        include_ToC (boolean): Whether to generate a table of contents for the
            documentation.
        """
        super(HTMLWriter, self).__init__()

        self.include_ToC = include_ToC

        # A list of _HTMLSectionDetails objects.
        self.html_sds = []

        # A set of reserved HTML entity IDs (i.e., IDs that should not be
        # assigned to user content).
        self.RESERVED_IDS = {'toc', 'main'}

        # A set to keep track of HTML entity IDs that have already been written
        # to the output file.  This is so we can avoid assigning the same ID to
        # nodes that are visited more than once in a hierarchy of ontology
        # entities.
        self.printed_IDs = set()

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

    def _assignHeadingIDsToNodeList(self, nodelist, usedIDs, entset=None):
        if entset is None:
            # Initialize a set to track all DocumentNodes that are seen
            # during the recursion.  This is necessary to avoid getting stuck
            # in circular descendant relationships.
            entset = set()

        for node in nodelist:
            if node.entIRI not in entset:
                entset.add(node.entIRI)

                nname = node.getName()
                node.custom_id = self._getIDText(nname, usedIDs)

                self._assignHeadingIDsToNodeList(
                    node.children, usedIDs, entset
                )

    def _assignHeadingIDsToMarkdown(self, mdtext, usedIDs):
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
            # writing to the output destination.  It also avoids problems
            # caused by concatenating 8-bit strings and unicode strings.
            xhtmlstr = ET.tostring(child, encoding='utf-8', method='html')
            html_sd.htmltext += xhtmlstr.decode('utf-8')
            html_sd.htmltext += '\n'

        return html_sd

    def _assignHeadingIDs(self, document):
        usedIDs = set(self.RESERVED_IDS)

        for section in document.sections:
            if isinstance(section, EntitiesSection):
                self._assignHeadingIDsToNodeList(section.docnodes, usedIDs)
            elif isinstance(section, MarkdownSection):
                html_sd = self._assignHeadingIDsToMarkdown(
                    section.content, usedIDs
                )

                self.html_sds.append(html_sd)

    def _writeToC(self, document, fileout):
        fileout.write("""
<nav id="toc">
<h1>Table of Contents</h1>
<div id="toc_buttons">
    <div id="expand_all" class="top_toc_button">expand all</div>
    <div id="collapse_all" class="top_toc_button">collapse all</div>
</div>
<ul>
""")
        ht_nsg = _HTMLToCNodeStrGenerator()

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
                if not(md_li_open):
                    fileout.write('<li>\n')
                    md_li_open = True

                if len(section.docnodes) > 0:
                    fileout.write('    <ul>\n')

                    for node in section.docnodes:
                        fileout.write(ht_nsg.getNodeString(node))

                    fileout.write('    </ul>\n')

                fileout.write('</li>\n')
                md_li_open = False

        if md_li_open:
            fileout.write('</li>\n')

        fileout.write('</ul>\n</nav>\n\n')

    def _getCommentsDiv(self, comments, indentstr):
        retstr = '{0}<div class="comments">\n'.format(indentstr)

        if len(comments) == 1:
            retstr += '{0}  <p>Comment: {1}</p>\n'.format(
                indentstr, comments[0]
            )

        elif len(comments) > 1:
            retstr += '{0}  <p>Comments:</p>\n'.format(indentstr)
            retstr += '{0}  <ul>\n'.format(indentstr)

            for comment in comments:
                retstr += '{0}    <li>{1}</li>\n'.format(indentstr, comment)

            retstr += '{0}  </ul>\n'.format(indentstr)

        retstr += '{0}</div>\n'.format(indentstr)

        return retstr

    def _getNodeOpeningText(self, node, depth, will_traverse):
        li_indentstr = '    ' * (depth)
        indentstr = '    ' * (depth + 1)

        nname = node.getName()

        retstr = '{0}<li>\n'.format(li_indentstr)

        # Check if this entity (and its ID) has already been "printed" in the
        # output document.  If so, do not repeat the ID.
        if node.custom_id not in self.printed_IDs:
            self.printed_IDs.add(node.custom_id)

            retstr += '{0}<h3 id="{1}">{2}</h3>\n'.format(
                indentstr, node.custom_id, nname
            )
        else:
            retstr += '{0}<h3>{1}</h3>\n'.format(indentstr, nname)

        if node.entOBO_ID != nname and node.entOBO_ID != '':
            retstr += '{0}<p>OBO ID: {1}</p>\n'.format(
                    indentstr, node.entOBO_ID
            )

        retstr += '{0}<p>IRI: {1}</p>\n'.format(indentstr, node.entIRI)

        if node.entdef != '':
            retstr += '{0}<p>Definition: {1}</p>\n'.format(
                    indentstr, node.entdef
            )

        if len(node.comments) > 0:
            retstr += self._getCommentsDiv(node.comments, indentstr)

        if will_traverse and len(node.children) > 0:
            retstr += '{0}<ul class="entity_list">\n'.format(indentstr)
    
        return retstr

    def _getNodeClosingText(self, node, depth, traversed):
        li_indentstr = '    ' * (depth)
        indentstr = '    ' * (depth + 1)
        retstr = ''

        if traversed and len(node.children) > 0:
            retstr = '{0}</ul>\n'.format(indentstr)

        retstr += '{0}</li>\n'.format(li_indentstr)

        return retstr
  
    def _writeMarkdownSection(self, section, sectioncnt, fileout):
        """
        Writes a MarkdownSection of a Document object.

        section: A MarkdownSection object.
        sectioncnt: The 0-based count of MarkdownSections that have been seen.
        fileout: An output file stream.
        """
        fileout.write(self.html_sds[sectioncnt].htmltext)

    def _writeEntitiesSection(self, section, sectioncnt, fileout):
        """
        Writes an EntitiesSection of a Document object.

        section: An EntitiesSection object.
        sectioncnt: The 0-based count of EntitiesSections that have been seen.
        fileout: An output file stream.
        """
        if len(section.docnodes) > 0:
            fileout.write('<ul class="entity_list">\n')

            for node in section.docnodes:
                fileout.write(self.getNodeString(node))

            fileout.write('</ul>\n\n')

    def _writeHeader(self, document, fileout):
        header = """<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8" />
    <title>{0}</title>
    <link rel="stylesheet" type="text/css" href="documentation_styles.css" />
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <script src="navtree.js"></script>
</head>
<body>
"""

        self.html_sds = []
        self.printed_IDs.clear()
        self._assignHeadingIDs(document)

        # If the first document section is a MarkdownSection with a level 1
        # heading, use it as the document's title.
        titlestr = ''
        if (
            (len(document.sections) > 0) and
            isinstance(document.sections[0], MarkdownSection)
        ):
            for line in document.sections[0].content.splitlines():
                if line.startswith('# ') and len(line) > 2:
                    titlestr = line[2:]

        fileout.write(header.format(titlestr))

        if self.include_ToC:
            self._writeToC(document, fileout)

        fileout.write('<main>\n')

    def _writeFooter(self, document, fileout):
        fileout.write('</main>\n</body>\n</html>')

