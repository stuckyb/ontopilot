# Copyright (C) 2016 Brian J. Stucky
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
from ontobuilder.ontoconfig import ConfigError, OntoConfig
import unittest
from testfixtures import LogCapture
import os.path

# Java imports.
from org.semanticweb.owlapi.model import IRI


class TestOntoConfig(unittest.TestCase):
    """
    Tests the OntoConfig class.
    """
    def setUp(self):
        self.ontIRIstr = 'https://a.sample.iri/to/ontology/ontname.owl'
        self.termsfiles = ['terms_1.csv', 'terms_2.csv']
        self.mod_baseIRI = 'https://a.sample.iri/to/imports'

        self.oc = OntoConfig('test_data/config.conf')

        self.td_path = os.path.abspath('test_data/')

    def test_getCustom(self):
        # Test an extant option.
        self.assertEqual(
            self.ontIRIstr, self.oc.getCustom('Main', 'ontologyIRI')
        )

        # Test an extant option that is empty.
        self.oc.set('Main', 'optstr', '    \t  ')
        self.assertEqual(
            'defaultval', self.oc.getCustom('Main', 'optstr', 'defaultval')
        )

        # Test a nonexistent option.
        self.assertEqual(
            'defaultval', self.oc.getCustom('Main', 'optstr2', 'defaultval')
        )

    def test_checkConfig(self):
        """
        Verifies that basic configuration file errors are correctly detected.
        """
        # Start with an empty configuration.
        self.oc.remove_section('Main')

        with self.assertRaisesRegexp(
            ConfigError, 'The "Main" section was not found'
        ):
            self.oc.checkConfig()

        self.oc.add_section('Main')

        # This should not raise an exception.
        self.oc.checkConfig()

    def test_getOntologyIRI(self):
        self.assertEqual(self.ontIRIstr, self.oc.getOntologyIRI())

        # Verify that a missing IRI is detected.
        self.oc.remove_option('Main', 'ontologyIRI')
        with self.assertRaisesRegexp(
            ConfigError, 'No ontology IRI was provided.'
        ):
            self.oc.getOntologyIRI()

        # Verify that a blank IRI string is detected.
        self.oc.set('Main', 'ontologyIRI', '  \t  ')
        with self.assertRaisesRegexp(
            ConfigError, 'No ontology IRI was provided.'
        ):
            self.oc.getOntologyIRI()

        # Verify that an invalid IRI string is detected.
        self.oc.set('Main', 'ontologyIRI', '/not/an/absolute/IRI')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid ontology IRI string'
        ):
            self.oc.getOntologyIRI()

    def test_getTermsFilePaths(self):
        # Check the default terms file location.
        exp = [self.td_path + '/src/terms/' + fname for fname in self.termsfiles]
        self.assertEqual(exp, self.oc.getTermsFilePaths())

        # Check a custom relative path terms file location.
        relpath = 'a/rel/path'
        self.oc.set('Ontology', 'termsdir', relpath)
        abspath = self.td_path + '/' + relpath
        exp = [abspath + '/' + fname for fname in self.termsfiles]
        self.assertEqual(exp, self.oc.getTermsFilePaths())

        # Check a custom absolute path terms file location.
        abspath = '/an/absolute/path'
        self.oc.set('Ontology', 'termsdir', abspath)
        exp = [abspath + '/' + fname for fname in self.termsfiles]
        self.assertEqual(exp, self.oc.getTermsFilePaths())

        # Verify that a missing termsfiles setting is detected.
        self.oc.remove_option('Main', 'termsfiles')
        with self.assertRaisesRegexp(
            ConfigError, 'No ontology entities/terms files were provided.'
        ):
            self.oc.getTermsFilePaths()

        # Verify that a blank termsfiles setting is detected.
        self.oc.set('Main', 'termsfiles', '   \t  ')
        with self.assertRaisesRegexp(
            ConfigError, 'No ontology entities/terms files were provided.'
        ):
            self.oc.getTermsFilePaths()

    def test_getAbsPath(self):
        # Test an absolute input path.
        abspath = '/an/absolute/path'
        self.assertEqual(abspath, self.oc._getAbsPath(abspath))

        # Test a relative input path.
        relpath = 'a/rel/path'
        self.assertEqual(
            self.td_path + '/' + relpath, self.oc._getAbsPath(relpath)
        )

    def test_getOntFileBase(self):
        self.assertEqual('ontname', self.oc._getOntFileBase())

    def test_getOntologyFileName(self):
        # Test extracting the file name from the ontology's IRI.
        self.assertEqual('ontname.owl', self.oc.getOntologyFileName())

        # Test that an IRI without a filename is correctly detected.
        self.oc.set('Main', 'ontologyIRI', 'https://a.sample.iri/to/ontology/')
        with self.assertRaisesRegexp(
            ConfigError, 'An ontology file name was not provided'
        ):
            self.oc.getOntologyFileName()

        # Test an explicitly provided file name.
        self.oc.set('Ontology', 'ontology_file', 'custom.owl')
        self.assertEqual('custom.owl', self.oc.getOntologyFileName())

    def test_getBaseOntologyPath(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/src/ontname-base.owl',
            self.oc.getBaseOntologyPath()
        )

        # Test a custom relative file path and name.
        relpath = 'rel/path/custom-base.owl'
        self.oc.set('Ontology', 'base_ontology_file', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getBaseOntologyPath()
        )

        # Test a custom absolute file path and name.
        abspath = '/an/absolute/path/custom-base.owl'
        self.oc.set('Ontology', 'base_ontology_file', abspath)
        self.assertEqual(abspath, self.oc.getBaseOntologyPath())

    def test_getImportsDir(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/src/imports',
            self.oc.getImportsDir()
        )

        # Test a custom relative file path.
        relpath = 'rel/path/imports'
        self.oc.set('Imports', 'importsdir', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getImportsDir()
        )

        # Test a custom absolute file path.
        abspath = '/an/absolute/path/imports'
        self.oc.set('Imports', 'importsdir', abspath)
        self.assertEqual(abspath, self.oc.getImportsDir())

    def test_getTopImportsFilePath(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/src/imports/imported_ontologies.csv',
            self.oc.getTopImportsFilePath()
        )

        # Test a custom relative file path and name.
        relpath = 'rel/path/imports/imports.csv'
        self.oc.set('Imports', 'top_importsfile', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getTopImportsFilePath()
        )

        # Test a custom absolute file path and name.
        abspath = '/an/absolute/path/imports/imports.csv'
        self.oc.set('Imports', 'top_importsfile', abspath)
        self.assertEqual(abspath, self.oc.getTopImportsFilePath())

    def test_getModulesBaseIRI(self):
        # Check auto-generating a modules base IRI.
        self.assertEqual(
            'https://a.sample.iri/to/imports', self.oc.getModulesBaseIRI()
        )

        # Check an ontology IRI that can't be converted.
        self.oc.set('Main', 'ontologyIRI', 'https://a.sample.iri/non/default/ontology.owl')
        with self.assertRaisesRegexp(
            ConfigError, 'Unable to automatically generate a suitable base IRI'
        ):
            self.oc.getModulesBaseIRI()

        # Check an explicitly provided IRI.
        altIRI = 'https://a.sample.iri/alt/imports/path'
        self.oc.set('Imports', 'mod_baseIRI', altIRI)
        self.assertEqual(altIRI, self.oc.getModulesBaseIRI())

    def test_getImportModSuffix(self):
        # Check an auto-generated suffix.
        self.assertEqual(
            '_ontname_import_module.owl', self.oc.getImportModSuffix()
        )

        # Check an explicitly provided suffix.
        suffix = '_new_suffix.owl'
        self.oc.set('Imports', 'import_mod_suffix', suffix)
        self.assertEqual(suffix, self.oc.getImportModSuffix())

