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
from ontopilot import logger
from ontopilot import TRUE_STRS
import yaml

# Java imports.


class DocumentationSpecificationError(RuntimeError):
    """
    Exception for errors detected in the documentation specification.
    """
    pass


class _Document:
    """
    Top-level class for data structures that provide an abstract representation
    of a complete ontology documentation document.
    """
    def __init__(self):
        self.title = ''
        self.sections = []

    def __str__(self):
        if self.title != '':
            strval = '** {0} **\n\n'.format(self.title)
        else:
            strval = ''

        sectioncnt = 0
        for section in self.sections:
            sectioncnt += 1
            if sectioncnt > 1:
                strval += '\n' + str(section)
            else:
                strval += str(section)

        return strval


class _DocumentSection:
    """
    An internal "struct" that represents one top-level section in an ontology
    documentation document.
    """
    def __init__(self):
        self.title = ''
        self.docnodes = []

    def __str__(self):
        docnodes_str = 'Title: {0}\nEntities:'.format(self.title)

        for docnode in self.docnodes:
            docnodes_str += '\n' + str(docnode)

        # Handle the case where docnodes is empty.
        if docnodes_str[-1] != '\n':
            docnodes_str += '\n'

        return docnodes_str


class _DocumentNode:
    """
    An internal class for building a tree-like data structure that
    represents ontology entities in an ontology documentation document.
    """
    def __init__(self, entID, srcont):
        """
        Initializes this _DocumentNode with information from the ontology
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
                childnode = _DocumentNode(iristr, self.ont)
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

    def _toIndentedStr(self, indentlevel):
        """
        Generates and returns a string representation of this _DocumentNode,
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
    def __init__(self, src_ont):
        """
        Initializes this Documenter with a source ontology.

        src_ont: An ontopilot.Ontology instance.
        """
        self.ont = src_ont

    def _buildDocumentNode(self, rawdocnode):
        """
        Builds a _DocumentNode objects that corresponds with the raw data
        structure parsed from a strict YAML documentation specification.
        """
        if ('ID' not in rawdocnode) or not(isinstance(rawdocnode, dict)):
            raise DocumentationSpecificationError(
                'No entity ID was provided for an element in the documentation '
                'specification.  An ID must be provided for each ontology '
                'entity you wish to include in the ontology documentation.  '
                'The element with the missing ID is: {0}.'.format(rawdocnode)
            )

        docnode = _DocumentNode(rawdocnode['ID'], self.ont)

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

    def _buildDocumentSection(self, rawsection):
        """
        Builds a _DocumentSection object that corresponds with the raw section
        data structure parsed from a strict YAML documentation specification.
        """
        title_strs = rawsection.keys()
        if len(title_strs) != 1:
            raise DocumentationSpecificationError(
                'Each documentation section must have exactly one heading.  '
                'The current documentation section has the following headings: '
                '{0}.  Please correct the documentation specification '
                'file.'.format('"' + '", "'.join(title_strs) + '"')
            )

        title = title_strs[0].strip()

        new_section = _DocumentSection()
        new_section.title = title

        if rawsection[title_strs[0]] is not None:
            for rawdocnode in rawsection[title_strs[0]]:
                docnode = self._buildDocumentNode(rawdocnode)
                new_section.docnodes.append(docnode)

        return new_section

    def _parseDocSpec(self, docspec):
        """
        Builds a _Document data structure that captures the components of the
        ontology and relevant information from a documentation specification
        provided in YAML format.

        docspec: A source of YAML-formatted documentation specification
            information.  Can be either a byte string, regular (or unicode)
            string, or a file object.
        """
        parsed_docspec = yaml.safe_load_all(docspec)
        #print docspec
        #print parsed_docspec

        document = _Document()

        if parsed_docspec is not None:
            section_cnt = 0
            for rawsection in parsed_docspec:
                section_cnt += 1

                # If the first section contains only a string value, then
                # interpret it as the document's title.
                if (section_cnt == 1) and isinstance(rawsection, basestring):
                    document.title = rawsection
                else:
                    #print rawsection
                    section = self._buildDocumentSection(rawsection)
                    document.sections.append(section)
        
        return document

    def _writeMarkdown(self, doctree, fileout):
        """
        Uses a list of _DocumentSection objects to generate an output Markdown
        document.
        """

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
        print docDS

