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
from org.semanticweb.owlapi.model import AxiomType
from org.semanticweb.owlapi.model import OWLObjectPropertyCharacteristicAxiom
from org.semanticweb.owlapi.model import OWLFunctionalDataPropertyAxiom
from org.semanticweb.owlapi.model import OWLTransitiveObjectPropertyAxiom


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

        self.me.addEntity('OBTO:0001', me_methods.SINGLE)
        self.me.addEntity('OBTO:0010', me_methods.SINGLE)
        self.me.addEntity('OBTO:0001', me_methods.LOCALITY)
        self.assertEqual(3, self.me.getSignatureSize())

        # Confirm that adding entities already in the signature does not
        # increase the signature size.
        self.me.addEntity('OBTO:0010', me_methods.SINGLE)
        self.assertEqual(3, self.me.getSignatureSize())

    def test_getPropertyCharacteristicsAxioms(self):
        # Test object property characteristics.
        ent = self.ont.getExistingObjectProperty('OBTO:0001')
        owlent = ent.getOWLAPIObj()

        axioms = self.me._getPropertyCharacteristicsAxioms(owlent)
        self.assertEqual(0, len(axioms))

        ent.makeFunctional()
        ent.makeInverseFunctional()
        ent.makeReflexive()
        ent.makeIrreflexive()
        ent.makeSymmetric()
        ent.makeAsymmetric()
        ent.makeTransitive()

        axioms = self.me._getPropertyCharacteristicsAxioms(owlent)
        self.assertEqual(7, len(axioms))
        for axiom in axioms:
            self.assertTrue(
                isinstance(axiom, OWLObjectPropertyCharacteristicAxiom)
            )
            self.assertTrue(axiom.getProperty().equals(owlent))

        # Test data property characteristics.
        ent = self.ont.getExistingDataProperty('OBTO:0020')
        owlent = ent.getOWLAPIObj()

        axioms = self.me._getPropertyCharacteristicsAxioms(owlent)
        self.assertEqual(0, len(axioms))

        ent.makeFunctional()

        axioms = self.me._getPropertyCharacteristicsAxioms(owlent)
        self.assertEqual(1, len(axioms))
        for axiom in axioms:
            self.assertTrue(isinstance(axiom, OWLFunctionalDataPropertyAxiom))
            self.assertTrue(axiom.getProperty().equals(owlent))

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

    def test_getDirectlyRelatedComponents(self):
        # Define a set of related axiom types for ancestors and descendants.
        relatives = {rel_axiom_types.ANCESTORS, rel_axiom_types.DESCENDANTS}

        #--------
        # Tests for classes.
        #--------

        # Create a parent class for OBITO:0001.  This results in an explicit
        # class hierarchy that is 3 levels deep (starting from OBTO:9999).
        ent = self.ont.getExistingClass('OBITO:0001')
        owlent = ent.getOWLAPIObj()
        self.ont.createNewClass('OBTO:9999')
        ent.addSuperclass('OBTO:9999')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, relatives
        )
        self._compareEntitySets(
            ['OBTO:9999', 'OBTO:0010', 'OBTO:0011', 'OBTO:0012'], entset
        )
        self.assertEqual(4, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(axiom.isOfType(AxiomType.SUBCLASS_OF))
            self.assertTrue(axiom.containsEntityInSignature(owlent))

        # Test a disjointness relationship.
        owlent = self.ont.getExistingClass('OBTO:0010').getOWLAPIObj()

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.DISJOINTS}
        )

        self._compareEntitySets(['OBTO:0011'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(axiom.isOfType(AxiomType.DISJOINT_CLASSES))
            self.assertTrue(axiom.contains(owlent))

        # Test equivalency relationships, and verify that the pairwise
        # equivalency axioms are properly analyzed.
        ent = self.ont.getExistingClass('OBTO:0010')
        owlent = ent.getOWLAPIObj()
        self.ont.createNewClass('OBTO:0013')
        self.ont.createNewClass('OBTO:0014')
        ent.addEquivalentTo('OBTO:0013')
        ent.addEquivalentTo('OBTO:0014')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.EQUIVALENTS}
        )

        self._compareEntitySets(['OBTO:0013', 'OBTO:0014'], entset)
        self.assertEqual(2, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(axiom.isOfType(AxiomType.EQUIVALENT_CLASSES))
            self.assertTrue(axiom.contains(owlent))

        #--------
        # Tests for object properties.
        #--------

        # Create a superproperty for 'test object property 1'.
        ent = self.ont.getExistingObjectProperty('OBTO:0001')
        owlent = ent.getOWLAPIObj()
        self.ont.createNewObjectProperty('OBTO:0002')
        ent.addSuperproperty('OBTO:0002')

        # Create a subproperty for 'test object property 1'.
        newent = self.ont.createNewObjectProperty('OBTO:0003')
        newent.addSuperproperty('OBTO:0001')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, relatives
        )

        self._compareEntitySets(['OBTO:0002', 'OBTO:0003'], entset)
        self.assertEqual(2, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(axiom.isOfType(AxiomType.SUB_OBJECT_PROPERTY))
            self.assertTrue(axiom.containsEntityInSignature(owlent))

        # Test an equivalency relationship.
        self.ont.createNewObjectProperty('OBTO:0004')
        ent.addEquivalentTo('OBTO:0004')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.EQUIVALENTS}
        )

        self._compareEntitySets(['OBTO:0004'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.EQUIVALENT_OBJECT_PROPERTIES)
            )
            self.assertTrue(axiom.getProperties().contains(owlent))

        # Test a disjointness relationship.
        self.ont.createNewObjectProperty('OBTO:0005')
        ent.addDisjointWith('OBTO:0005')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.DISJOINTS}
        )

        self._compareEntitySets(['OBTO:0005'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.DISJOINT_OBJECT_PROPERTIES)
            )
            self.assertTrue(axiom.getProperties().contains(owlent))

        # Test an inverse relationship.
        self.ont.createNewObjectProperty('OBTO:0006')
        ent.addInverse('OBTO:0006')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.INVERSES}
        )

        self._compareEntitySets(['OBTO:0006'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.INVERSE_OBJECT_PROPERTIES)
            )
            self.assertTrue(axiom.getProperties().contains(owlent))

        # Test a domain axiom.
        ent.addDomain('OBTO:0010')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.DOMAINS}
        )

        self._compareEntitySets(['OBTO:0010'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.OBJECT_PROPERTY_DOMAIN)
            )
            self.assertTrue(axiom.getProperty().equals(owlent))

        # Test a range axiom.
        ent.addRange('OBTO:0011')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.RANGES}
        )

        self._compareEntitySets(['OBTO:0011'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.OBJECT_PROPERTY_RANGE)
            )
            self.assertTrue(axiom.getProperty().equals(owlent))

        #--------
        # Tests for data properties.
        #--------

        # Create a superproperty for 'test data property 1'.
        ent = self.ont.getExistingDataProperty('OBTO:0020')
        owlent = ent.getOWLAPIObj()
        self.ont.createNewDataProperty('OBTO:0021')
        ent.addSuperproperty('OBTO:0021')

        # Create a subproperty for 'test data property 1'.
        newent = self.ont.createNewDataProperty('OBTO:0022')
        newent.addSuperproperty('OBTO:0020')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, relatives
        )

        self._compareEntitySets(['OBTO:0021', 'OBTO:0022'], entset)
        self.assertEqual(2, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(axiom.isOfType(AxiomType.SUB_DATA_PROPERTY))
            self.assertTrue(axiom.containsEntityInSignature(owlent))

        # Test an equivalency relationship.
        self.ont.createNewDataProperty('OBTO:0023')
        ent.addEquivalentTo('OBTO:0023')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.EQUIVALENTS}
        )

        self._compareEntitySets(['OBTO:0023'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.EQUIVALENT_DATA_PROPERTIES)
            )
            self.assertTrue(axiom.getProperties().contains(owlent))

        # Test a disjointness relationship.
        self.ont.createNewDataProperty('OBTO:0024')
        ent.addDisjointWith('OBTO:0024')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.DISJOINTS}
        )

        self._compareEntitySets(['OBTO:0024'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.DISJOINT_DATA_PROPERTIES)
            )
            self.assertTrue(axiom.getProperties().contains(owlent))

        # Test a domain axiom.
        ent.addDomain('OBTO:0010')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.DOMAINS}
        )

        self._compareEntitySets(['OBTO:0010'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.DATA_PROPERTY_DOMAIN)
            )
            self.assertTrue(axiom.getProperty().equals(owlent))

        # Test a range axiom.
        ent.addRange('xsd:string')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.RANGES}
        )

        self.assertEqual(0, len(entset))
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.DATA_PROPERTY_RANGE)
            )
            self.assertTrue(axiom.getProperty().equals(owlent))

        #--------
        # Tests for annotation properties.
        #--------

        # Create a superproperty for 'annotation property 1'.
        ent = self.ont.getExistingAnnotationProperty('OBTO:0030')
        owlent = ent.getOWLAPIObj()
        self.ont.createNewAnnotationProperty('OBTO:0031')
        ent.addSuperproperty('OBTO:0031')

        # Create a subproperty for 'annotation property 1'.
        newent = self.ont.createNewAnnotationProperty('OBTO:0032')
        newent.addSuperproperty('OBTO:0030')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, relatives
        )

        self._compareEntitySets(['OBTO:0031', 'OBTO:0032'], entset)
        self.assertEqual(2, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.SUB_ANNOTATION_PROPERTY_OF)
            )
            self.assertTrue(axiom.containsEntityInSignature(owlent))

        #--------
        # Tests for named individuals.
        #--------

        # Test a class assertion (type).
        ent = self.ont.createNewIndividual('OBTO:0042')
        owlent = ent.getOWLAPIObj()
        ent.addType('OBTO:0010')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.TYPES}
        )

        self._compareEntitySets(['OBTO:0010'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.CLASS_ASSERTION)
            )
            self.assertTrue(axiom.getIndividual().equals(owlent))

        # Test an object property assertion.
        self.ont.createNewIndividual('OBTO:0043')
        ent.addObjectPropertyFact('OBTO:0001', 'OBTO:0043')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.PROPERTY_ASSERTIONS}
        )

        self._compareEntitySets(['OBTO:0001', 'OBTO:0043'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.OBJECT_PROPERTY_ASSERTION)
            )
            self.assertTrue(axiom.getSubject().equals(owlent))

        # Test a negative object property assertion.
        ent = self.ont.createNewIndividual('OBTO:0044')
        self.ont.createNewIndividual('OBTO:0045')
        owlent = ent.getOWLAPIObj()
        ent.addObjectPropertyFact('OBTO:0001', 'OBTO:0045', is_negative=True)

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.PROPERTY_ASSERTIONS}
        )

        self._compareEntitySets(['OBTO:0001', 'OBTO:0045'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.NEGATIVE_OBJECT_PROPERTY_ASSERTION)
            )
            self.assertTrue(axiom.getSubject().equals(owlent))

        # Test a data property assertion.
        ent = self.ont.createNewIndividual('OBTO:0046')
        owlent = ent.getOWLAPIObj()
        ent.addDataPropertyFact('OBTO:0020', '"literal"^^xsd:string')

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.PROPERTY_ASSERTIONS}
        )

        self._compareEntitySets(['OBTO:0020'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.DATA_PROPERTY_ASSERTION)
            )
            self.assertTrue(axiom.getSubject().equals(owlent))

        # Test a negative data property assertion.
        ent = self.ont.createNewIndividual('OBTO:0047')
        owlent = ent.getOWLAPIObj()
        ent.addDataPropertyFact(
            'OBTO:0020', '"literal"^^xsd:string', is_negative=True
        )

        entset, axiomset = self.me.getDirectlyRelatedComponents(
            owlent, {rel_axiom_types.PROPERTY_ASSERTIONS}
        )

        self._compareEntitySets(['OBTO:0020'], entset)
        self.assertEqual(1, len(axiomset))
        for axiom in axiomset:
            self.assertTrue(
                axiom.isOfType(AxiomType.NEGATIVE_DATA_PROPERTY_ASSERTION)
            )
            self.assertTrue(axiom.getSubject().equals(owlent))

    def test_getRelatedComponents(self):
        # Create a subclass for 'test class 2'.  This results in an explicit
        # class hierarchy that is 3 levels deep and includes a node with
        # multiple child classes, all of which should provide a good test case
        # for the traversal algorithm.  The class structure should be as
        # follows:
        #
        # OBITO:0001
        # |--- OBTO:0010
        # |--- OBTO:0011
        # |    |--- OBTO:9999
        # |--- OBTO:0012
        newent = self.ont.createNewClass('OBTO:9999')
        newent.addSuperclass('OBTO:0011')

        # Test class descendant retrieval.
        ent = self.ont.getExistingClass('OBITO:0001').getOWLAPIObj()
        entset, axiomset = self.me.getRelatedComponents(
            ent, {rel_axiom_types.DESCENDANTS}
        )

        self._compareEntitySets(
            ['OBITO:0001', 'OBTO:0010', 'OBTO:0011', 'OBTO:0012', 'OBTO:9999'],
            entset
        )
        self.assertEqual(4, len(axiomset))

        # Make a cyclic parent/child relationship for 'test class 2'.  The
        # class structure should be as follows:
        #
        # OBITO:0001
        # |--- OBTO:0010
        # |--- OBTO:0011
        # |    |--- OBTO:9999
        # |         |--- OBTO:0011
        # |--- OBTO:0012
        ent = self.ont.getExistingClass('OBTO:0011')
        ent.addSuperclass('OBTO:9999')

        # Verify that the cycle is correctly handled.
        ent = self.ont.getExistingClass('OBTO:0011').getOWLAPIObj()
        entset, axiomset = self.me.getRelatedComponents(
            ent, {rel_axiom_types.DESCENDANTS}
        )

        self._compareEntitySets(['OBTO:0011', 'OBTO:9999'], entset)
        self.assertEqual(2, len(axiomset))

        # Create a polyhierarchy by making OBITO:0010 a parent class of
        # OBTO:0011.  The class structure should now be as follows:
        #
        # OBITO:0001
        # |--- OBTO:0010
        # |    |--- OBTO:0011
        # |         |--- OBTO:9999
        # |              |--- OBTO:0011
        # |--- OBTO:0011
        # |    |-- OBTO:9999
        # |        |--- OBTO:0011
        # |--- OBTO:0012
        ent = self.ont.getExistingClass('OBTO:0011')
        ent.addSuperclass('OBTO:0010')

        ent = self.ont.getExistingClass('OBITO:0001').getOWLAPIObj()
        entset, axiomset = self.me.getRelatedComponents(
            ent, {rel_axiom_types.DESCENDANTS}
        )

        self._compareEntitySets(
            ['OBITO:0001', 'OBTO:0010', 'OBTO:0011', 'OBTO:0012', 'OBTO:9999'],
            entset
        )
        self.assertEqual(6, len(axiomset))

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
        ent.addSuperclass('OBTO:9999')

        #--------
        # Create a new module to test adding single terms without any ancestors
        # or descendants.
        #--------

        # Add 'test class 1'.
        self.me.addEntity('OBTO:0010', me_methods.SINGLE)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE)

        # Make 'test object property 1' transitive.
        prop = self.ont.getExistingObjectProperty('OBTO:0001')
        prop.makeTransitive()

        module = self.me.extractModule('http://test.mod/id')

        # Verify that all expected entities are present in the module.  Use at
        # least one label reference to verify that labels are mapped correctly
        # in the module ontology.
        self.assertIsNotNone(module.getExistingClass("'test class 1'"))
        self.assertIsNotNone(module.getExistingObjectProperty('OBTO:0001'))
        self.assertIsNotNone(module.getExistingAnnotationProperty('OBTO:0030'))

        # Verify that 'test object property 1' is transitive.
        owlprop = module.getExistingObjectProperty('OBTO:0001').getOWLAPIObj()
        owlmod = module.getOWLOntology()
        axioms = owlmod.getTransitiveObjectPropertyAxioms(owlprop)
        self.assertEqual(1, len(axioms))
        for axiom in axioms:
            self.assertTrue(
                isinstance(axiom, OWLTransitiveObjectPropertyAxiom)
            )
            self.assertTrue(axiom.getProperty().equals(owlprop))

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

        # Define a set of related axiom types for descendants.
        descendants = {rel_axiom_types.DESCENDANTS}

        # Add 'imported test class 1'.
        self.me.addEntity('OBITO:0001', me_methods.SINGLE, descendants)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE, descendants)

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

        # Define a set of related axiom types for ancestors and descendants.
        relatives = {rel_axiom_types.ANCESTORS, rel_axiom_types.DESCENDANTS}

        # Add 'imported test class 1'.
        self.me.addEntity('OBITO:0001', me_methods.SINGLE, relatives)
        # Add 'test class 3'.  This should already be part of the signature
        # thanks to the preceding call, but we add it again here to verify that
        # repeated entities are not somehow duplicated in the extracted module.
        self.me.addEntity('OBTO:0012', me_methods.SINGLE)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE, relatives)

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
        self.me.addEntity('OBITO:0001', me_methods.SINGLE, relatives)
        self.me.excludeEntity('OBITO:0001', descendants)
        # Add 'test object property 1'.
        self.me.addEntity('OBTO:0001', me_methods.SINGLE, relatives)

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

