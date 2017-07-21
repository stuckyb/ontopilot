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
# Generates documentation for the entities in a source ontology.
#

# Python imports.
from __future__ import unicode_literals
import codecs
import StringIO
import re
import yaml
from doc_document import (
    Document, MarkdownSection, EntitiesSection, DocumentNode
)
from documentation_writers import MarkdownWriter

# Java imports.


class DocumentationSpecificationError(RuntimeError):
    """
    Exception for errors detected in the documentation specification.
    """
    pass


class Documenter:
    def __init__(self, src_ont, writer=None):
        """
        Initializes this Documenter with a source ontology and, optionally, a
        custom writer instance.  If no writer is provided, markdown will be
        produced by default.

        src_ont: An ontopilot.Ontology instance.
        """
        self.ont = src_ont

        if writer is None:
            self.writer = MarkdownWriter()
        else:
            self.writer = writer

    def setWriter(self, writer):
        """
        Configures this Documenter to write to a specified output format.
        """
        self.writer = writer

    def _buildDocumentNode(self, rawdocnode):
        """
        Builds a list of DocumentNode objects that corresponds with the raw
        data structure parsed from a strict YAML documentation specification.
        """
        if ('ID' not in rawdocnode) or not(isinstance(rawdocnode, dict)):
            raise DocumentationSpecificationError(
                'No entity ID was provided for an element in the documentation '
                'specification.  An ID must be provided for each ontology '
                'entity you wish to include in the ontology documentation.  '
                'The element with the missing ID is: {0}.'.format(rawdocnode)
            )

        entID = rawdocnode['ID']
        entity = self.ont.getExistingEntity(entID)
        if entity is None:
            raise DocumentationSpecificationError(
                'No entity with the ID "{0}" could be found in the source '
                'ontology.  Please provide the correct entity ID in the '
                'documentation specification.'.format(entID)
            )

        docnode = DocumentNode(entity, self.ont)

        if 'children' in rawdocnode:
            for child in rawdocnode['children']:
                childnodes = self._buildDocumentNode(child)
                docnode.children.extend(childnodes)
        elif 'descendants' in rawdocnode:
            desc_str = unicode(rawdocnode['descendants']).lower()
            if desc_str != 'none':
                # Get the integer value of maxdepth for the call to
                # getDescendants() that corresponds with the value of the
                # "descendants" directive.
                if desc_str == 'all':
                    maxdepth = -1
                else:
                    try:
                        maxdepth = int(desc_str)
                        if maxdepth < 0:
                            raise ValueError()
                    except ValueError:
                        raise DocumentationSpecificationError(
                            'Invalid value for "descendants" directive in '
                            'documentation specification file: "{0}".  Valid '
                            'values for "descendants" are "all", "none", or '
                            'any non-negative integer.'.format(
                                rawdocnode['descendants']
                            )
                        )

                if maxdepth != 0:
                    docnode.getDescendants(maxdepth)

        label_filter = IRI_filter = ''
        if 'filter_by_label' in rawdocnode:
            label_filter = unicode(rawdocnode['filter_by_label'])
        if 'filter_by_IRI' in rawdocnode:
            IRI_filter = unicode(rawdocnode['filter_by_IRI'])

        if label_filter != '' or IRI_filter != '':
            return docnode.filterNode(label_filter, IRI_filter)
        else:
            return [docnode]

    def _buildEntitiesSection(self, rawsection):
        """
        Builds an EntitiesSection object that corresponds with the raw section
        data structure parsed from a YAML documentation specification.
        """
        new_section = EntitiesSection()

        for rawdocnode in rawsection:
            new_docnodes = self._buildDocumentNode(rawdocnode)
            new_section.docnodes.extend(new_docnodes)

        return new_section

    def _readMarkdownSection(self, fin, firstline):
        """
        Reads a Markdown document section from a file-like object.
        """
        # A regular expression to match lines that start with an escaped '- '.
        escp_re = re.compile(r'^\\+- ')

        section_ended = False
        sectionstr = firstline

        while not(section_ended):
            line = fin.readline()

            if line == '':
                section_ended = True
            elif line.startswith('- '):
                section_ended = True
            else:
                if escp_re.match(line) is not None:
                        line = line.replace(r'\-', '-', 1)

                sectionstr += line

        if sectionstr.strip() == '':
            return (None, line)
        else:
            return (MarkdownSection(sectionstr), line)

    def _readEntitiesSection(self, fin, firstline):
        """
        Reads an ontology entities document section from a file-like object.
        """
        # A regular expression to match lines that do not start with
        # whitespace.
        nws_re = re.compile('^\S+')

        section_ended = False
        sectionstr = firstline

        while not(section_ended):
            line = fin.readline()

            if line == '':
                section_ended = True
            elif (
                not(line.startswith('- ')) and (nws_re.match(line) is not None)
            ):
                section_ended = True
            else:
                sectionstr += line

        content = yaml.load(sectionstr)

        return (self._buildEntitiesSection(content), line)

    def _parseDocSpec(self, docspec):
        """
        Builds a Document data structure that captures the components of the
        ontology and relevant information from a documentation specification
        provided in mixed Markdown/YAML format.

        docspec: A source of mixed Markdown/YAML documentation specification
            information.  Can be either a regular string, unicode string, or a
            file object.
        """
        if isinstance(docspec, basestring):
            docspecf = StringIO.StringIO(docspec)
        else:
            docspecf = docspec

        udocspecf = codecs.getreader('utf-8')(docspecf)

        document = Document()

        # Parse the input document, separating Markdown content sections from
        # ontology entities sections.
        nextline = udocspecf.readline()
        while nextline != '':
            if nextline.startswith('- '):
                entsec, nextline = self._readEntitiesSection(
                    udocspecf, nextline
                )
                document.sections.append(entsec)
            else:
                mdsec, nextline = self._readMarkdownSection(
                    udocspecf, nextline
                )
                if mdsec is not None:
                    document.sections.append(mdsec)

        if isinstance(docspec, basestring):
            docspecf.close()
        
        return document

    def document(self, docspec, fileout):
        """
        Generates Markdown documentation for the source ontology according to a
        documentation specification provided in YAML format.

        docspec: A source of YAML-formatted documentation specification
            information.  Can be either a byte string, regular (or unicode)
            string, or a file object.
        fileout: A writable file object.
        """
        docDS = self._parseDocSpec(docspec)
        #print docDS

        self.writer.write(docDS, fileout)

