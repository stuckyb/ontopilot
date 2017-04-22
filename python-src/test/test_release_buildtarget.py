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
from ontopilot.ontoconfig import OntoConfig
from ontopilot.release_buildtarget import ReleaseBuildTarget
from ontopilot.release_buildtarget import _ArgsType, FileInfo
import unittest
import os.path
from collections import namedtuple
import datetime

# Java imports.


# Define a simple "struct" type for simulating command-line arguments.
ArgsStruct = namedtuple(
    'ArgsStruct', 'merge_imports, reason, no_def_expand, release_date'
)

# Define another simple "struct" type for testing _ArgsType.  Don't use
# namedtuple here because we want the attributes to be read/write.
class TestStruct:
    pass


class TestArgsType(unittest.TestCase):
    """
    Tests the functionality of the supporting class _ArgsType.
    """
    def test_ArgsType(self):
        # Tests that the object attribute copy works as expected.
        orig = TestStruct()
        orig.prop1 = 1
        orig.prop2 = 'two'

        copy = _ArgsType(orig)
        self.assertTrue(hasattr(copy, 'prop1'))
        self.assertTrue(hasattr(copy, 'prop2'))
        self.assertEqual(1, copy.prop1)
        self.assertEqual('two', copy.prop2)

        # Verify that the copy is a deep copy.
        copy.prop1 = 2
        copy.prop2 = 'three'
        self.assertEqual(2, copy.prop1)
        self.assertEqual('three', copy.prop2)
        self.assertEqual(1, orig.prop1)
        self.assertEqual('two', orig.prop2)


class TestReleaseBuildTarget(unittest.TestCase):
    """
    Tests the supporting methods of the ReleaseBuildTarget class.
    """
    def setUp(self):
        self.base_iri = 'http://release.base.iri/for/ont'

        self.oc = OntoConfig('test_data/project.conf')
        self.oc.set('Ontology', 'termsdir', '.')
        self.oc.set('IRIs', 'release_base_iri', self.base_iri)

        # We need to set the imports source location so that the
        # ImportsBuildTarget dependency of OntoBuildTarget will initialize
        # without error.
        self.oc.set('Imports', 'imports_src', 'imports_src/')

        self.td_path = os.path.abspath('test_data/')

        args = ArgsStruct(
            merge_imports=False, reason=False, no_def_expand=False,
            release_date=''
        )
        self.rbt = ReleaseBuildTarget(args, False, self.oc)

    def test_generateReleaseDirPath(self):
        # Check the default, automatically generated date string.
        datestr = datetime.date.today().isoformat()
        release_path = self.td_path + '/releases/' + datestr
        self.assertEqual(release_path, self.rbt._generateReleaseDirPath(''))

        # Check a custom date string.
        datestr = '2017-01-01'
        release_path = self.td_path + '/releases/' + datestr
        self.assertEqual(release_path, self.rbt._generateReleaseDirPath(datestr))

        # Check an invalid date string.
        with self.assertRaisesRegexp(
            ValueError, 'The custom release date string, .*, is invalid.'
        ):
            self.rbt._generateReleaseDirPath('2017-01-32')

    def test_generateImportFileInfo(self):        
        sourcepath = self.td_path + '/imports/import.owl'
        oldiri = 'http://old.iri/for/import'

        datestr = datetime.date.today().isoformat()
        relpath = '/releases/' + datestr + '/imports/import.owl'
        exp = FileInfo(
            sourcepath=sourcepath, destpath=self.td_path + relpath,
            oldIRI=oldiri, destIRI=self.base_iri + '/imports/import.owl',
            versionIRI=self.base_iri + relpath
        )

        self.assertEqual(
            exp, self.rbt._generateImportFileInfo(sourcepath, oldiri)
        )

    def test_generateOntologyFileInfo(self):
        # Set a custom main ontology IRI.
        custom_iri = 'http://a.custom.main/ont/iri/ontfile.owl'
        self.oc.set('IRIs', 'release_ontology_IRI', custom_iri)

        # Generate the expected relative release directory path.
        datestr = datetime.date.today().isoformat()
        relpath = '/releases/' + datestr

        # Generate an expected FileInfo object for each ontology file name
        # suffix.
        sourcepath = self.td_path + '/ontsrc/demo.owl'
        testvals = {}
        for suffix in ('', '-raw'):
            ofname = '/ontname' + suffix + '.owl'
            testvals[suffix] = FileInfo(
                sourcepath=sourcepath,
                destpath=self.td_path + relpath + ofname, oldIRI='',
                destIRI=self.base_iri + ofname,
                versionIRI=self.base_iri + relpath + ofname
            )

        for suffix in testvals:
            self.assertEqual(
                testvals[suffix],
                self.rbt._generateOntologyFileInfo(sourcepath, suffix, False)
            )

        # Test the custom main ontology IRI.
        exp = FileInfo(
            sourcepath=sourcepath,
            destpath=self.td_path + relpath + '/ontname.owl', oldIRI='',
            destIRI=custom_iri,
            versionIRI=self.base_iri + relpath + '/ontname.owl'
        )

        self.assertEqual(
            exp,
            self.rbt._generateOntologyFileInfo(sourcepath, '', True)
        )

