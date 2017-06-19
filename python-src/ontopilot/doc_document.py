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
# Classes that implement an abstract representation of documentation documents.
#

# Python imports.
from __future__ import unicode_literals
from module_extractor import ModuleExtractor, rel_axiom_types
from obohelper import termIRIToOboID, OBOIdentifierError

# Java imports.


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
                strval += '' + unicode(section)
            else:
                strval += unicode(section)

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
        self.docnodes = []

    def __str__(self):
        docnodes_str = 'Entities:'

        for docnode in self.docnodes:
            docnodes_str += '\n' + unicode(docnode)

        # Handle the case where docnodes is empty.
        if docnodes_str[-1] != '\n':
            docnodes_str += '\n'

        return docnodes_str + '\n'


class DocumentNode:
    """
    An internal class for building a tree-like data structure that
    represents ontology entities in an ontology documentation document.
    """
    def __init__(self, entity, srcont):
        """
        Initializes this DocumentNode with information from the ontology
        entity specified by entID.

        entity: An ontopilot ontology entity.
        srcont: The source ontopilot.Ontology object.
        """
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

                centity = self.ont.getExistingEntity(iristr)
                if centity is None:
                    raise RuntimeError(
                        'Error retrieving child entities of <{0}>: could not '
                        'find <{1}> in the source ontology or its imports '
                        'closure.'.format(self.entity.getIRI(), iristr)
                    )

                childnode = DocumentNode(centity, self.ont)
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

