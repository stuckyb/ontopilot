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
                'expected': 
"""
# Document title"""
            },
            # A single empty document section.
            {
                'docspec':
"""
---
Classes:
""",
                'expected':
"""
Title: Classes
Entities:

"""
            },
            # A single entities section with an opening Markdown section.
            {
                'docspec':
"""
#Document title

---
Classes:
""",
                'expected':
""" 
#Document title

Title: Classes
Entities:

"""
            },
            # Multiple empty entities sections.
            {
                'docspec':
"""
---
Properties:
---
Classes:
""",
                'expected':
"""
Title: Properties
Entities:

Title: Classes
Entities:

"""
            },
            # Multiple non-empty document sections.
            {
                'docspec':
"""
---
Properties:
    - ID: OBTO:'test data property 1'
---
Classes:
    - ID: OBTO:0010
    - ID: OBTO:0011
""",
                'expected':
"""
Title: Properties
Entities:
    IRI: http://purl.obolibrary.org/obo/OBTO_0020
    OBO ID: OBTO:0020
    Label: test data property 1

Title: Classes
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
---
Classes:
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
Title: Classes
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
---
Classes:
    - ID: OBITO:0001
      descendants: none
""",
                'expected':
"""
Title: Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

"""
            },
            {
                'docspec':
"""
---
Classes:
    - ID: OBITO:0001
      descendants: 0
""",
                'expected':
"""
Title: Classes
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
---
Classes:
    - ID: OBITO:0001
      descendants: 1
""",
                'expected':
"""
Title: Classes
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
---
Classes:
    - ID: OBITO:0001
      descendants: all
""",
                'expected':
"""
Title: Classes
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
            # Multiple mixed Markdown and entities sections.
            {
                'docspec':
"""
# Document title.

Markdown paragraph.

---
Classes:
    - ID: OBITO:0001

Another Markdown *paragraph*.

* a
* list
---
Properties:
    - ID: OBTO:'test data property 1'
A final Markdown paragraph.
""",
                'expected':
""" 
# Document title.

Markdown paragraph.

Title: Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

Another Markdown *paragraph*.

* a
* list
Title: Properties
Entities:
    IRI: http://purl.obolibrary.org/obo/OBTO_0020
    OBO ID: OBTO:0020
    Label: test data property 1

A final Markdown paragraph.
"""
            },
            # Including literal '---' in a Markdown section.
            {
                'docspec':
r"""
 ---
\---
\\---
\\\---
---
Classes:
    - ID: OBITO:0001
""",
                'expected':
r""" 
 ---
---
\---
\\---
Title: Classes
Entities:
    IRI: http://purl.obolibrary.org/obo/OBITO_0001
    OBO ID: OBITO:0001
    Label: imported test class 1

"""
            },
        ]

        # Add some extra classes to the test ontology hierarchy.
        newclass = self.ont.createNewClass('OBTO:0090')
        classent = self.ont.getExistingClass('OBTO:0010')
        newclass = self.ont.createNewClass('OBTO:0091')
        classent.addSubclass('OBTO:0091')

        for testval in testvals:
            result = str(self.doc._parseDocSpec(testval['docspec']))
            #print result
            # When testing the result, remove the leading newline from the
            # expected results string.
            self.assertEqual(
                testval['expected'][1:], result,
                msg='Input specification:"""{0}"""'.format(testval['docspec'])
            )

        # Create a cycle in the descendant relationships, then run the last
        # test again to make sure the cycle doesn't "trap" the algorithm.
        newclass.addSubclass('OBTO:0010')
        testval = testvals[-1]
        result = str(self.doc._parseDocSpec(testval['docspec']))
        self.assertEqual(testval['expected'][1:], result)

        # Test error conditions to make sure they are handled correctly.
        testvals = [
            # Missing entity ID.
            {
                'docspec':
"""
---
Classes:
    - descendants: 1
""",
                'errorstr': 'No entity ID was provided'
            },
            # Invalid ID.
            {
                'docspec':
"""
---
Classes:
    - ID: OBTO:INVALID
""",
                'errorstr': 'No entity with the ID ".*" could be found'
            },
            # Invalid "descendants" values.
            {
                'docspec':
"""
---
Classes:
    - ID: OBTO:0010
      descendants: invalid
""",
                'errorstr': 'Invalid value for "descendants" directive'
            },
            {
                'docspec':
"""
---
Classes:
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

