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
import abc
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
        docnodes_str = 'Entities:\n'

        for docnode in self.docnodes:
            docnodes_str += unicode(docnode)

        # Handle the case where docnodes is empty.
        if docnodes_str[-1] != '\n':
            docnodes_str += '\n'

        return docnodes_str


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

        self.comments = entity.getComments()

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
            # Initialize a dictionary to track all entities that are seen
            # during the recursion.  This is necessary to avoid getting stuck
            # in circular descendant relationships.  Entity IRIs are the set of
            # dictionary keys, and they map to DocumentNode objects.
            entset = {self.entIRI: self}

        me = ModuleExtractor(self.ont)

        # Get the direct descendants of this node's entity.
        components = me.getDirectlyRelatedComponents(
            self.entity.getOWLAPIObj(), (rel_axiom_types.DESCENDANTS,)
        )
        children = components[0]

        for child in children:
            iristr = child.getIRI().toString()

            if iristr in entset:
                self.children.append(entset[iristr])
            else:
                centity = self.ont.getExistingEntity(iristr)
                if centity is None:
                    raise RuntimeError(
                        'Error retrieving child entities of <{0}>: could not '
                        'find <{1}> in the source ontology or its imports '
                        'closure.'.format(self.entity.getIRI(), iristr)
                    )

                childnode = DocumentNode(centity, self.ont)
                self.children.append(childnode)

                entset[iristr] = childnode
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

    def filterNode(self, label_filter, IRI_filter, entset=None):
        """
        Filters this node and all of its descendants by label text and/or IRI
        string.  Any nodes that do not match the filter(s) will be removed from
        the hierarchy, including the root node.  Returns a list of nodes.  If
        the root node (i.e., this node) matches the filter(s), then the
        returned list will only contain the root node.

        label_filter: Label filter string.
        IRI_filter: IRI filter string.
        """
        if entset is None:
            # Create a set to keep track of which nodes we've seen so that we
            # can avoid getting stuck in graph cycles.
            entset = set()

        if self.entIRI not in entset:
            entset.add(self.entIRI)

            filtered_children = []

            for child in self.children:
                filtered_children.extend(
                    child.filterNode(label_filter, IRI_filter, entset)
                )

            # Remove any duplicate nodes.
            childIRIs = set()
            deduped_filtered = []

            for node in filtered_children:
                if node.entIRI not in childIRIs:
                    deduped_filtered.append(node)
                    childIRIs.add(node.entIRI)

            # Sort the filtered child nodes.  Nodes are sorted in the following
            # order: entity label, OBO ID, IRI.
            deduped_filtered.sort(
                key=lambda node:
                    (
                        node.entlabel.lower(), node.entOBO_ID.lower(),
                        node.entIRI.lower()
                    )
            )

            self.children = deduped_filtered                   

        if (label_filter in self.entlabel) and (IRI_filter in self.entIRI):
            return [self]
        else:
            return self.children

    def getName(self):
        """
        Returns a string that can be used as the text name for this node.  The
        string will be one of the contained element's label, OBO ID, or IRI.
        Components will be evaluated in that order, and the first non-empty
        value will be returned.
        """
        if self.entlabel != '':
            return self.entlabel
        elif self.entOBO_ID != '':
            return self.entOBO_ID
        else:
            return self.entIRI

    def __str__(self):
        text_nsg = TextNodeStrGenerator()

        return text_nsg.getNodeString(self)


class NodeStrGenerator(object):
    """
    An abstract base class that defines a traversal algorithm and interface for
    converting a DocumentNode object into a string representation.  This ABC is
    also suitable for use as a "mixin" class with multiple inheritance.
    """
    def __init__(self):
        # This is an abstract base class.
        __metaclass__ = abc.ABCMeta

    def getNodeString(self, docnode):
        """
        Returns a string representation of this DocumentNode object.
        """
        return self._processNode(docnode, 0, None)

    def _processNode(self, node, depth, entset=None):
        """
        Recursively traverses the current DocumentNode and its children,
        building up a string representation of the top-level DocumentNode along
        the way.  This method traverses polyhierarchies as fully as possible
        while avoiding circular descendant relationships (i.e., graph cycles).
        This method implements the traversal algorithm and calls
        _getNodeOpeningText() and _getNodeClosingText() to actually produce the
        string representations.
        """
        if entset is None:
            # Initialize a set to track all nodes that are in the midst of a
            # descendant traversal operation.  This is necessary to avoid
            # getting stuck in circular descendant relationships.  Once all
            # children of a node are processed, the node is removed from the
            # set, which ensures that polyhierarchies are properly traversed
            # (note that a single node might be visited multiple times).
            entset = set()

        will_traverse = node.entIRI not in entset

        retstr = self._getNodeOpeningText(node, depth, will_traverse)

        if will_traverse:
            entset.add(node.entIRI)

            childcnt = 0
            for child in node.children:
                childcnt += 1
                retstr += self._processNode(child, depth + 1, entset)

            entset.remove(node.entIRI)

        retstr += self._getNodeClosingText(node, depth, will_traverse)

        return retstr

    @abc.abstractmethod
    def _getNodeOpeningText(self, node, depth, will_traverse):
        """
        Returns the text that should appear before any children of the current
        node in the traversal.

        node: A DocumentNode object.
        depth: The current traversal depth.
        will_traverse: Whether the children of this node will be visited.
        """
        pass

    @abc.abstractmethod
    def _getNodeClosingText(self, node, depth, traversed):
        """
        Returns the text that should appear after any children of the current
        node in the traversal.

        node: A DocumentNode object.
        depth: The current traversal depth.
        traversed: Whether the children of this node were visited.
        """
        pass


class TextNodeStrGenerator(NodeStrGenerator):
    """
    A NodeStrGenerator that produces a basic text representation of a
    DocumentNode.
    """
    def _getNodeOpeningText(self, node, depth, will_traverse):
        """
        Returns the text that should appear before any children of the current
        node in the traversal.

        node: A DocumentNode object.
        depth: The current traversal depth.
        will_traverse: Whether the children of this node will be visited.
        """
        indent = '    ' * (depth + 1)

        strs = [
            'IRI: ' + node.entIRI,
            'OBO ID: ' + node.entOBO_ID,
            'Label: ' + node.entlabel
        ]
        retstr = '\n'.join([indent + strval for strval in strs])
        retstr += '\n'

        if will_traverse and len(node.children) > 0:
            retstr += indent + 'Children:\n'

        return retstr

    def _getNodeClosingText(self, node, depth, traversed):
        """
        Returns the text that should appear after any children of the current
        node in the traversal.

        node: A DocumentNode object.
        depth: The current traversal depth.
        traversed: Whether the children of this node were visited.
        """
        if traversed and len(node.children) > 0:
            return ''
        else:
            return '\n'

