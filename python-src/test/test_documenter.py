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


# Python imports.
from ontopilot.documenter import Documenter, DocumentationSpecificationError
from ontopilot.ontology import Ontology
import unittest
#from testfixtures import LogCapture

# Java imports.


class Test_Documenter(unittest.TestCase):
    """
    Tests the Documenter class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.doc = Documenter(self.ont)

        self.longMessage = True

    def test_parseDocSpec(self):
        """
        This method tests the results of _parseDocSpec() by converting the
        returned Document objects to a string representation and checking the
        string.
        """
        # Define test values and results for valid specifications.
        testvals = [
            {
                'docspec': '',
                'expected': ''
            },
            {
                'docspec': ' \n',
                'expected': ''
            },
            # Only a title.
            {
                'docspec': '# Document title',
                'expected': '# Document title'
            },
            # Several headings and other non-entities text.
            {
                'docspec':
"""
# Document title

---
## Classes

 - not an entities entry
""",
                'expected':
"""
# Document title

---
## Classes

 - not an entities entry
"""
            },
            # Multiple non-empty document sections.
            {
                'docspec':
"""
## Properties
- ID: OBTO:'test data property 1'

## Classes
- ID: OBTO:0010
- ID: OBTO:0011
""",
                'expected':
"""
## Properties
Entities:
    IRI: http://purl.obolibrary.org/obo/OBTO_0020
    OBO ID: OBTO:0020
    Label: test data property 1

## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBTO_0010
    OBO ID: OBTO:0010
    Label: test class 1

    IRI: http://purl.obolibrary.org/obo/OBTO_0011
    OBO ID: OBTO:0011
    Label: test class 2

"""
            },
            # Multi-level nested child specifications.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  children:
      - ID: OBTO:0010
        children:
            - ID: OBTO:0012
      - ID: OBTO:0011
- ID: OBTO:0090
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1
    Children:
        IRI: http://purl.obolibrary.org/obo/OBTO_0010
        OBO ID: OBTO:0010
        Label: test class 1
        Children:
            IRI: http://purl.obolibrary.org/obo/OBTO_0012
            OBO ID: OBTO:0012
            Label: test class 3

        IRI: http://purl.obolibrary.org/obo/OBTO_0011
        OBO ID: OBTO:0011
        Label: test class 2

    IRI: http://purl.obolibrary.org/obo/OBTO_0090
    OBO ID: OBTO:0090
    Label: 

"""
            },
            # Values of "descendants" that do not result in entity retrieval.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: none
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

"""
            },
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: 0
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

"""
            },
            # Single-level automatic descendants retrieval.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: 1
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1
    Children:
        IRI: http://purl.obolibrary.org/obo/OBTO_0010
        OBO ID: OBTO:0010
        Label: test class 1

        IRI: http://purl.obolibrary.org/obo/OBTO_0011
        OBO ID: OBTO:0011
        Label: test class 2

        IRI: http://purl.obolibrary.org/obo/OBTO_0012
        OBO ID: OBTO:0012
        Label: test class 3

"""
            },
            # Multi-level automatic descendants retrieval.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: all
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1
    Children:
        IRI: http://purl.obolibrary.org/obo/OBTO_0010
        OBO ID: OBTO:0010
        Label: test class 1
        Children:
            IRI: http://purl.obolibrary.org/obo/OBTO_0091
            OBO ID: OBTO:0091
            Label: 

        IRI: http://purl.obolibrary.org/obo/OBTO_0011
        OBO ID: OBTO:0011
        Label: test class 2

        IRI: http://purl.obolibrary.org/obo/OBTO_0012
        OBO ID: OBTO:0012
        Label: test class 3

"""
            },
            # Multi-level automatic descendants retrieval with filtering.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: all
  filter_by_label: " 1"
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1
    Children:
        IRI: http://purl.obolibrary.org/obo/OBTO_0010
        OBO ID: OBTO:0010
        Label: test class 1

"""
            },
            # Multi-level automatic descendants retrieval with both label and
            # IRI filtering.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: all
  filter_by_label: " 1"
  filter_by_IRI: "OBITO_"
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

"""
            },
            # Multiple mixed Markdown and entities sections.
            {
                'docspec':
"""
# Document title.

Markdown paragraph.

## Classes
- ID: OBITO:0001

Another Markdown *paragraph*.

* a
* list

## Properties
- ID: OBTO:'test data property 1'
A final Markdown paragraph.
""",
                'expected':
"""
# Document title.

Markdown paragraph.

## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

Another Markdown *paragraph*.

* a
* list

## Properties
Entities:
    IRI: http://purl.obolibrary.org/obo/OBTO_0020
    OBO ID: OBTO:0020
    Label: test data property 1

A final Markdown paragraph.
"""
            },
            # Including literal '^- .*' in a Markdown section.
            {
                'docspec':
r"""
 - text
-- text
\- text
\\- text
\\\- text

## Classes
- ID: OBITO:0001
""",
                'expected':
r"""
 - text
-- text
- text
\- text
\\- text

## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

"""
            },
            # Test UTF-8 unicode support.
            {
                'docspec':
"""
# Document title

## Greek alpha: \xce\xb1
Other text.
""",
                'expected':
u"""
# Document title

## Greek alpha: \u03b1
Other text.
"""
            }
        ]

        # Add some extra classes to the test ontology hierarchy.  After the
        # additions, the class structure should now be as follows:
        #
        # OBTO:0090
        # OBITO:0001
        # |--- OBTO:0010
        # |    |--- OBTO:0091
        # |--- OBTO:0011
        # |--- OBTO:0012
        newclass = self.ont.createNewClass('OBTO:0090')
        newclass = self.ont.createNewClass('OBTO:0091')
        newclass.addSuperclass('OBTO:0010')

        for testval in testvals:
            result = unicode(self.doc._parseDocSpec(testval['docspec']))
            #print result
            # When testing the result, remove the leading newline from the
            # expected results string.
            self.assertEqual(
                testval['expected'], result,
                msg='Input specification:"""{0}"""'.format(testval['docspec'])
            )

        # Create a cycle in the descendant relationships by making OBITO:0001 a
        # subclass of OBTO:0091, and make a polyhierarchy by making OBTO:0010 a
        # subclass of OBTO:0011.  The class structure should look like this:
        #
        # OBTO:0090
        # OBITO:0001
        # |--- OBTO:0010
        # |    |--- OBTO:0091
        # |         |--- OBITO:0001
        # |--- OBTO:0011
        # |    |--- OBTO:0010
        # |         |--- OBTO:0091
        # |              |--- OBITO:0001
        # |--- OBTO:0012
        newclass.addSubclass('OBITO:0001')
        ent = self.ont.getExistingClass('OBTO:0011')
        ent.addSubclass('OBTO:0010')

        # Run new multi-level descendants tests to make sure the cycle doesn't
        # "trap" the algorithms and that the polyhierarchy is handled
        # correctly.
        testvals = [
            # Multi-level automatic descendants retrieval.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: all
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1
    Children:
        IRI: http://purl.obolibrary.org/obo/OBTO_0010
        OBO ID: OBTO:0010
        Label: test class 1
        Children:
            IRI: http://purl.obolibrary.org/obo/OBTO_0091
            OBO ID: OBTO:0091
            Label: 
            Children:
                IRI: http://purl.obolibrary.org/obo/OBITO_0001
                OBO ID: OBITO:0001
                Label: imported test class 1

        IRI: http://purl.obolibrary.org/obo/OBTO_0011
        OBO ID: OBTO:0011
        Label: test class 2
        Children:
            IRI: http://purl.obolibrary.org/obo/OBTO_0010
            OBO ID: OBTO:0010
            Label: test class 1
            Children:
                IRI: http://purl.obolibrary.org/obo/OBTO_0091
                OBO ID: OBTO:0091
                Label: 
                Children:
                    IRI: http://purl.obolibrary.org/obo/OBITO_0001
                    OBO ID: OBITO:0001
                    Label: imported test class 1

        IRI: http://purl.obolibrary.org/obo/OBTO_0012
        OBO ID: OBTO:0012
        Label: test class 3

"""
            },
            # Multi-level automatic descendants retrieval with filtering.  This
            # also tests duplicate deletion.
            {
                'docspec':
"""
## Classes
- ID: OBITO:0001
  descendants: all
  filter_by_label: " 1"
""",
                'expected':
"""
## Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1
    Children:
        IRI: http://purl.obolibrary.org/obo/OBTO_0010
        OBO ID: OBTO:0010
        Label: test class 1
        Children:
            IRI: http://purl.obolibrary.org/obo/OBITO_0001
            OBO ID: OBITO:0001
            Label: imported test class 1

"""
            }
        ]

        for testval in testvals:
            result = unicode(self.doc._parseDocSpec(testval['docspec']))
            #print result
            self.assertEqual(testval['expected'], result)

        # Test error conditions to make sure they are handled correctly.
        testvals = [
            # Missing entity ID.
            {
                'docspec':
"""
## Classes
- descendants: 1
""",
                'errorstr': 'No entity ID was provided'
            },
            # Invalid ID.
            {
                'docspec':
"""
## Classes
- ID: OBTO:INVALID
""",
                'errorstr': 'No entity with the ID ".*" could be found'
            },
            # Invalid "descendants" values.
            {
                'docspec':
"""
## Classes
- ID: OBTO:0010
  descendants: invalid
""",
                'errorstr': 'Invalid value for "descendants" directive'
            },
            {
                'docspec':
"""
## Classes
- ID: OBTO:0010
  descendants: -1
""",
                'errorstr': 'Invalid value for "descendants" directive'
            },
        ]

        for testval in testvals:
            with self.assertRaisesRegexp(
                DocumentationSpecificationError, testval['errorstr']
            ):
                self.doc._parseDocSpec(testval['docspec'])

