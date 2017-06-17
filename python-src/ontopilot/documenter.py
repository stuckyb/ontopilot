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
from module_extractor import ModuleExtractor, rel_axiom_types
from obohelper import termIRIToOboID, OBOIdentifierError
from documentation_writers import MarkdownWriter
import StringIO
import re
import yaml

# Java imports.


class DocumentationSpecificationError(RuntimeError):
    """
    Exception for errors detected in the documentation specification.
    """
    pass


class Document:
    """
    Top-level class for data structures that provide an abstract representation
    of a complete ontology documentation document.
    """
    def __init__(self):
        self.sections = []

    def __str__(self):
        strval = ''

        sectioncnt = 0
        for section in self.sections:
            sectioncnt += 1
            if sectioncnt > 1:
                strval += '' + str(section)
            else:
                strval += str(section)

        return strval


class MarkdownSection:
    """
    Represents one top-level section in an ontology documentation document.
    EntitiesSection objects contain arbitrary Markdown content.
    """
    def __init__(self, contentstr):
        self.content = contentstr

    def __str__(self):
        return self.content


class EntitiesSection:
    """
    Represents one top-level section in an ontology documentation document.
    EntitiesSection objects contain ontology entity information.
    """
    def __init__(self):
        """
        Accepts a string that contains a YAML specification for an entities
        section, parses it, and instantiates the corresponding data structures
        as attributes of this EntitiesSection object.
        """
        self.title = ''
        self.custom_id = ''
        self.docnodes = []

    def __str__(self):
        docnodes_str = 'Title: {0}\nEntities:'.format(self.title)

        for docnode in self.docnodes:
            docnodes_str += '\n' + str(docnode)

        # Handle the case where docnodes is empty.
        if docnodes_str[-1] != '\n':
            docnodes_str += '\n'

        return docnodes_str + '\n'


class DocumentNode:
    """
    An internal class for building a tree-like data structure that
    represents ontology entities in an ontology documentation document.
    """
    def __init__(self, entID, srcont):
        """
        Initializes this DocumentNode with information from the ontology
        entity specified by entID.

        entID: An entity identifier.
        srcont: The source ontopilot.Ontology object.
        """
        entity = srcont.getExistingEntity(entID)
        if entity is None:
            raise DocumentationSpecificationError(
                'No entity with the ID "{0}" could be found in the source '
                'ontology.  Please provide the correct entity ID in the '
                'documentation specification.'.format(entID)
            )

        self.entIRI = entity.getIRI().toString()
        try:
            self.entOBO_ID = termIRIToOboID(self.entIRI)
        except OBOIdentifierError:
            self.entOBO_ID = ''

        labels = entity.getLabels()
        if len(labels) > 0:
            self.entlabel = labels[0]
        else:
            self.entlabel = ''

        defs = entity.getDefinitions()
        if len(defs) > 0:
            self.entdef = defs[0]
        else:
            self.entdef = ''

        self.custom_id = ''
        self.children = []

        self.entity = entity
        self.ont = srcont

    def getDescendants(self, maxdepth, curdepth=1, entset=None):
        """
        Recursively retrieves all descendents of the ontology entity contained
        by this DocumentNode up to the specified maxdepth.  If maxdepth == -1,
        all descendents are retrieved.  This method is also safe for ontologies
        that include cycles in their descendant relationships.
        """
        if entset is None:
            # Initialize a set to track all entities that are seen during the
            # recursion.  This is necessary to avoid getting stuck in circular
            # descendant relationships.
            entset = set(self.entIRI)

        me = ModuleExtractor(self.ont)

        # Get the direct descendants of this node's entity.
        components = me.getDirectlyRelatedComponents(
            self.entity.getOWLAPIObj(), (rel_axiom_types.DESCENDANTS,)
        )
        children = components[0]

        for child in children:
            iristr = child.getIRI().toString()
            if iristr not in entset:
                entset.add(iristr)
                childnode = DocumentNode(iristr, self.ont)
                self.children.append(childnode)
                if curdepth < maxdepth or maxdepth == -1:
                    childnode.getDescendants(maxdepth, curdepth + 1, entset)

        # Sort the child nodes in the following order: entity label, OBO ID,
        # IRI.  Use a custom function rather than attrgetter() to ensure that
        # the sort is not case sensitive.
        self.children.sort(
            key=lambda node:
                (
                    node.entlabel.lower(), node.entOBO_ID.lower(),
                    node.entIRI.lower()
                )
        )

    def getName(self):
        """
        Returns a string that can be used as the text name for this node.  The
        string will be one of the contained element's label, OBO ID, or IRI.
        Components will be evaluated in that order, and the forst non-empty
        value will be returned.
        """
        if self.entlabel != '':
            return self.entlabel
        elif self.entOBO_ID != '':
            return self.entOBO_ID
        else:
            return self.entIRI

    def _toIndentedStr(self, indentlevel):
        """
        Generates and returns a string representation of this DocumentNode,
        indented according to the specified indentlevel.
        """
        indent = '    ' * indentlevel
        strs = [
            'IRI: ' + self.entIRI,
            'OBO ID: ' + self.entOBO_ID,
            'Label: ' + self.entlabel
        ]
        if len(self.children) > 0:
            strs.append('Children:')

        retstr = '\n'.join([indent + strval for strval in strs])
        retstr += '\n'

        childcnt = 0
        for child in self.children:
            childcnt += 1
            retstr += child._toIndentedStr(indentlevel + 1)
            if childcnt < len(self.children):
                retstr += '\n'

        return retstr

    def __str__(self):
        return self._toIndentedStr(1)


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
        Builds a DocumentNode objects that corresponds with the raw data
        structure parsed from a strict YAML documentation specification.
        """
        if ('ID' not in rawdocnode) or not(isinstance(rawdocnode, dict)):
            raise DocumentationSpecificationError(
                'No entity ID was provided for an element in the documentation '
                'specification.  An ID must be provided for each ontology '
                'entity you wish to include in the ontology documentation.  '
                'The element with the missing ID is: {0}.'.format(rawdocnode)
            )

        docnode = DocumentNode(rawdocnode['ID'], self.ont)

        if 'children' in rawdocnode:
            for child in rawdocnode['children']:
                childnode = self._buildDocumentNode(child)
                docnode.children.append(childnode)
        elif 'descendants' in rawdocnode:
            desc_str = str(rawdocnode['descendants']).lower()
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

        return docnode

    def _buildEntitiesSection(self, rawsection):
        """
        Builds an EntitiesSection object that corresponds with the raw section
        data structure parsed from a YAML documentation specification.
        """
        title_strs = rawsection.keys()
        if len(title_strs) != 1:
            raise DocumentationSpecificationError(
                'Each ontology entities documentation section must have exactly one heading.  '
                'The current documentation section has the following headings: '
                '{0}.  Please correct the documentation specification '
                'file.'.format('"' + '", "'.join(title_strs) + '"')
            )

        title = title_strs[0].strip()

        new_section = EntitiesSection()
        new_section.title = title

        if rawsection[title_strs[0]] is not None:
            for rawdocnode in rawsection[title_strs[0]]:
                docnode = self._buildDocumentNode(rawdocnode)
                new_section.docnodes.append(docnode)

        return new_section

    def _readMarkdownSection(self, fin, firstline):
        """
        Reads a Markdown document section from a file-like object.
        """
        # A regular expression to match lines that include an escaped '---'.
        escp_re = re.compile(r'^\\+---\s*$')

        section_ended = False
        sectionstr = firstline

        while not(section_ended):
            pos = fin.tell()
            line = fin.readline()

            if line == '':
                section_ended = True
            elif line.rstrip() == '---':
                section_ended = True
            else:
                if escp_re.match(line) is not None:
                        line = line.replace(r'\-', '-', 1)

                sectionstr += line

        # Reset the file pointer to the beginning of the previous line.
        fin.seek(pos)

        if sectionstr.strip() == '':
            return None
        else:
            return MarkdownSection(sectionstr)

    def _readEntitiesSection(self, fin):
        """
        Reads an ontology entities document section from a file-like object.
        """
        # A regular expression to match lines that do not start with
        # whitespace.
        nws_re = re.compile('^\S+')

        section_ended = False
        sectionstr = ''

        linecnt = 0
        while not(section_ended):
            pos = fin.tell()
            line = fin.readline()
            linecnt += 1

            if line == '':
                section_ended = True
            elif (nws_re.match(line) is not None) and (linecnt > 1):
                section_ended = True
            else:
                sectionstr += line

        # Reset the file pointer to the beginning of the previous line.
        fin.seek(pos)

        content = yaml.load(sectionstr)

        return self._buildEntitiesSection(content)

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

        document = Document()

        # Parse the input document, separating Markdown content sections from
        # ontology entities sections.
        at_file_end = False        
        while not(at_file_end):
            line = docspecf.readline()

            if line == '':
                at_file_end = True
            elif line.rstrip() == '---':
                document.sections.append(self._readEntitiesSection(docspecf))
            else:
                newsection = self._readMarkdownSection(docspecf, line)
                if newsection is not None:
                    document.sections.append(newsection)

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

