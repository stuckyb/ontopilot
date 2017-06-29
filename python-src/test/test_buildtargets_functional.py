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
import unittest
import os.path, shutil
import subprocess
import tempfile
from ontopilot.ontology import Ontology

# Java imports.
from java.lang import System as JavaSystem
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model.parameters import Imports


class TestBuildTargetsFunctional(unittest.TestCase):
    """
    Implements functional/integration tests for each of OntoPilot's main build
    targets.  These tests do not attempt to provide complete coverage or test
    every possible edge case, but they do verify that the OntoPilot executable
    and all of the main build processes work from start to finish and produce
    the expected results.
    """
    def setUp(self):
        # Get the path to the ontopilot executable.  This depends on whether
        # we're running on *nix or Windows, and we can't use the usual methods
        # (os.name, sys.platform) to figure this out because they report "java"
        # or something similar.
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        if JavaSystem.getProperty('os.name').startswith('Windows'):
            self.execpath = os.path.realpath(
                os.path.join(scriptdir, '..', '..', 'bin', 'ontopilot.bat')
            )
        else:
            self.execpath = os.path.realpath(
                os.path.join(scriptdir, '..', '..', 'bin', 'ontopilot')
            )

        # Get the path to the test project.
        self.tproj_path = os.path.realpath(
            os.path.join(scriptdir, 'test_project')
        )

        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        if self.tmpdir is not None:
            shutil.rmtree(self.tmpdir)

    def test_init(self):
        # Run the init build task.  For now, just make sure that it runs
        # without error and check for the expected output files and
        # directories.
        args = [self.execpath, 'init', 'test.owl']
        retval = subprocess.call(args, cwd=self.tmpdir)
        self.assertEqual(0, retval)

        exp_dirs = [
            'ontology/', 'imports/', 'src/', 'src/entities/', 'src/imports/',
            'documentation'
        ]
        exp_dirs = [os.path.join(self.tmpdir, dpath) for dpath in exp_dirs]

        exp_files = [
            'project.conf',
            'src/test-base.owl',
            'src/doc_specification.txt',
            'src/imports/imported_ontologies.csv',
            'src/imports/bfo_test_entities.csv',
            'src/entities/test_properties.csv',
            'src/entities/test_classes.csv',
            'src/entities/test_individuals.csv'
        ]
        exp_files = [os.path.join(self.tmpdir, fpath) for fpath in exp_files]

        for exp_dir in exp_dirs:
            self.assertTrue(
                os.path.isdir(exp_dir),
                msg='Could not find expected directory: {0}'.format(exp_dir)
            )

        for exp_file in exp_files:
            self.assertTrue(
                os.path.isfile(exp_file),
                msg='Could not find expected file: {0}'.format(exp_file)
            )

    def _test_make_imports(self, tppath):
        """
        Tests the "make imports" build task.

        tppath: The path of the test OntoPilot project.
        """
        args = [self.execpath, 'make', 'imports']
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Check that the compiled import module exists.
        im_path = os.path.join(tppath, 'imports/bfo_test_import_module.owl')
        self.assertTrue(os.path.isfile(im_path))

        im_ont = Ontology(im_path)
        owlont = im_ont.getOWLOntology()

        # Confirm that it contains the single imported class.
        self.assertIsNotNone(im_ont.getExistingClass("'continuant'"))
        self.assertEqual(
            1, owlont.getClassesInSignature(Imports.EXCLUDED).size()
        )

        # Confirm that it contains the proper source annotation.
        bfo_verIRI = IRI.create('http://purl.obolibrary.org/obo/bfo/2.0/bfo.owl')
        found_src_annot = False
        for ont_annot in owlont.getAnnotations():
            if ont_annot.getProperty().getIRI().equals(Ontology.SOURCE_ANNOT_IRI):
                if ont_annot.getValue().asIRI().isPresent():
                    sourceIRI = ont_annot.getValue().asIRI().get()
                    if sourceIRI.equals(bfo_verIRI):
                        found_src_annot = True

        self.assertTrue(found_src_annot)

    def _test_make_ont(self, tppath):
        """
        Tests the basic "make ontology" build task.

        tppath: The path of the test OntoPilot project.
        """
        args = [self.execpath, 'make', 'ontology']
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Check that the compiled ontology exists.
        ont_path = os.path.join(tppath, 'ontology/test-raw.owl')
        self.assertTrue(os.path.isfile(ont_path))

        ont = Ontology(ont_path)
        owlont = ont.getOWLOntology()

        # Confirm that it contains the expected object property, class, and
        # individual, and nothing else.

        self.assertIsNotNone(ont.getExistingClass("'test class'"))
        # There are two classes in the signature because BFO:'continuant' is
        # used in a "subclass of" axiom.
        self.assertEqual(
            2, owlont.getClassesInSignature(Imports.EXCLUDED).size()
        )

        self.assertIsNotNone(ont.getExistingObjectProperty("'test property'"))
        self.assertEqual(
            1, owlont.getObjectPropertiesInSignature(Imports.EXCLUDED).size()
        )

        self.assertIsNotNone(ont.getExistingIndividual("'test individual'"))
        self.assertEqual(
            1, owlont.getIndividualsInSignature(Imports.EXCLUDED).size()
        )

        self.assertEqual(
            0, owlont.getDataPropertiesInSignature(Imports.EXCLUDED).size()
        )

    def _test_make_ont_merged(self, tppath):
        """
        Tests the "make ontology --merge" build task.

        tppath: The path of the test OntoPilot project.
        """
        args = [self.execpath, 'make', 'ontology', '--merge']
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Check that the compiled ontology exists.
        ont_path = os.path.join(tppath, 'ontology/test-merged.owl')
        self.assertTrue(os.path.isfile(ont_path))

        ont = Ontology(ont_path)
        owlont = ont.getOWLOntology()

        # There should not be any imports.
        self.assertTrue(owlont.getImports().isEmpty())

        # Confirm that the ontology contains the expected object property,
        # classes, and individual, and nothing else.

        self.assertIsNotNone(ont.getExistingClass("'test class'"))
        self.assertIsNotNone(ont.getExistingClass("'continuant'"))
        self.assertEqual(
            2, owlont.getClassesInSignature(Imports.EXCLUDED).size()
        )

        self.assertIsNotNone(ont.getExistingObjectProperty("'test property'"))
        self.assertEqual(
            1, owlont.getObjectPropertiesInSignature(Imports.EXCLUDED).size()
        )

        self.assertIsNotNone(ont.getExistingIndividual("'test individual'"))
        self.assertEqual(
            1, owlont.getIndividualsInSignature(Imports.EXCLUDED).size()
        )

        self.assertEqual(
            0, owlont.getDataPropertiesInSignature(Imports.EXCLUDED).size()
        )

    def _test_type_assertions(self, ont):
        """
        Tests that ont contains the type assertions expected after running a
        reasoner on the test ontology.
        """
        owlont = ont.getOWLOntology()

        indv = ont.getExistingIndividual("'test individual'").getOWLAPIObj()

        axioms = owlont.getClassAssertionAxioms(indv)
        self.assertEqual(2, axioms.size())

        exp_types = {
            'http://purl.obolibrary.org/obo/TO_0000001',
            'http://purl.obolibrary.org/obo/BFO_0000002'
        }
        types = set()
        for axiom in axioms:
            cexp = axiom.getClassExpression()
            if not(cexp.isAnonymous()):
                types.add(cexp.asOWLClass().getIRI().toString())

        self.assertEqual(exp_types, types)

    def _test_make_ont_reasoned(self, tppath):
        """
        Tests the "make ontology --reason" build task.  This should add one
        type assertion for individual 'test individual' (asserting it is of
        type 'continuant').

        tppath: The path of the test OntoPilot project.
        """
        args = [self.execpath, 'make', 'ontology', '--reason']
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Check that the compiled ontology exists.
        ont_path = os.path.join(tppath, 'ontology/test-reasoned.owl')
        self.assertTrue(os.path.isfile(ont_path))

        # Confirm that the ontology contains the expected type assertions.
        ont = Ontology(ont_path)
        self._test_type_assertions(ont)

    def _test_make_release(self, tppath):
        """
        Tests the "make release" build task.  This mostly just verifies that it
        runs without error and that all the expected files and directories were
        created, since the file contents are covered by the other build task
        tests.

        tppath: The path of the test OntoPilot project.
        """
        args = [
            self.execpath, 'make', 'release', '--release_date', '2017-05-01'
        ]
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Check that the release directory and files exist.
        exp_dirs = [
            'releases/', 'releases/2017-05-01/', 'releases/2017-05-01/imports/'
        ]
        exp_dirs = [os.path.join(tppath, dirpath) for dirpath in exp_dirs]

        exp_files = [
            'releases/2017-05-01/test.owl', 'releases/2017-05-01/test-raw.owl',
            'releases/2017-05-01/test-merged.owl',
            'releases/2017-05-01/imports/bfo_test_import_module.owl'
        ]
        exp_files = [os.path.join(tppath, filepath) for filepath in exp_files]

        for exp_dir in exp_dirs:
            self.assertTrue(os.path.isdir(exp_dir))

        for exp_file in exp_files:
            self.assertTrue(os.path.isfile(exp_file))

    def _test_make_documentation(self, tppath):
        """
        Tests the "make documentation" build task.  This mostly just verifies
        that it runs without error and that all the expected files and
        directories were created, since documentation output is covered by
        other unit tests.

        tppath: The path of the test OntoPilot project.
        """
        args = [self.execpath, 'make', 'documentation']
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Check that the documentation files exist.
        exp_files = [
            'documentation/test.html',
            'documentation/test.md',
            'documentation/documentation_styles.css',
            'documentation/navtree.js'
        ]
        exp_files = [os.path.join(tppath, filepath) for filepath in exp_files]

        for exp_file in exp_files:
            self.assertTrue(
                os.path.isfile(exp_file),
                msg='Could not find expected file: {0}'.format(exp_file)
            )

    def _test_errorcheck(self, tppath):
        """
        Tests the "error_check" build task.  This just verifies that it runs
        without error and returns the expected console output.

        tppath: The path of the test OntoPilot project.
        """
        args = [self.execpath, 'error_check']

        # If the process return value is non-zero, this will raise an
        # exception.
        output = subprocess.check_output(
            args, cwd=tppath, stderr=subprocess.STDOUT
        )
        print output

        self.assertTrue('No entailment problems were found.' in output)

    def _test_inference_pipeline(self, tppath):
        """
        Tests the "inference_pipeline" build target.  This method assumes that
        the unmodified ontology for the test project has already been built.

        tppath: The path of the test OntoPilot project.
        """
        in_path = os.path.join(tppath, 'ontology/test-raw.owl')
        out_path = os.path.join(tppath, 'ip_output.owl')

        args = [
            self.execpath, 'inference_pipeline', '--input', in_path,
            '--fileout', out_path
        ]

        # If the process return value is non-zero, this will raise an
        # exception.
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Confirm that the ontology contains the expected type assertions.
        ont = Ontology(out_path)
        self._test_type_assertions(ont)

    def _test_update_base(self, tppath):
        """
        Tests the "update_base" build target.

        tppath: The path of the test OntoPilot project.
        """
        args = [self.execpath, 'update_base']
        retval = subprocess.call(args, cwd=tppath)
        self.assertEqual(0, retval)

        # Check that the updated base ontology exists.
        ont_path = os.path.join(tppath, 'src/test-base.owl')
        self.assertTrue(os.path.isfile(ont_path))

        ont = Ontology(ont_path)
        owlont = ont.getOWLOntology()

        # Verify that the import was added to the base ontology.
        imports = owlont.getDirectImportsDocuments()
        self.assertEqual(1, imports.size())

        importIRI = imports.iterator().next().toString()
        self.assertTrue(importIRI.endswith('bfo_test_import_module.owl'))

    def test_ontology_tasks(self):
        """
        Tests all of the "make" build targets, including building imports,
        ontologies, modified ontologies, and releases.  Also tests the
        "error_check", "update_base", and "inference_pipeline" build targets.
        """
        # Copy the test project to the temporary location.
        tppath = os.path.realpath(os.path.join(self.tmpdir, 'test_project'))
        shutil.copytree(self.tproj_path, tppath)

        self._test_make_imports(tppath)

        self._test_make_ont(tppath)
        self._test_make_ont_merged(tppath)
        self._test_make_ont_reasoned(tppath)
        self._test_make_release(tppath)

        self._test_make_documentation(tppath)

        self._test_errorcheck(tppath)

        self._test_inference_pipeline(tppath)

        self._test_update_base(tppath)

