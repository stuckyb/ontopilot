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
from ontopilot.ontology import Ontology
from ontopilot.module_extractor import ModuleExtractor
from ontopilot.module_extractor import methods as me_methods
import unittest

# Java imports.
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum


# IRIs of entities in the test ontology.
OBJPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0001'
DATAPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0020'
ANNOTPROP_IRI = 'http://purl.obolibrary.org/obo/OBTO_0030'
CLASS_IRI = 'http://purl.obolibrary.org/obo/OBTO_0010'
INDIVIDUAL_IRI = 'https://github.com/stuckyb/ontopilot/raw/master/test/test_data/ontology.owl#individual_002'

# IRI that is not used in the test ontology.
NULL_IRI = 'http://purl.obolibrary.org/obo/OBTO_9999'


class Test_ModuleExtractor(unittest.TestCase):
    """
    Tests the ModuleExtractor class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.owlont = self.ont.getOWLOntology()

        self.me = ModuleExtractor(self.ont)

    def test_extractSingleTerms(self):
        """
        Tests building an import module using only the single-term extraction
        method.
        """
        # Add 'test class 1'.
        self.me.addEntity('OBTO:0010', me_methods.SINGLE)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE)

        module = self.me.extractModule('http://test.mod/id')

        # Verify that all expected entities are present in the module.  Use at
        # least one label reference to verify that labels are mapped correctly
        # in the module ontology.
        self.assertIsNotNone(module.getExistingClass("'test class 1'"))
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0001'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))

        # Verify that there are no unexpected entities.  Note that the
        # annotation properties in the signature will include rdfs:label and
        # dc:source.
        owlont = module.getOWLOntology()
        self.assertEqual(1, owlont.getClassesInSignature(True).size())
        self.assertEqual(1, owlont.getObjectPropertiesInSignature(True).size())
        self.assertEqual(0, owlont.getDataPropertiesInSignature(True).size())
        self.assertEqual(3, owlont.getAnnotationPropertiesInSignature(False).size())
        self.assertEqual(0, owlont.getIndividualsInSignature(True).size())

        module.saveOntology('blah.owl')

