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
import ontopilot.oom_manager as oom_man
import unittest
#from testfixtures import LogCapture

# Java imports.
from org.semanticweb.owlapi.apibinding import OWLManager
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.util import SimpleIRIMapper


class Test_OOMManager(unittest.TestCase):
    """
    Tests the OWLOntologyManager manager module.
    """
    def setUp(self):
        pass

    def test_lookupDocumentIRI(self):
        oom = OWLManager.createOWLOntologyManager()

        # Test two mappings to make sure multiple mappings work as expected.
        testvals = [
            {
                'ontIRI': IRI.create('http://some.ontology.iri/path'),
                'docIRI': IRI.create('http://some.doc.iri/path')
            },
            {
                'ontIRI': IRI.create('http://2nd.ontology.iri/path'),
                'docIRI': IRI.create('http://2nd.doc.iri/path')
            }
        ]

        for testval in testvals:
            self.assertIsNone(
                oom_man.lookupDocumentIRI(oom, testval['ontIRI'])
            )

            oom.getIRIMappers().add(
                SimpleIRIMapper(testval['ontIRI'], testval['docIRI'])
            )

            self.assertTrue(
                oom_man.lookupDocumentIRI(oom, testval['ontIRI']).equals(
                    testval['docIRI']
                )
            )

    def test_IRIMapping(self):
        """
        This method test both addNewIRIMapping() and
        getNewOWLOntologyManager(), including updating of the mappings in
        previously created OOMs.
        """
        ontIRI = IRI.create('http://some.ontology.iri/path')
        docIRI = IRI.create('http://some.doc.iri/path')

        oom1 = oom_man.getNewOWLOntologyManager()

        # Verify that the new OOM does not contain the IRI mapping.
        self.assertIsNone(oom_man.lookupDocumentIRI(oom1, ontIRI))

        oom_man.addNewIRIMapping(ontIRI, docIRI)

        # Verify that the old OOM got the new mapping.
        self.assertTrue(
            oom_man.lookupDocumentIRI(oom1, ontIRI).equals(docIRI)
        )

        # Verify that a new OOM has the new mapping.
        oom2 = oom_man.getNewOWLOntologyManager()
        self.assertTrue(
            oom_man.lookupDocumentIRI(oom2, ontIRI).equals(docIRI)
        )

        # Attempting to add a mapping that already exists should not raise an
        # exception.
        oom_man.addNewIRIMapping(ontIRI, docIRI)

        # Attempting to add a conflicting mapping should raise an exception.
        with self.assertRaisesRegexp(
            RuntimeError, 'conflicting mapping of .* already exists'
        ):
            oom_man.addNewIRIMapping(
                ontIRI, IRI.create('http://conflicting.iri')
            )

