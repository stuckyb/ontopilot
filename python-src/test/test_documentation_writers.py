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
from ontopilot.documenter import Documenter
from ontopilot.documentation_writers import getDocumentationWriter
from ontopilot.documentation_writers import MarkdownWriter, HTMLWriter
from ontopilot.ontology import Ontology
import unittest
import StringIO
#from testfixtures import LogCapture

# Java imports.


class Test_GetDocumentationWriter(unittest.TestCase):
    """
    Tests the getDocumentationWriter factory function.
    """
    def setUp(self):
        pass

    def test_getDocumentationWriter(self):
        self.assertIsInstance(
            getDocumentationWriter('Markdown'), MarkdownWriter
        )
        self.assertIsInstance(getDocumentationWriter('HTML'), HTMLWriter)

        # Verify that format string matching is not case sensitive.
        self.assertIsInstance(getDocumentationWriter('html'), HTMLWriter)

        with self.assertRaisesRegexp(
            RuntimeError, 'Unrecognized documentation format string'
        ):
            getDocumentationWriter('invalid')


class Test_MarkdownWriter(unittest.TestCase):
    """
    Tests the MarkdownWriter class.  No attempt is made to cover every possible
    input data structure variation, or even most of them.  Instead, it
    basically just confirms that the converter is working and producing correct
    output for a sample input document.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.doc = Documenter(self.ont)

    def test_write(self):
        testvals = [
            {
                'docspec': """
# Test documentation

## Classes

- ID: OBITO:0001
  descendants: 1
""",
                'expected': """
# Test documentation

## Classes

* ### imported test class 1

  OBO ID: OBITO:0001

  IRI: http://purl.obolibrary.org/obo/OBITO_0001

    * ### test class 1

      OBO ID: OBTO:0010

      IRI: http://purl.obolibrary.org/obo/OBTO_0010

    * ### test class 2

      OBO ID: OBTO:0011

      IRI: http://purl.obolibrary.org/obo/OBTO_0011

    * ### test class 3

      OBO ID: OBTO:0012

      IRI: http://purl.obolibrary.org/obo/OBTO_0012


"""
            },
            # A document specification that includes UTF-8 non-ASCI text.
            {
                'docspec': """
## UTF-8 Greek alpha: \xce\xb1
""",
                'expected': """
## UTF-8 Greek alpha: \xce\xb1
"""
            }
        ]

        self.doc.setWriter(MarkdownWriter())

        for testval in testvals:
            docspec = testval['docspec']
            expected = testval['expected']
            
            strbuf = StringIO.StringIO()
            self.doc.document(docspec, strbuf)
            result = strbuf.getvalue()
            strbuf.close()

            self.assertEqual(expected, result)


class Test_HTMLWriter(unittest.TestCase):
    """
    Tests the HTMLWriter class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.doc = Documenter(self.ont)

        self.hw = HTMLWriter()

    def test_getUniqueValue(self):
        coll = ['a', 'b', 'b-1', 'c-']

        testvals = [
            {
                'text': '',
                'expected': '-1'
            },
            {
                'text': 'd',
                'expected': 'd'
            },
            {
                'text': 'a',
                'expected': 'a-1'
            },
            {
                'text': 'b',
                'expected': 'b-2'
            },
            {
                'text': 'c-',
                'expected': 'c--1'
            }
        ]

        for testval in testvals:
            self.assertEqual(
                testval['expected'],
                self.hw._getUniqueValue(testval['text'], coll)
            )

    def test_getIDText(self):
        # String conversion tests.
        testvals = [
            {
                'text': '',
                'expected': '-1'
            },
            {
                'text': '- -- \t\n',
                'expected': '-'
            },
            {
                'text': 'will-not_be-changed',
                'expected': 'will-not_be-changed'
            },
            {
                'text': '(w*&il|}[]l be\tch@anged',
                'expected': 'will-be-changed'
            },
            {
                'text': 'Case-Will-Change',
                'expected': 'case-will-change'
            },
            {
                # Includes a unicode lower-case Greek alpha.
                'text': unicode('unicode: \xce\xb1', 'utf-8'),
                'expected': 'unicode-'
            }
        ]

        for testval in testvals:
            self.assertEqual(
                testval['expected'], self.hw._getIDText(testval['text'], set())
            )

        # Test unique ID generation.
        usedIDs = {
            'ida', 'idb', 'idb-1', 'idc', 'idc-2', 'idd', 'idd-1', 'idd-2'
        }

        testvals = [
            {
                'text': 'ide',
                'expected': 'ide'
            },
            {
                'text': 'ida',
                'expected': 'ida-1'
            },
            {
                'text': 'idb',
                'expected': 'idb-2'
            },
            {
                'text': 'idc',
                'expected': 'idc-1'
            },
            {
                'text': 'idd',
                'expected': 'idd-3'
            }
        ]

        for testval in testvals:
            self.assertEqual(
                testval['expected'],
                self.hw._getIDText(testval['text'], usedIDs)
            )

    def _printResultsComparison(self, expected, result):
        """
        Prints a line-by-line comparison of an expected text string and a
        result text string.
        """
        for e_line, r_line in zip(
            expected.splitlines(), result.splitlines()
        ):
            if e_line != r_line:
                print 'MISMATCH:'
            print 'exp: "{0}"\nres: "{1}"'.format(e_line, r_line)

    def test_write(self):
        testvals = [
            # A document specification that includes two Markdown sections with
            # h2 headers, separated by an entities section, followed by another
            # entities section.  One of the h2 headers has content that will
            # generate an ID that conflicts with a reserved ID, to verify that
            # reserved IDs are properly preserved.
            {
                'docspec': """
# Test documentation

## First h2 header

## main

## Properties
- ID: OBTO:0020

## Classes

- ID: OBITO:0001
  descendants: 1
""",
                'expected': """
<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8" />
    <title>Test documentation</title>
    <link rel="stylesheet" type="text/css" href="documentation_styles.css" />
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <script src="navtree.js"></script>
</head>
<body>

<nav id="toc">
<h1>Table of Contents</h1>
<div id="toc_buttons">
    <div id="expand_all" class="top_toc_button">expand all</div>
    <div id="collapse_all" class="top_toc_button">collapse all</div>
</div>
<ul>
<li><a href="#first-h2-header">First h2 header</a>
</li>
<li><a href="#main-1">main</a>
</li>
<li><a href="#properties">Properties</a>
    <ul>
    <li><a href="#test-data-property-1">test data property 1</a></li>
    </ul>
</li>
<li><a href="#classes">Classes</a>
    <ul>
    <li><a href="#imported-test-class-1">imported test class 1</a>
        <ul>
        <li><a href="#test-class-1">test class 1</a></li>
        <li><a href="#test-class-2">test class 2</a></li>
        <li><a href="#test-class-3">test class 3</a></li>
        </ul>
    </li>
    </ul>
</li>
</ul>
</nav>

<main>
<h1>Test documentation</h1>

<h2 id="first-h2-header">First h2 header</h2>

<h2 id="main-1">main</h2>

<h2 id="properties">Properties</h2>
<ul class="entity_list">
<li>
    <h3 id="test-data-property-1">test data property 1</h3>
    <p>OBO ID: OBTO:0020</p>
    <p>IRI: http://purl.obolibrary.org/obo/OBTO_0020</p>
</li>
</ul>

<h2 id="classes">Classes</h2>
<ul class="entity_list">
<li>
    <h3 id="imported-test-class-1">imported test class 1</h3>
    <p>OBO ID: OBITO:0001</p>
    <p>IRI: http://purl.obolibrary.org/obo/OBITO_0001</p>
    <ul class="entity_list">
    <li>
        <h3 id="test-class-1">test class 1</h3>
        <p>OBO ID: OBTO:0010</p>
        <p>IRI: http://purl.obolibrary.org/obo/OBTO_0010</p>
    </li>
    <li>
        <h3 id="test-class-2">test class 2</h3>
        <p>OBO ID: OBTO:0011</p>
        <p>IRI: http://purl.obolibrary.org/obo/OBTO_0011</p>
    </li>
    <li>
        <h3 id="test-class-3">test class 3</h3>
        <p>OBO ID: OBTO:0012</p>
        <p>IRI: http://purl.obolibrary.org/obo/OBTO_0012</p>
    </li>
    </ul>
</li>
</ul>

</main>
</body>
</html>"""
            },
            # A document specification that includes UTF-8 non-ASCI text.
            {
                'docspec': """
## UTF-8 Greek alpha: \xce\xb1
""",
                'expected': """
<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8" />
    <title></title>
    <link rel="stylesheet" type="text/css" href="documentation_styles.css" />
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <script src="navtree.js"></script>
</head>
<body>

<nav id="toc">
<h1>Table of Contents</h1>
<div id="toc_buttons">
    <div id="expand_all" class="top_toc_button">expand all</div>
    <div id="collapse_all" class="top_toc_button">collapse all</div>
</div>
<ul>
<li><a href="#utf-8-greek-alpha-">UTF-8 Greek alpha: \xce\xb1</a>
</li>
</ul>
</nav>

<main>
<h2 id="utf-8-greek-alpha-">UTF-8 Greek alpha: \xce\xb1</h2>
</main>
</body>
</html>"""
            }
        ]

        self.doc.setWriter(HTMLWriter())

        for testval in testvals:
            docspec = testval['docspec']
            expected = testval['expected']

            strbuf = StringIO.StringIO()
            self.doc.document(docspec, strbuf)
            result = strbuf.getvalue()
            strbuf.close()

            #self._printResultsComparison(expected[1:], result)
    
            self.assertEqual(expected[1:], result)

        # Create a cycle in the descendant relationships by making OBITO:0001 a
        # subclass of OBTO:0010, and make a polyhierarchy by making OBTO:0012 a
        # subclass of OBTO:0011.  The class structure should look like this:
        #
        # OBTO:0090
        # OBITO:0001
        # |--- OBTO:0010
        # |    |--- OBITO:0001
        # |--- OBTO:0011
        # |    |--- OBTO:0012
        # |--- OBTO:0012
        ent = self.ont.getExistingClass('OBTO:0010')
        ent.addSubclass('OBITO:0001')
        ent = self.ont.getExistingClass('OBTO:0011')
        ent.addSubclass('OBTO:0012')

        # Make sure the cycle doesn't "trap" the documentation generating
        # algorithms and that the polyhierarchy is handled correctly.
        docspec = """
## Classes
- ID: OBITO:0001
  descendants: all
"""
        expected = """
<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta charset="utf-8" />
    <title></title>
    <link rel="stylesheet" type="text/css" href="documentation_styles.css" />
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
    <script src="navtree.js"></script>
</head>
<body>

<nav id="toc">
<h1>Table of Contents</h1>
<div id="toc_buttons">
    <div id="expand_all" class="top_toc_button">expand all</div>
    <div id="collapse_all" class="top_toc_button">collapse all</div>
</div>
<ul>
<li><a href="#classes">Classes</a>
    <ul>
    <li><a href="#imported-test-class-1">imported test class 1</a>
        <ul>
        <li><a href="#test-class-1">test class 1</a>
            <ul>
            <li><a href="#imported-test-class-1">imported test class 1</a></li>
            </ul>
        </li>
        <li><a href="#test-class-2">test class 2</a>
            <ul>
            <li><a href="#test-class-3">test class 3</a></li>
            </ul>
        </li>
        <li><a href="#test-class-3">test class 3</a></li>
        </ul>
    </li>
    </ul>
</li>
</ul>
</nav>

<main>
<h2 id="classes">Classes</h2>
<ul class="entity_list">
<li>
    <h3 id="imported-test-class-1">imported test class 1</h3>
    <p>OBO ID: OBITO:0001</p>
    <p>IRI: http://purl.obolibrary.org/obo/OBITO_0001</p>
    <ul class="entity_list">
    <li>
        <h3 id="test-class-1">test class 1</h3>
        <p>OBO ID: OBTO:0010</p>
        <p>IRI: http://purl.obolibrary.org/obo/OBTO_0010</p>
        <ul class="entity_list">
        <li>
            <h3>imported test class 1</h3>
            <p>OBO ID: OBITO:0001</p>
            <p>IRI: http://purl.obolibrary.org/obo/OBITO_0001</p>
        </li>
        </ul>
    </li>
    <li>
        <h3 id="test-class-2">test class 2</h3>
        <p>OBO ID: OBTO:0011</p>
        <p>IRI: http://purl.obolibrary.org/obo/OBTO_0011</p>
        <ul class="entity_list">
        <li>
            <h3 id="test-class-3">test class 3</h3>
            <p>OBO ID: OBTO:0012</p>
            <p>IRI: http://purl.obolibrary.org/obo/OBTO_0012</p>
        </li>
        </ul>
    </li>
    <li>
        <h3>test class 3</h3>
        <p>OBO ID: OBTO:0012</p>
        <p>IRI: http://purl.obolibrary.org/obo/OBTO_0012</p>
    </li>
    </ul>
</li>
</ul>

</main>
</body>
</html>"""

        strbuf = StringIO.StringIO()
        self.doc.document(docspec, strbuf)
        result = strbuf.getvalue()
        strbuf.close()

        #self._printResultsComparison(expected[1:], result)

        self.assertEqual(expected[1:], result)

