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
# Implements a custom table of contents (ToC) extension for the Python Markdown
# library to generate ToCs for HTML ontology documentation files.
#

# Python imports.
from __future__ import unicode_literals
import re
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree

# Java imports.


class _ToCNode:
    """
    A simple "struct" for building a tree-like data structure of nodes for
    Tables of Contents.
    """
    def __init__(self, idtext, innertext):
        self.idtext = idtext
        self.innertext = innertext
        self.childnodes = []


class _ToCGenerator(Treeprocessor):
    def __init__(self, md, document, startlevel=2):
        """
        document:  A _Document instance.
        """
        super(_ToCGenerator, self).__init__(md)

        self.document = document

        if not(isinstance(startlevel, int)):
            raise RuntimeError(
                'Invalid HTML header level: "{0}".  The header level must be '
                'an integer from 1 to 6.'.format(startlevel)
            )

        if startlevel < 1 or startlevel > 6:
            raise RuntimeError(
                'Invalid HTML header level: {0}.  The header level must be '
                'an integer from 1 to 6.'.format(startlevel)
            )

        self.htag_regex = re.compile('[Hh][{0}-6]'.format(startlevel))

        self.usedIDs = set()

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

        return idtext

    def _getUniqueValue(self, strval, collection):
        """
        Given a string value and a collection that supports the "in" operator,
        returns a possibly modified copy of strval that is not already in the
        collection.  The returned string is guaranteed to be non-empty.
        """
        finalstr = strval
        counter = 1
        while finalstr in collection or finalstr == '':
            finalstr = strval + '-{0}'.format(counter)
            counter += 1

        return finalstr

    def _makeToCNodeList(self, nodelist, startingIDs):
        """
        Generates ToC HTML for a list of _DocumentNode objects.
        """
        ul = etree.Element('ul')

        for node in nodelist:
            idstr = self._getIDText(node.getName(), startingIDs)
            assert idstr in self.usedIDs, (
                'The ToC ID "{0}" did not match a header ID in the HTML '
                'document.'.format(idstr)
            )
            startingIDs.add(idstr)

            li = etree.Element('li')
            anchor = etree.Element('a')
            li.append(anchor)
            anchor.set('href', '#' + idstr)
            anchor.text = node.getName()
            ul.append(li)

            if len(node.children) > 0:
                li.append(self._makeToCNodeList(node.children, startingIDs))

        return ul

    def _makeToC(self, startingIDs):
        """
        Generates an XML tree for the documentation table of contents.
        """
        # Because the element nesting in the generated HTML does not exactly
        # match the nesting of logical components in the documentation, we
        # can't easily use the HTML structure to generate the ToC.  Instead,
        # when generating the header IDs, run() creates a set of all starting
        # header IDs.  Then, in this method, when traversing the document data
        # structure, as long as we follow the same order as the traversal in
        # run(), we can duplicate the procedure for generating IDs for each
        # document component and get IDs that match those used in the HTML.

        toc = etree.Element('div')
        toc.set('class', 'toc')

        ul = etree.Element('ul')
        toc.append(ul)

        for section in self.document.sections:
            idstr = self._getIDText(section.title, startingIDs)
            assert idstr in self.usedIDs, (
                'The ToC ID "{0}" did not match a header ID in the HTML '
                'document.'.format(idstr)
            )
            startingIDs.add(idstr)

            li = etree.Element('li')
            anchor = etree.Element('a')
            li.append(anchor)
            anchor.set('href', '#' + idstr)
            anchor.text = section.title
            ul.append(li)

            if len(section.docnodes) > 0:
                li.append(
                    self._makeToCNodeList(section.docnodes, startingIDs)
                )

        return toc

    def run(self, root):
        self.usedIDs.clear()

        # Generate the set of all IDs in the document.
        for elem in root.iter():
            if 'id' in elem.attrib:
                self.usedIDs.add(elem.get('id'))

        # Save this initial set of IDs for use when generating the ToC.
        startingIDs = set(self.usedIDs)

        # Generate the header IDs.
        for elem in root.iter():
            if self.htag_regex.match(elem.tag):
                innertext = ''.join(elem.itertext())
                if 'id' not in elem.attrib:
                    idtext = self._getIDText(innertext, self.usedIDs)
                    elem.set('id', idtext)
                    self.usedIDs.add(idtext)
                else:
                    idtext = elem.get('id')

        tocdiv = self._makeToC(startingIDs)

        # Generate a list of (parent, child) pairs where child is an element to
        # replace with the ToC.  We have to make the changes after the
        # iteration so we don't invalidate the iterator.
        changepairs = []
        for parent in root.iter():
            for child in parent:
                innertext = ''.join(child.itertext())

                if (
                    innertext.strip() == '[ToC]' and
                    not(self.htag_regex.match(child.tag))
                ):
                    changepairs.append((parent, child))

        for changepair in changepairs:
            parent, child = changepair
            for index in range(len(parent)):
                if parent[index] == child:
                    parent[index] = tocdiv


class DocToCExtension(Extension):
    """
    A custom table of contents (ToC) extension for ontology documentation.
    Implements the following features not available in the standard Python
    Markdown extensions: 1) allows high-level headers to be ignored; and 2)
    ensures that the nesting of the ToC lists matches the nesting of the entity
    documentation lists.
    """
    def __init__(self, document, *args, **kwargs):
        """
        document:  A _Document instance.
        """
        self.config = {
            'startlevel': [2, 'Header level at which the ToC should begin.']
        }

        super(DocToCExtension, self).__init__(*args, **kwargs)

        self.document = document

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)

        tocgen = _ToCGenerator(md, self.document, self.getConfig('startlevel'))
        md.treeprocessors.add('doctoc', tocgen, '_end')

