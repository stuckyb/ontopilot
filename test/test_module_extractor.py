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
from ontopilot.module_extractor import methods as me_methods, rel_axiom_types
import unittest

# Java imports.


class Test_RelatedAxiomTypes(unittest.TestCase):
    """
    Tests the _RelatedAxiomTypes class.
    """
    def setUp(self):
        pass

    def test_getAxiomTypesFromStr(self):
        axset = rel_axiom_types.getAxiomTypesFromStr('')
        self.assertEqual(0, len(axset))

        axset = rel_axiom_types.getAxiomTypesFromStr(' \t  ')
        self.assertEqual(0, len(axset))

        axset = rel_axiom_types.getAxiomTypesFromStr(' ,,  ,\t ,')
        self.assertEqual(0, len(axset))

        axset = rel_axiom_types.getAxiomTypesFromStr('ancestors')
        expctd = {rel_axiom_types.ANCESTORS}
        self.assertEqual(expctd, axset)

        axset = rel_axiom_types.getAxiomTypesFromStr('ANCESTORS')
        self.assertEqual(expctd, axset)

        axset = rel_axiom_types.getAxiomTypesFromStr('ancestors, ancestors')
        self.assertEqual(expctd, axset)

        axset = rel_axiom_types.getAxiomTypesFromStr(
            'ancestors, domains, inverses'
        )
        expctd = {
            rel_axiom_types.ANCESTORS, rel_axiom_types.DOMAINS,
            rel_axiom_types.INVERSES
        }
        self.assertEqual(expctd, axset)

        axset = rel_axiom_types.getAxiomTypesFromStr(
            ',ancestors,, ,  domains, domains, ,inverses,'
        )
        self.assertEqual(expctd, axset)


class Test_ModuleExtractor(unittest.TestCase):
    """
    Tests the ModuleExtractor class.
    """
    def setUp(self):
        self.ont = Ontology('test_data/ontology.owl')
        self.owlont = self.ont.getOWLOntology()

        self.me = ModuleExtractor(self.ont)

    def test_getSignatureSize(self):
        self.assertEqual(0, self.me.getSignatureSize())

        self.me.addEntity('OBTO:0001', me_methods.SINGLE, False, False)
        self.me.addEntity('OBTO:0010', me_methods.SINGLE, False, False)
        self.me.addEntity('OBTO:0001', me_methods.LOCALITY, False, False)
        self.assertEqual(3, self.me.getSignatureSize())

        # Confirm that adding entities already in the signature does not
        # increase the signature size.
        self.me.addEntity('OBTO:0010', me_methods.SINGLE, False, False)
        self.assertEqual(3, self.me.getSignatureSize())

    def _compareEntitySets(self, ent_list, result):
        """
        Compares a list of expected entities to a result set of OWLEntity
        instances.  The list should contain entity ID strings.
        """
        expset = set()
        for ent_id in ent_list:
            ent = self.ont.getExistingEntity(ent_id)
            expset.add(ent.getOWLAPIObj())

        self.assertEqual(expset, result)

    def test_getAncestors(self):
        # Create a parent class for OBITO:0001.  This results in an explicit
        # class hierarchy that is 3 levels deep (starting from OBTO:0010),
        # which should provide a good test case for the traversal algorithm.
        ent = self.ont.getExistingClass('OBITO:0001')
        self.ont.createNewClass('OBTO:9999')
        ent.addSubclassOf('OBTO:9999')

        # Create a superproperty for 'test object property 1'.
        ent = self.ont.getExistingObjectProperty('OBTO:0001')
        self.ont.createNewObjectProperty('OBTO:0002')
        ent.addSuperproperty('OBTO:0002')

        # Create a superproperty for 'test data property 1'.
        ent = self.ont.getExistingDataProperty('OBTO:0020')
        self.ont.createNewDataProperty('OBTO:0021')
        ent.addSuperproperty('OBTO:0021')

        # Create a superproperty for 'annotation property 1'.
        ent = self.ont.getExistingAnnotationProperty('OBTO:0030')
        self.ont.createNewAnnotationProperty('OBTO:0031')
        ent.addSuperproperty('OBTO:0031')

        # Test class ancestors retrieval.
        ent = self.ont.getExistingClass('OBTO:0010').getOWLAPIObj()
        entset, axset = self.me._getAncestors(ent)
        self._compareEntitySets(
            ['OBITO:0001', 'OBTO:0010', 'OBTO:9999'], entset
        )
        self.assertEqual(2, len(axset))

        # Test object property ancestors retrieval.
        ent = self.ont.getExistingObjectProperty('OBTO:0001').getOWLAPIObj()
        entset, axset = self.me._getAncestors(ent)
        self._compareEntitySets(['OBTO:0001', 'OBTO:0002'], entset)
        self.assertEqual(1, len(axset))

        # Test data property branch retrieval.
        ent = self.ont.getExistingDataProperty('OBTO:0020').getOWLAPIObj()
        entset, axset = self.me._getAncestors(ent)
        self._compareEntitySets(['OBTO:0020', 'OBTO:0021'], entset)
        self.assertEqual(1, len(axset))

        # Test annotation property branch retrieval.
        ent = self.ont.getExistingAnnotationProperty('OBTO:0030').getOWLAPIObj()
        entset, axset = self.me._getAncestors(ent)
        self._compareEntitySets(['OBTO:0030', 'OBTO:0031'], entset)
        self.assertEqual(1, len(axset))

        # Make a cyclic parent/child relationship for 'test class 1'.
        ent = self.ont.getExistingClass('OBTO:9999')
        ent.addSubclassOf('OBITO:0001')

        # Verify that the cycle is correctly handled.
        ent = self.ont.getExistingClass('OBITO:0001').getOWLAPIObj()
        entset, axset = self.me._getAncestors(ent)
        self._compareEntitySets(['OBITO:0001', 'OBTO:9999'], entset)
        self.assertEqual(2, len(axset))

    def test_getBranch(self):
        # Create a subclass for 'test class 2'.  This results in an explicit
        # class hierarchy that is 3 levels deep and includes a node with
        # multiple child classes, all of which should provide a good test case
        # for the traversal algorithm.
        newent = self.ont.createNewClass('OBTO:9999')
        newent.addSubclassOf('OBTO:0011')

        # Create a subproperty for 'test object property 1'.
        newent = self.ont.createNewObjectProperty('OBTO:0002')
        newent.addSuperproperty('OBTO:0001')

        # Create a subproperty for 'test data property 1'.
        newent = self.ont.createNewDataProperty('OBTO:0021')
        newent.addSuperproperty('OBTO:0020')

        # Create a subproperty for 'annotation property 1'.
        newent = self.ont.createNewAnnotationProperty('OBTO:0031')
        newent.addSuperproperty('OBTO:0030')

        # Test class branch retrieval.
        ent = self.ont.getExistingClass('OBITO:0001').getOWLAPIObj()
        entset, axset = self.me._getBranch(ent)
        self._compareEntitySets(
            ['OBITO:0001', 'OBTO:0010', 'OBTO:0011', 'OBTO:0012', 'OBTO:9999'],
            entset
        )
        self.assertEqual(4, len(axset))

        # Test object property branch retrieval.
        ent = self.ont.getExistingObjectProperty('OBTO:0001').getOWLAPIObj()
        entset, axset = self.me._getBranch(ent)
        self._compareEntitySets(['OBTO:0001', 'OBTO:0002'], entset)
        self.assertEqual(1, len(axset))

        # Test data property branch retrieval.
        ent = self.ont.getExistingDataProperty('OBTO:0020').getOWLAPIObj()
        entset, axset = self.me._getBranch(ent)
        self._compareEntitySets(['OBTO:0020', 'OBTO:0021'], entset)
        self.assertEqual(1, len(axset))

        # Test annotation property branch retrieval.
        ent = self.ont.getExistingAnnotationProperty('OBTO:0030').getOWLAPIObj()
        entset, axset = self.me._getBranch(ent)
        self._compareEntitySets(['OBTO:0030', 'OBTO:0031'], entset)
        self.assertEqual(1, len(axset))

        # Make a cyclic parent/child relationship for 'test class 2'.
        ent = self.ont.getExistingClass('OBTO:0011')
        ent.addSubclassOf('OBTO:9999')

        # Verify that the cycle is correctly handled.
        ent = self.ont.getExistingClass('OBTO:0011').getOWLAPIObj()
        entset, axset = self.me._getBranch(ent)
        self._compareEntitySets(['OBTO:0011', 'OBTO:9999'], entset)
        self.assertEqual(2, len(axset))

    def test_extractSingleTerms(self):
        """
        Tests building an import module using only the single-term extraction
        method.
        """
        # Create a parent class for OBITO:0001.  This results in an explicit
        # class hierarchy that is 3 levels deep (starting from OBTO:0010),
        # which should provide a good test case for the traversal algorithm.
        ent = self.ont.getExistingClass('OBITO:0001')
        self.ont.createNewClass('OBTO:9999')
        ent.addSubclassOf('OBTO:9999')

        #--------
        # Create a new module to test adding single terms without any ancestors
        # or descendants.
        #--------

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

        #--------
        # Create a new module to test adding single terms with their
        # descendants.
        #--------

        self.me.clearSignatures()

        # Add 'imported test class 1'.
        self.me.addEntity('OBITO:0001', me_methods.SINGLE, True, False)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE, True, False)

        module = self.me.extractModule('http://test.mod/id2')

        # Verify that all expected entities are present in the module.  Use at
        # least one label reference to verify that labels are mapped correctly
        # in the module ontology.
        self.assertIsNotNone(module.getExistingClass('OBITO:0001'))
        self.assertIsNotNone(module.getExistingClass('OBTO:0010'))
        self.assertIsNotNone(module.getExistingClass('OBTO:0011'))
        self.assertIsNotNone(module.getExistingClass('OBTO:0012'))
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0001'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))

        # Verify that there are no unexpected entities.  Note that the
        # annotation properties in the signature will include rdfs:label and
        # dc:source.
        owlont = module.getOWLOntology()
        self.assertEqual(4, owlont.getClassesInSignature(True).size())
        self.assertEqual(1, owlont.getObjectPropertiesInSignature(True).size())
        self.assertEqual(0, owlont.getDataPropertiesInSignature(True).size())
        self.assertEqual(3, owlont.getAnnotationPropertiesInSignature(False).size())
        self.assertEqual(0, owlont.getIndividualsInSignature(True).size())

        # Verify that the parent/child axioms are present.
        ent = module.getExistingClass('OBITO:0001')
        axioms = owlont.getSubClassAxiomsForSuperClass(ent.getOWLAPIObj())
        self.assertEqual(3, axioms.size())

        #--------
        # Create a new module to test adding single terms with their
        # descendants and ancestors.
        #--------

        self.me.clearSignatures()

        # Add 'imported test class 1'.
        self.me.addEntity('OBITO:0001', me_methods.SINGLE, True, True)
        # Add 'test class 3'.  This should already be part of the signature
        # thanks to the preceding call, but we add it again here to verify that
        # repeated entities are not somehow duplicated in the extracted module.
        self.me.addEntity('OBTO:0012', me_methods.SINGLE, False, False)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE, True, True)

        module = self.me.extractModule('http://test.mod/id3')

        # Verify that all expected entities are present in the module.
        self.assertIsNotNone(module.getExistingClass('OBTO:9999'))
        self.assertIsNotNone(module.getExistingClass('OBITO:0001'))
        self.assertIsNotNone(module.getExistingClass('OBTO:0010'))
        self.assertIsNotNone(module.getExistingClass('OBTO:0011'))
        self.assertIsNotNone(module.getExistingClass('OBTO:0012'))
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0001'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))

        # Verify that there are no unexpected entities.  Note that the
        # annotation properties in the signature will include rdfs:label and
        # dc:source.
        owlont = module.getOWLOntology()
        self.assertEqual(5, owlont.getClassesInSignature(True).size())
        self.assertEqual(1, owlont.getObjectPropertiesInSignature(True).size())
        self.assertEqual(0, owlont.getDataPropertiesInSignature(True).size())
        self.assertEqual(3, owlont.getAnnotationPropertiesInSignature(False).size())
        self.assertEqual(0, owlont.getIndividualsInSignature(True).size())

        # Verify that the parent/child axioms are present.
        ent = module.getExistingClass('OBITO:0001')
        axioms = owlont.getSubClassAxiomsForSuperClass(ent.getOWLAPIObj())
        self.assertEqual(3, axioms.size())
        axioms = owlont.getSubClassAxiomsForSubClass(ent.getOWLAPIObj())
        self.assertEqual(1, axioms.size())

        #--------
        # Create a new module to test adding single terms combined with
        # explicitly excluding some entities.
        #--------

        self.me.clearSignatures()

        # Add 'imported test class 1', including all of its descendants and
        # ancestors, then exclude it and its descendants.
        self.me.addEntity('OBITO:0001', me_methods.SINGLE, True, True)
        self.me.excludeEntity('OBITO:0001', True, False)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE, True, True)

        module = self.me.extractModule('http://test.mod/id4')

        # Verify that all expected entities are present in the module.
        self.assertIsNotNone(module.getExistingClass('OBTO:9999'))
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

        # Verify that no parent/child axioms are present.
        ent = module.getExistingClass('OBTO:9999')
        axioms = owlont.getSubClassAxiomsForSuperClass(ent.getOWLAPIObj())
        self.assertTrue(axioms.isEmpty())

    def test_extractLocality(self):
        """
        Tests building an import module using only the syntactic locality
        extraction method.  This test only verifies that the code runs without
        error, since the correctness of the axiom extraction depends on the OWL
        API implementation.
        """
        # Add 'test class 1'.
        self.me.addEntity('OBTO:0010', me_methods.LOCALITY)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.LOCALITY)

        module = self.me.extractModule('http://test.mod/id')

        #module.saveOntology('test_mod.owl')

