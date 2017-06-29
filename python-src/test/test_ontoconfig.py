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
from ontopilot.ontoconfig import ConfigError, OntoConfig
import unittest
from testfixtures import LogCapture
import os.path

# Java imports.


class TestOntoConfig(unittest.TestCase):
    """
    Tests the OntoConfig class.
    """
    def setUp(self):
        self.termsfiles = ['terms_1.csv', 'terms_2.csv']
        self.mod_baseIRI = 'https://a.sample.iri/to/imports'

        self.oc = OntoConfig('test_data/project.conf')

        self.td_path = os.path.abspath('test_data/')

        # If we define custom failure messages, append them to the end of the
        # default failure message.
        self.longMessage = True

    def test_getCustom(self):
        # Test an extant option.
        self.assertEqual(
            'ontology/ontname.owl',
            self.oc.getCustom('Ontology', 'ontology_file')
        )

        # Test an extant option that is empty.
        self.oc.set('Ontology', 'optstr', '    \t  ')
        self.assertEqual(
            'defaultval', self.oc.getCustom('Ontology', 'optstr', 'defaultval')
        )

        # Test a nonexistent option.
        self.assertEqual(
            'defaultval', self.oc.getCustom('Ontology', 'optstr2', 'defaultval')
        )

    def test_getConfigFilePath(self):
        self.assertEqual(
            self.td_path + '/project.conf',
            self.oc.getConfigFilePath()
        )

    def test_constructWithoutConfFile(self):
        """
        Tests the functionality of OntoConfig when no config file is provided.
        In this case, OntoConfig should simply return default values for
        configuration settings.
        """
        oc = OntoConfig()

        # Check a few settings to make sure we're getting back default values.
        self.assertEqual('HermiT', oc.getReasonerStr())
        self.assertFalse(oc.getAnnotateInferred())

    def test_getAbsPath(self):
        # Test an absolute input path.
        abspath = '/an/absolute/path'
        self.assertEqual(abspath, self.oc._getAbsPath(abspath))

        # Test a relative input path.
        relpath = 'a/rel/path'
        self.assertEqual(
            self.td_path + '/' + relpath, self.oc._getAbsPath(relpath)
        )

    def test_isSubpathInPath(self):
        testvals = [
            {'exp': False, 'ppath': '', 'spath': ''},
            {'exp': False, 'ppath': '/', 'spath': '/'},
            {'exp': False, 'ppath': '', 'spath': '/test/path'},
            {'exp': False, 'ppath': '/test/path', 'spath': '/test/path'},
            {'exp': False, 'ppath': '/test/path', 'spath': '/test/path/'},
            {'exp': False, 'ppath': '/test/path/', 'spath': '/test/path'},
            {'exp': False, 'ppath': '/test/path/', 'spath': '/test/path/'},
            {'exp': False, 'ppath': '/test/path/long', 'spath': '/test/path'},
            {'exp': False, 'ppath': '/test/path', 'spath': '/alt/path/long'},
            {'exp': True, 'ppath': '/', 'spath': '/test/path/long'},
            {'exp': True, 'ppath': '/test/path', 'spath': '/test/path/long'},
            # A case for which simple string prefix checking would give the
            # wrong answer.
            {
                'exp': False,
                'ppath': '/test/path', 'spath': '/test/pathly/long'
            },
            {'exp': False, 'ppath': 'relpath', 'spath': 'relpath'},
            {'exp': True, 'ppath': 'relpath', 'spath': 'relpath/long'},
        ]

        for testval in testvals:
            self.assertEqual(
                testval['exp'],
                self.oc._isSubpathInPath(testval['ppath'], testval['spath']),
                msg='ppath: "{0}", spath: "{1}".'.format(
                    testval['ppath'], testval['spath']
                )
            )

    def test_getOntFileBase(self):
        self.assertEqual('ontname', self.oc.getOntFileBase())

    def test_getDevBaseIRI(self):
        # Test the default, automatically generated local file system IRI.
        self.assertEqual(
            'file://localhost' + self.td_path, self.oc.getDevBaseIRI()
        )

        # Test a custom IRI.
        iristr = 'http://custom.iri/path'
        self.oc.set('IRIs', 'dev_base_IRI', iristr)
        self.assertEqual(iristr, self.oc.getDevBaseIRI())

        # Verify that an invalid IRI string is detected.
        self.oc.set('IRIs', 'dev_base_IRI', '/not/an/absolute/IRI')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid development base IRI string'
        ):
            self.oc.getDevBaseIRI()

    def test_getReleaseBaseIRI(self):
        # Test the default IRI.
        self.assertEqual(
            self.oc.getDevBaseIRI(), self.oc.getReleaseBaseIRI()
        )

        # Test a custom IRI.
        iristr = 'http://custom.iri/path'
        self.oc.set('IRIs', 'release_base_IRI', iristr)
        self.assertEqual(iristr, self.oc.getReleaseBaseIRI())

        # Verify that an invalid IRI string is detected.
        self.oc.set('IRIs', 'release_base_IRI', '/not/an/absolute/IRI')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid release base IRI string'
        ):
            self.oc.getReleaseBaseIRI()

    def test_generatePathIRI(self):
        baseIRI = 'http://custom.iri/dev/'

        # Test a relative path.
        pathstr = 'ontology/test.owl'
        self.assertEqual(
            baseIRI + pathstr, self.oc._generatePathIRI(pathstr, baseIRI)
        )

        # Test an absolute path.
        pathstr = self.td_path + '/ontology/test.owl'
        self.assertEqual(
            baseIRI + 'ontology/test.owl',
            self.oc._generatePathIRI(pathstr, baseIRI)
        )

        # Test a relative path that is outside the project directory.
        pathstr = '../ontology/test.owl'
        with self.assertRaisesRegexp(
            ConfigError, 'is not a subpath of the main project folder'
        ):
            self.oc._generatePathIRI(pathstr, baseIRI)

        # Test an absolute path that is outside the project directory.
        pathstr = '/ontology/test.owl'
        with self.assertRaisesRegexp(
            ConfigError, 'is not a subpath of the main project folder'
        ):
            self.oc._generatePathIRI(pathstr, baseIRI)

    def test_generateDevIRI(self):
        dev_iristr = 'http://custom.iri/dev/'
        self.oc.set('IRIs', 'dev_base_IRI', dev_iristr)

        pathstr = 'ontology/test.owl'
        self.assertEqual(
            dev_iristr + 'ontology/test.owl', self.oc.generateDevIRI(pathstr)
        )

    def test_generateReleaseIRI(self):
        release_iristr = 'http://custom.iri/release/'
        self.oc.set('IRIs', 'release_base_IRI', release_iristr)

        pathstr = 'ontology/test.owl'
        self.assertEqual(
            release_iristr + 'ontology/test.owl',
            self.oc.generateReleaseIRI(pathstr)
        )

    def test_getImportsDevBaseIRI(self):
        # Check the default compiled imports modules location.
        iristr = 'http://custom.iri/path'
        self.oc.set('IRIs', 'dev_base_IRI', iristr)
        self.assertEqual(
            iristr + '/imports', self.oc.getImportsDevBaseIRI()
        )

        # Check a custom compiled imports modules location.
        self.oc.set('Imports', 'imports_dir', 'custom/dir/')
        self.assertEqual(
            iristr + '/custom/dir', self.oc.getImportsDevBaseIRI()
        )

    def test_getReleaseOntologyIRI(self):
        # Test an automatically generated IRI.
        iristr = 'http://custom.iri/path'
        self.oc.set('IRIs', 'release_base_IRI', iristr)
        self.assertEqual(
            iristr + '/ontname.owl', self.oc.getReleaseOntologyIRI()
        )

        # Test a custom IRI.
        iristr = 'http://custom.iri/path/test.owl'
        self.oc.set('IRIs', 'release_ontology_IRI', iristr)
        self.assertEqual(iristr, self.oc.getReleaseOntologyIRI())

        # Verify that an invalid IRI string is detected.
        self.oc.set('IRIs', 'release_ontology_IRI', '/not/an/absolute/IRI')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid release ontology IRI string'
        ):
            self.oc.getReleaseOntologyIRI()

    def test_getOntologyFilePath(self):
        # Test an explicitly provided file name.
        self.assertEqual(
            os.path.join(self.td_path, 'ontology/ontname.owl'),
            self.oc.getOntologyFilePath()
        )

        # Test that a blank path is correctly detected.
        self.oc.set('Ontology', 'ontology_file', '')
        with self.assertRaisesRegexp(
            ConfigError, 'An ontology file name was not provided'
        ):
            self.oc.getOntologyFilePath()

        # Test that a path outside of the project directory is correctly
        # detected.
        self.oc.set('Ontology', 'ontology_file', '/home/ontname.owl')
        with self.assertRaisesRegexp(
            ConfigError,
            'The compiled ontology file path (.*) is not a subpath of the main project folder'
        ):
            self.oc.getOntologyFilePath()

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

    def test_getEntitySourceDir(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/src/entities',
            self.oc.getEntitySourceDir()
        )

        # Test a custom relative file path.
        relpath = 'rel/terms'
        self.oc.set('Ontology', 'entity_sourcedir', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getEntitySourceDir()
        )

        # Test a custom absolute file path.
        abspath = '/an/absolute/path/terms'
        self.oc.set('Ontology', 'entity_sourcedir', abspath)
        self.assertEqual(abspath, self.oc.getEntitySourceDir())

    def test_getEntitySourceFilePaths(self):
        # Check the default terms file location.
        exp = [
            self.td_path + '/src/entities/' + fname for fname in self.termsfiles
        ]
        self.assertEqual(exp, self.oc.getEntitySourceFilePaths())

        # Check a custom relative path terms file location.
        relpath = 'a/rel/path'
        self.oc.set('Ontology', 'entity_sourcedir', relpath)
        abspath = self.td_path + '/' + relpath
        exp = [abspath + '/' + fname for fname in self.termsfiles]
        self.assertEqual(exp, self.oc.getEntitySourceFilePaths())

        # Check a custom absolute path terms file location.
        abspath = '/an/absolute/path'
        self.oc.set('Ontology', 'entity_sourcedir', abspath)
        exp = [abspath + '/' + fname for fname in self.termsfiles]
        self.assertEqual(exp, self.oc.getEntitySourceFilePaths())

        # Verify that a missing termsfiles setting returns an empty list.
        self.oc.remove_option('Ontology', 'entity_sourcefiles')
        self.assertEqual([], self.oc.getEntitySourceFilePaths())

        # Verify that a blank termsfiles returns an empty list.
        self.oc.set('Ontology', 'termsfiles', '   \t  ')
        self.assertEqual([], self.oc.getEntitySourceFilePaths())

    def test_getDoInSourceBuilds(self):
        self.assertFalse(self.oc.getDoInSourceBuilds())

        self.oc.set('Build', 'insource_builds', 'false')
        self.assertFalse(self.oc.getDoInSourceBuilds())

        self.oc.set('Build', 'insource_builds', 'True')
        self.assertTrue(self.oc.getDoInSourceBuilds())

        self.oc.set('Build', 'insource_builds', 'true')
        self.assertTrue(self.oc.getDoInSourceBuilds())

        self.oc.set('Build', 'insource_builds', 'yes')
        self.assertTrue(self.oc.getDoInSourceBuilds())

    def test_getBuildDir(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/build',
            self.oc.getBuildDir()
        )

        # Test a custom relative file path.
        relpath = 'rel/build'
        self.oc.set('Build', 'builddir', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getBuildDir()
        )

        # Test a custom absolute file path.
        abspath = '/an/absolute/path/build'
        self.oc.set('Build', 'builddir', abspath)
        self.assertEqual(abspath, self.oc.getBuildDir())

    def test_getExpandEntityDefs(self):
        # Check the default value first.
        self.assertTrue(self.oc.getExpandEntityDefs())

        testvals = [
            {'exp': False, 'val': 'false'},
            {'exp': False, 'val': 'FALSE'},
            {'exp': True, 'val': 'True'},
            {'exp': True, 'val': 'true'},
            {'exp': True, 'val': 'yes'}
        ]

        for testval in testvals:
            self.oc.set('Build', 'expand_entity_defs', testval['val'])
            self.assertEqual(testval['exp'], self.oc.getExpandEntityDefs())

    def test_getImportsSrcDir(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/src/imports',
            self.oc.getImportsSrcDir()
        )

        # Test a custom relative file path.
        relpath = 'rel/path/imports'
        self.oc.set('Imports', 'imports_src', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getImportsSrcDir()
        )

        # Test a custom absolute file path.
        abspath = '/an/absolute/path/imports'
        self.oc.set('Imports', 'imports_src', abspath)
        self.assertEqual(abspath, self.oc.getImportsSrcDir())

    def test_getImportsDir(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/imports',
            self.oc.getImportsDir()
        )

        # Test a custom relative file path.
        relpath = 'rel/path/imports'
        self.oc.set('Imports', 'imports_dir', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getImportsDir()
        )

        # Test that a path outside of the project directory is correctly
        # detected.
        self.oc.set('Imports', 'imports_dir', '/home/imports')
        with self.assertRaisesRegexp(
            ConfigError,
            'The compiled imports modules folder (.*) is not a subpath of the main project folder'
        ):
            self.oc.getImportsDir()

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

    def test_getImportModSuffix(self):
        # Check an auto-generated suffix.
        self.assertEqual(
            '_ontname_import_module.owl', self.oc.getImportModSuffix()
        )

        # Check an explicitly provided suffix.
        suffix = '_new_suffix.owl'
        self.oc.set('Imports', 'import_mod_suffix', suffix)
        self.assertEqual(suffix, self.oc.getImportModSuffix())

    def test_getReasonerStr(self):
        # Check the default value.
        self.assertEqual('HermiT', self.oc.getReasonerStr())

        # Verify that reasoner strings are not case sensitive.  If matching
        # were case sensitive, than at least one of the following would throw
        # an exception.
        self.oc.set('Reasoning', 'reasoner', 'HERMIT')
        self.assertEqual('HERMIT', self.oc.getReasonerStr())
        self.oc.set('Reasoning', 'reasoner', 'hermit')
        self.assertEqual('hermit', self.oc.getReasonerStr())

        # Verify that invalid strings are properly handled.
        self.oc.set('Reasoning', 'reasoner', 'invalid')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid value for the "reasoner" setting'
        ):
            self.oc.getReasonerStr()

    def test_getInferenceTypeStrs(self):
        # Check the default value.
        exp_strs = [
            'subclasses', 'equivalent classes', 'types', 'subdata properties',
            'subobject properties'
        ]
        self.oc.set('Reasoning', 'inferences', '')
        self.assertEqual(exp_strs, self.oc.getInferenceTypeStrs())

        # Verify that empty type strings are ignored.
        self.oc.set('Reasoning', 'inferences', ',')
        self.assertEqual(exp_strs, self.oc.getInferenceTypeStrs())
        self.oc.set('Reasoning', 'inferences', 'subclasses,')
        self.assertEqual(['subclasses'], self.oc.getInferenceTypeStrs())

        # Verify that inference type strings are not case sensitive.  If matching
        # were case sensitive, than at least one of the following would throw
        # an exception.
        self.oc.set('Reasoning', 'inferences', 'SUBCLASSES')
        self.assertEqual(['SUBCLASSES'], self.oc.getInferenceTypeStrs())
        self.oc.set('Reasoning', 'inferences', 'subclasses')
        self.assertEqual(['subclasses'], self.oc.getInferenceTypeStrs())

        # Verify that invalid type strings are properly handled.
        self.oc.set('Reasoning', 'inferences', 'subclasses, invalid')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid inference type for the "inferences" setting'
        ):
            self.oc.getInferenceTypeStrs()

    def test_getAnnotateInferred(self):
        self.assertFalse(self.oc.getAnnotateInferred())

        self.oc.set('Reasoning', 'annotate_inferred', 'false')
        self.assertFalse(self.oc.getAnnotateInferred())

        self.oc.set('Reasoning', 'annotate_inferred', 'True')
        self.assertTrue(self.oc.getAnnotateInferred())

        self.oc.set('Reasoning', 'annotate_inferred', 'true')
        self.assertTrue(self.oc.getAnnotateInferred())

        self.oc.set('Reasoning', 'annotate_inferred', 'yes')
        self.assertTrue(self.oc.getAnnotateInferred())

    def test_getPreprocessInverses(self):
        self.assertFalse(self.oc.getPreprocessInverses())

        self.oc.set('Reasoning', 'preprocess_inverses', 'false')
        self.assertFalse(self.oc.getPreprocessInverses())

        self.oc.set('Reasoning', 'preprocess_inverses', 'true')
        self.assertTrue(self.oc.getPreprocessInverses())

    def test_getExcludedTypesFile(self):
        # Test the default case.
        self.assertEqual('', self.oc.getExcludedTypesFile())

        # Test a custom relative file path.
        relpath = 'rel/path/excluded.csv'
        self.oc.set('Reasoning', 'excluded_types_file', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getExcludedTypesFile()
        )

        # Test a custom absolute file path.
        abspath = '/an/absolute/path/excluded.csv'
        self.oc.set('Reasoning', 'excluded_types_file', abspath)
        self.assertEqual(abspath, self.oc.getExcludedTypesFile())

    def test_getAnnotateMerged(self):
        self.assertTrue(self.oc.getAnnotateMerged())

        self.oc.set('Imports', 'annotate_merged', 'false')
        self.assertFalse(self.oc.getAnnotateMerged())

        self.oc.set('Imports', 'annotate_merged', 'true')
        self.assertTrue(self.oc.getAnnotateMerged())

    def test_getOutputFormat(self):
        # Check the default value.
        self.assertEqual('RDF/XML', self.oc.getOutputFormat())

        # Verify that output format strings are not case sensitive.  If
        # matching were case sensitive, than at least one of the following
        # would throw an exception.
        self.oc.set('Build', 'output_format', 'TURTLE')
        self.assertEqual('TURTLE', self.oc.getOutputFormat())
        self.oc.set('Build', 'output_format', 'turtle')
        self.assertEqual('turtle', self.oc.getOutputFormat())

        # Verify that invalid strings are properly handled.
        self.oc.set('Build', 'output_format', 'invalid')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid value for the "output_format" setting'
        ):
            self.oc.getOutputFormat()

    def test_getDocSpecificationFile(self):
        # Test the default case.
        expected = self.td_path + '/src/doc_specification.txt'
        self.assertEqual(expected, self.oc.getDocSpecificationFile())

        # Test a custom relative file path.
        relpath = 'rel/path/docspec.txt'
        self.oc.set('Documentation', 'doc_specification', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath,
            self.oc.getDocSpecificationFile()
        )

        # Test a custom absolute file path.
        abspath = '/an/absolute/path/docspec.txt'
        self.oc.set('Documentation', 'doc_specification', abspath)
        self.assertEqual(abspath, self.oc.getDocSpecificationFile())

    def test_getDocsFilePath(self):
        # Test the default case.
        self.assertEqual(
            self.td_path + '/documentation/ontname',
            self.oc.getDocsFilePath()
        )

        # Test a custom relative file path and name.
        relpath = 'rel/path/docs/docbase'
        self.oc.set('Documentation', 'docs_file_path', relpath)
        self.assertEqual(
            self.td_path + '/' + relpath, self.oc.getDocsFilePath()
        )

        # Test a custom absolute file path and name.
        abspath = '/an/absolute/path/docs/docbase'
        self.oc.set('Documentation', 'docs_file_path', abspath)
        self.assertEqual(abspath, self.oc.getDocsFilePath())

        self.oc.set('Documentation', 'docs_file_path', '/')
        with self.assertRaisesRegexp(
            ConfigError, 'Invalid value for the "docs_file_path" setting'
        ):
            self.oc.getDocsFilePath()

    def test_getDocFormats(self):
        # Check the default value.
        exp_strs = ['HTML']
        self.oc.set('Documentation', 'doc_formats', '')
        self.assertEqual(exp_strs, self.oc.getDocFormats())

        # Verify that empty type strings are ignored.
        self.oc.set('Documentation', 'doc_formats', ',')
        self.assertEqual(exp_strs, self.oc.getDocFormats())
        self.oc.set('Documentation', 'doc_formats', 'Markdown,')
        self.assertEqual(['Markdown'], self.oc.getDocFormats())

        # Verify that format type strings are not case sensitive.  If matching
        # were case sensitive, than at least one of the following would throw
        # an exception.
        self.oc.set('Documentation', 'doc_formats', 'HTML')
        self.assertEqual(['HTML'], self.oc.getDocFormats())
        self.oc.set('Documentation', 'doc_formats', 'html')
        self.assertEqual(['html'], self.oc.getDocFormats())

        # Verify that multiple values are correctly handled.
        self.oc.set('Documentation', 'doc_formats', 'HTML, Markdown')
        self.assertEqual(['HTML', 'Markdown'], self.oc.getDocFormats())

        # Verify that invalid format strings are properly handled.
        self.oc.set('Documentation', 'doc_formats', 'HTML, invalid')
        with self.assertRaisesRegexp(
            ConfigError,
            'Invalid documentation format string for the "doc_formats" setting'
        ):
            self.oc.getDocFormats()

