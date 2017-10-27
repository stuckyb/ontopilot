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
from __future__ import unicode_literals
import unicodedata
from ontology import Ontology

# Java imports.
from org.semanticweb.owlapi.model import AxiomType, OWLClass, OWLSubClassOfAxiom, OWLEquivalentClassesAxiom, OWLDisjointClassesAxiom, OWLObjectPropertyExpression, OWLSubObjectPropertyOfAxiom, OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom, OWLInverseObjectPropertiesAxiom, OWLEquivalentObjectPropertiesAxiom, OWLDisjointObjectPropertiesAxiom, OWLDataPropertyExpression, OWLSubDataPropertyOfAxiom, OWLDataPropertyDomainAxiom, OWLDataPropertyRangeAxiom, OWLEquivalentDataPropertiesAxiom, OWLDisjointDataPropertiesAxiom, OWLIndividual, OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom, OWLObjectPropertyAssertionAxiom, OWLNegativeObjectPropertyAssertionAxiom, OWLNegativeDataPropertyAssertionAxiom, OWLSymmetricObjectPropertyAxiom, OWLAsymmetricObjectPropertyAxiom, OWLReflexiveObjectPropertyAxiom, OWLIrreflexiveObjectPropertyAxiom, OWLTransitiveObjectPropertyAxiom, OWLFunctionalObjectPropertyAxiom, OWLInverseFunctionalObjectPropertyAxiom, OWLFunctionalDataPropertyAxiom

from org.semanticweb.owlapi.model.parameters import Imports
from org.semanticweb.owlapi.model.parameters.Navigation import (
    IN_SUB_POSITION, IN_SUPER_POSITION
)
from org.semanticweb.owlapi.search import Filters
from uk.ac.manchester.cs.owlapi.modularity import SyntacticLocalityModuleExtractor
from uk.ac.manchester.cs.owlapi.modularity import ModuleType
from org.semanticweb.owlapi.model import EntityType


# Define constants for the supported extraction methods and methods for
# handling the constants.
class _ExtractMethods:
    # The STAR syntactic locality extraction method.
    LOCALITY = 0
    # Extract single entities without any other axioms (except annotations).
    SINGLE = 1

    # Combine all supported methods in a single tuple.
    all_methods = (LOCALITY, SINGLE)

    # Define string values that map to the extraction methods.
    strings = {
        'locality': LOCALITY,
        'single': SINGLE
    }

    def getMethodFromStr(self, method_str):
        """
        Returns the module extraction method constant that corresponds with the
        provided string value.
        """
        if method_str.lower() in self.strings:
            return self.strings[method_str.lower()]
        else:
            raise RuntimeError(
                'Invalid module extraction method: "{0}".  Method must be one '
                'of {{"{1}"}}.'.format(
                    method_str, '", "'.join(self.strings.keys())
                )
            )

methods = _ExtractMethods()


# Define constants for the kinds of axioms from which related terms can be
# extracted and methods for handling the constants.
class _RelatedAxiomTypes:
    # Superclasses and superproperties.
    ANCESTORS = 0
    # Subclasses and subproperties.
    DESCENDANTS = 1
    # Equivalent classes and properties.
    EQUIVALENTS = 2
    # Disjoint classes and properties.
    DISJOINTS = 3
    # Domains of object and data properties.
    DOMAINS = 4
    # Ranges of object and data properties.
    RANGES = 5
    # Object property inverses.
    INVERSES = 6
    # Types (class assertions) of named individuals.
    TYPES = 7
    # Object and data property assertions of named individuals, including
    # negative property assertions.
    PROPERTY_ASSERTIONS = 8

    # Combine all supported axiom types in a single tuple.
    all_ax_types = (
        ANCESTORS, DESCENDANTS, EQUIVALENTS, DISJOINTS, DOMAINS, RANGES,
        INVERSES
    )

    # Define string values that map to the axiom types.
    strings = {
        'ancestors': ANCESTORS,
        'descendants': DESCENDANTS,
        'equivalents': EQUIVALENTS,
        'disjoints': DISJOINTS,
        'domains': DOMAINS,
        'ranges': RANGES,
        'inverses': INVERSES,
        'types': TYPES,
        'property assertions': PROPERTY_ASSERTIONS
    }

    def getAxiomTypesFromStr(self, ax_types_str):
        """
        Returns a set of axiom type constants parsed from the input string,
        which should contain a comma-separated list of axiom type string
        values.  Matching is not case sensitive.
        """
        # First normalize the axiom types string using unicode compatibility
        # equivalents.  This ensures that "space-like" characters (e.g.,
        # no-break space) are converted to the ordinary space character.
        ax_types_str = unicodedata.normalize('NFKC', ax_types_str)
        type_strs = ax_types_str.split(',')

        ax_types = set()

        for type_str in type_strs:
            type_str = type_str.strip()
            if type_str == '':
                continue

            if type_str.lower() in self.strings:
                ax_types.add(self.strings[type_str.lower()])
            else:
                raise RuntimeError(
                    'Invalid axiom type for specifying related terms to '
                    'extract: "{0}".  Axiom type strings must be one of '
                    '{{"{1}"}}.'.format(
                        type_str, '", "'.join(self.strings.keys())
                    )
                )

        return ax_types

rel_axiom_types = _RelatedAxiomTypes()


class ModuleExtractor:
    """
    Extracts import "modules" from existing OWL ontologies.  Also includes two
    methods that might be useful in other contexts: getRelatedComponents() and
    getDirectlyRelatedComponents().  These methods make it simple to traverse
    the relationships among entities in an ontology.
    """
    def __init__(self, ontology_source):
        """
        Initialize this ModuleExtractor instance.  The argument
        "ontology_source" should be an instance of ontopilot.Ontology.
        """
        self.ontology = ontology_source
        self.owlont = self.ontology.getOWLOntology()

        # Initialize data structures for holding the extraction signature,
        # axioms that need to be retained, and entities to exclude.
        self.signatures = {}
        self.saved_axioms = set()
        self.excluded_entities = set()
        self.clearSignatures()

    def clearSignatures(self):
        """
        Resets all signature sets, the saved axiom set, and the excluded
        entities set to empty.
        """
        self.saved_axioms.clear()
        self.excluded_entities.clear()

        for method in methods.all_methods:
            self.signatures[method] = set()

    def getSignatureSize(self):
        """
        Returns the total number of entities in the starting module signature.
        """
        sigsize = 0
        for method in methods.all_methods:
            sigsize += len(self.signatures[method])

        return sigsize

    def addEntity(self, entity_id, method, rel_types=set()):
        """
        Adds an entity to the module signature.  If rel_types includes one or
        more entity relationship type constants, all relevant related entities
        will be retrieved recursively.  The final module will preserve all
        retrieved entity relationships.

        entity_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a label (with or without a prefix),
            a prefix IRI (i.e., a curie, such as "owl:Thing"), a relative IRI,
            a full IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label text' or
            prefix:'label txt').
        method: The extraction method to use for this entity.
        rel_types: A set of related axiom type constants.
        """
        entity = self.ontology.getExistingEntity(entity_id)
        if entity is None:
            raise RuntimeError(
                'The entity "{0}" could not be found in the source '
                'ontology.'.format(entity_id)
            )

        owlent = entity.getOWLAPIObj()

        entset, axiomset = self.getRelatedComponents(owlent, rel_types, True)

        self.saved_axioms.update(axiomset)
        self.signatures[method].update(entset)

    def excludeEntity(self, entity_id, rel_types=set()):
        """
        Adds an entity to exclude from the final module.  If rel_types includes
        one or more entity relationship type constants, all relevant related
        entities will be retrieved recursively and also excluded from the final
        module.

        entity_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a label (with or without a prefix),
            a prefix IRI (i.e., a curie, such as "owl:Thing"), a relative IRI,
            a full IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label text' or
            prefix:'label txt').
        rel_types: A set of related axiom type constants.
        """
        entity = self.ontology.getExistingEntity(entity_id)
        if entity is None:
            raise RuntimeError(
                'The entity "{0}" could not be found in the source '
                'ontology.'.format(entity_id)
            )

        owlent = entity.getOWLAPIObj()

        entset, axiomset = self.getRelatedComponents(owlent, rel_types, True)

        self.excluded_entities.update(entset)

    def extractModule(self, mod_iri):
        """
        Extracts a module that is a subset of the entities in the source
        ontology.  The result is returned as an Ontology object.

        mod_iri: The IRI for the extracted ontology module.  Can be either an
            IRI object or a string containing a relative IRI, prefix IRI, or
            full IRI.
        """
        modont = Ontology(self.ontology.ontman.createOntology())
        modont.setOntologyID(mod_iri)

        # Do the syntactic locality extraction.  Only do the extraction if the
        # signature set is non-empty.  The OWL API module extractor will
        # produce a non-empty module even for an empty signature set.
        if len(self.signatures[methods.LOCALITY]) > 0:
            slme = SyntacticLocalityModuleExtractor(
                self.ontology.ontman, self.owlont, ModuleType.STAR
            )
            mod_axioms = slme.extract(self.signatures[methods.LOCALITY])
            for axiom in mod_axioms:
                modont.addEntityAxiom(axiom)

        # Do all single-entity extractions.
        self._extractSingleEntities(self.signatures[methods.SINGLE], modont)

        # Add all saved axioms.
        for axiom in self.saved_axioms:
            modont.addEntityAxiom(axiom)

        # Remove any entities that should be excluded from the final module.
        for ent in self.excluded_entities:
            modont.removeEntity(ent, remove_annotations=True)

        # Add an annotation for the source of the module.
        sourceIRI = None
        ontid = self.owlont.getOntologyID()
        if ontid.getVersionIRI().isPresent():
            sourceIRI = ontid.getVersionIRI().get()
        elif ontid.getOntologyIRI().isPresent():
            sourceIRI = ontid.getOntologyIRI().get()

        if sourceIRI is not None:
            modont.setOntologySource(sourceIRI)

        return modont

    def _extractSingleEntities(self, signature, target):
        """
        Extracts entities from the source ontology using the single-entity
        extraction method, which pulls individual entities without any
        associated axioms (except for annotations).  Annotation properties that
        are used to annotate entities in the signature will also be extracted
        from the source ontology.

        signature: A set of OWL API OWLEntity objects.
        target: The target module ontopilot.Ontology object.
        """
        rdfslabel = self.ontology.df.getRDFSLabel()

        while len(signature) > 0:
            owlent = signature.pop()

            # Get the declaration axiom for this entity and add it to the
            # target ontology.
            ontset = self.owlont.getImportsClosure()
            for ont in ontset:
                dec_axioms = ont.getDeclarationAxioms(owlent)
                for axiom in dec_axioms:
                    target.addEntityAxiom(axiom)

            # If the current entity is a data or object property, make sure to
            # preserve its characteristics.
            proptypes = (EntityType.OBJECT_PROPERTY, EntityType.DATA_PROPERTY)
            if owlent.getEntityType() in proptypes:
                axioms = self._getPropertyCharacteristicsAxioms(owlent, True)
                for axiom in axioms:
                    target.addEntityAxiom(axiom)

            # Get all annotation axioms for this entity and add them to the
            # target ontology.
            for ont in ontset:
                annot_axioms = ont.getAnnotationAssertionAxioms(owlent.getIRI())

                for annot_axiom in annot_axioms:
                    target.addEntityAxiom(annot_axiom)

                    # Check if the relevant annotation property is already
                    # included in the target ontology.  If not, add it to the
                    # set of terms to extract.

                    # Ignore rdfs:label since it is always included.
                    if annot_axiom.getProperty().equals(rdfslabel):
                        continue

                    prop_iri = annot_axiom.getProperty().getIRI()

                    if target.getExistingAnnotationProperty(prop_iri) is None:
                        annot_ent = self.ontology.getExistingAnnotationProperty(prop_iri)
                        # Built-in annotation properties, such as rdfs:label,
                        # will not "exist" because they have no declaration
                        # axioms, so we need to check for this.
                        if annot_ent is not None:
                            signature.add(annot_ent.getOWLAPIObj())

    def _getAxioms(
        self, axiom_type, entity_type, entity, include_imports,
        position=IN_SUB_POSITION
    ):
        """
        This is an alternative (partial) implementation of the corresponding
        getAxioms() method in OWLAxiomIndex.  The OWL API implementation is
        buggy when searches include the imports closure, at least up to version
        4.3.1.  For example, when "subclass of" axioms are retrieved using
        Imports.INCLUDED, the OWL API implementation ends up searching for
        entities of type OWLClassImpl rather than OWLClass, which causes the
        search method in the Internals instance to fail, and ends up returning
        invalid results.  This implementation avoids those problems.

        axiom_type: The type of axiom to search for (should be an OWL API class
            object).
        entity_type: The type of entity referenced in the axioms (should be an
            OWL API class object, and should be the type (or supertype) of
            "entity").
        include_imports: Whether to search the imports closure.
        position: Whether "entity" should be the sub- or super-entity in the
            returned axioms.  Ignored for axioms that don't have sub/super
            positions.
        """
        if include_imports:
            axioms = set()

            for ont in self.owlont.getImportsClosure():
                new_axioms = ont.getAxioms(
                    axiom_type, entity_type, entity, Imports.EXCLUDED, position
                )
                axioms.update(new_axioms)
        else:
            axioms = self.owlont.getAxioms(
                axiom_type, entity_type, entity, Imports.EXCLUDED, position
            )

        return axioms

    def _getPropertyCharacteristicsAxioms(self, entity, include_imports=True):
        """
        Gets all axioms that define the characteristics of the target property.

        entity: An OWL API OWLEntity object for an object or data property.
        include_imports: Whether to search the ontology's imports closure.
        """
        axiomset = set()

        if entity.getEntityType() == EntityType.OBJECT_PROPERTY:
            axiomset.update(self._getAxioms(
                OWLSymmetricObjectPropertyAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            ))
            axiomset.update(self._getAxioms(
                OWLAsymmetricObjectPropertyAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            ))
            axiomset.update(self._getAxioms(
                OWLTransitiveObjectPropertyAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            ))
            axiomset.update(self._getAxioms(
                OWLReflexiveObjectPropertyAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            ))
            axiomset.update(self._getAxioms(
                OWLIrreflexiveObjectPropertyAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            ))
            axiomset.update(self._getAxioms(
                OWLFunctionalObjectPropertyAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            ))
            axiomset.update(self._getAxioms(
                OWLInverseFunctionalObjectPropertyAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            ))

        elif entity.getEntityType() == EntityType.DATA_PROPERTY:
            axiomset.update(self._getAxioms(
                OWLFunctionalDataPropertyAxiom, OWLDataPropertyExpression,
                entity, include_imports
            ))

        return axiomset

    def getRelatedComponents(self, target_entity, rel_types, include_imports=True):
        """
        Gets all entities and axioms that are recursively (i.e., either
        directly or indirectly) related to the target entity by the specified
        axiom types.  Returns a tuple containing two sets: 1) A set consisting
        of the target entity plus all related entities; and 2) a set of axioms
        that define the relationships among the entities plus any additional
        required axioms.

        target_entity: An OWL API OWLEntity object.
        rel_types: A set of related axiom type constants.
        include_imports: Whether to search the ontology's imports closure.
        """
        entset = set()
        axiomset = set()

        # Initialize a list to serve as a stack for tracking the "recursion"
        # through the entity graph.
        entstack = [target_entity]

        while len(entstack) > 0:
            entity = entstack.pop()

            entset.add(entity)

            new_sets = self.getDirectlyRelatedComponents(
                entity, rel_types, include_imports
            )
            new_entset, new_axiomset = new_sets

            axiomset.update(new_axiomset)

            for new_entity in new_entset:
                # Check whether this entity has already been processed so we
                # don't get stuck in cyclic relationship graphs.
                if not(new_entity in entset):
                    entstack.append(new_entity)

        return (entset, axiomset)

    def getDirectlyRelatedComponents(self, entity, rel_types, include_imports=True):
        """
        Gets all entities and axioms that are directly related to the target
        entity by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships plus any additional required axioms.

        entity: An OWL API OWLEntity object.
        rel_types: A set of related axiom type constants.
        include_imports: Whether to search the ontology's imports closure.
        """
        if entity.getEntityType() == EntityType.CLASS:
            return self._getRelComponentsForClass(
                entity, rel_types, include_imports
            )

        elif entity.getEntityType() == EntityType.OBJECT_PROPERTY:
            return self._getRelComponentsForObjectProp(
                entity, rel_types, include_imports
            )

        elif entity.getEntityType() == EntityType.DATA_PROPERTY:
            return self._getRelComponentsForDataProp(
                entity, rel_types, include_imports
            )

        elif entity.getEntityType() == EntityType.ANNOTATION_PROPERTY:
            return self._getRelComponentsForAnnotProp(
                entity, rel_types, include_imports
            )

        elif entity.getEntityType() == EntityType.NAMED_INDIVIDUAL:
            return self._getRelComponentsForIndividual(
                entity, rel_types, include_imports
            )

    def _getRelComponentsForClass(self, entity, rel_types, include_imports):
        """
        Gets all entities and axioms that are directly related to a class by
        the specified axiom types.  Returns a tuple containing two sets: 1) A
        set of all related entities; and 2) a set of axioms that define the
        relationships.

        entity: An OWL API OWLEntity object for a class.
        rel_types: A set of related axiom type constants.
        include_imports: Whether to search the ontology's imports closure.
        """
        entset = set()
        axiomset = set()

        # As a general comment, note that we use the generic getAxioms() search
        # method of OWLAxiomIndex, because it allows searching the imports
        # closure, rather than the more specialized search methods (e.g.,
        # getSubClassAxiomsForSubClass()), which do not allow searching the
        # imports closure.  This should not incur any performance penalty,
        # because an examination of the OWL API source code reveals that the
        # specialized search methods just call getAxioms() anyway.
        # Unfortunately, the OWL API implementation of getAxioms() is buggy
        # when the search includes the imports closure, so we actually have to
        # use the alternative implementation _getAxioms(), defined above in
        # this class.  See the comments for _getAxioms() for more details.

        from uk.ac.manchester.cs.owl.owlapi import OWLClassImpl
        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self._getAxioms(
                OWLSubClassOfAxiom, OWLClass, entity, include_imports,
                IN_SUB_POSITION
            )
            for axiom in axioms:
                super_ce = axiom.getSuperClass()
                if not(super_ce.isAnonymous()):
                    entset.add(super_ce.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            axioms = self._getAxioms(
                OWLSubClassOfAxiom, OWLClass, entity, include_imports,
                IN_SUPER_POSITION
            )
            for axiom in axioms:
                sub_ce = axiom.getSubClass()
                if not(sub_ce.isAnonymous()):
                    entset.add(sub_ce.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.EQUIVALENTS in rel_types:
            rawaxioms = self._getAxioms(
                OWLEquivalentClassesAxiom, OWLClass, entity, include_imports
            )
            for rawaxiom in rawaxioms:
                # Only examine pairwise axioms so we don't add axioms with
                # unnamed class expressions.
                for axiom in rawaxiom.asPairwiseAxioms():
                    # Converting a set of axioms to pairwise representations
                    # might include pairs that don't include the target class,
                    # so we need to check for this.
                    if not(axiom.contains(entity)):
                        continue

                    namedclasses = axiom.getNamedClasses()
                    for namedclass in namedclasses:
                        if not(namedclass.equals(entity)):
                            entset.add(namedclass)
                            axiomset.add(axiom)

        if rel_axiom_types.DISJOINTS in rel_types:
            rawaxioms = self._getAxioms(
                OWLDisjointClassesAxiom, OWLClass, entity, include_imports
            )
            for rawaxiom in rawaxioms:
                # Only examine pairwise axioms so we don't add axioms with
                # unnamed class expressions.
                for axiom in rawaxiom.asPairwiseAxioms():
                    # Converting a set of axioms to pairwise representations
                    # might include pairs that don't include the target class,
                    # so we need to check for this.
                    if not(axiom.contains(entity)):
                        continue

                    cexps = axiom.getClassExpressions()
                    for cexp in cexps:
                        if not(cexp.isAnonymous()):
                            namedclass = cexp.asOWLClass()
                            if not(namedclass.equals(entity)):
                                entset.add(namedclass)
                                axiomset.add(axiom)

        return (entset, axiomset)

    def _getRelComponentsForObjectProp(self, entity, rel_types, include_imports):
        """
        Gets all entities and axioms that are directly related to an object
        property by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships.

        entity: An OWL API OWLEntity object for an object property.
        rel_types: A set of related axiom type constants.
        include_imports: Whether to search the ontology's imports closure.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self._getAxioms(
                OWLSubObjectPropertyOfAxiom, OWLObjectPropertyExpression,
                entity, include_imports, IN_SUB_POSITION
            )
            for axiom in axioms:
                super_pe = axiom.getSuperProperty()
                if not(super_pe.isAnonymous()):
                    entset.add(super_pe.asOWLObjectProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            axioms = self._getAxioms(
                OWLSubObjectPropertyOfAxiom, OWLObjectPropertyExpression,
                entity, include_imports, IN_SUPER_POSITION
            )
            for axiom in axioms:
                sub_pe = axiom.getSubProperty()
                if not(sub_pe.isAnonymous()):
                    entset.add(sub_pe.asOWLObjectProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DOMAINS in rel_types:
            axioms = self._getAxioms(
                OWLObjectPropertyDomainAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            )
            for axiom in axioms:
                cexp = axiom.getDomain()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.RANGES in rel_types:
            axioms = self._getAxioms(
                OWLObjectPropertyRangeAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            )
            for axiom in axioms:
                cexp = axiom.getRange()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.INVERSES in rel_types:
            axioms = self._getAxioms(
                OWLInverseObjectPropertiesAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            )
            for axiom in axioms:
                for pexp in axiom.getPropertiesMinus(entity):
                    if not(pexp.isAnonymous()):
                        entset.add(pexp.asOWLObjectProperty())
                        axiomset.add(axiom)

        if rel_axiom_types.EQUIVALENTS in rel_types:
            rawaxioms = self._getAxioms(
                OWLEquivalentObjectPropertiesAxiom,
                OWLObjectPropertyExpression, entity, include_imports
            )
            for rawaxiom in rawaxioms:
                # Only examine pairwise axioms so we don't add axioms with
                # unnamed property expressions.
                for axiom in rawaxiom.asPairwiseAxioms():
                    # Converting a set of axioms to pairwise representations
                    # might include pairs that don't include the target
                    # property, so we need to check for this.
                    if not(axiom.getProperties().contains(entity)):
                        continue

                    for pexp in axiom.getPropertiesMinus(entity):
                        if not(pexp.isAnonymous()):
                            entset.add(pexp.asOWLObjectProperty())
                            axiomset.add(axiom)

        if rel_axiom_types.DISJOINTS in rel_types:
            rawaxioms = self._getAxioms(
                OWLDisjointObjectPropertiesAxiom, OWLObjectPropertyExpression,
                entity, include_imports
            )
            for rawaxiom in rawaxioms:
                # Only examine pairwise axioms so we don't add axioms with
                # unnamed property expressions.
                for axiom in rawaxiom.asPairwiseAxioms():
                    # Converting a set of axioms to pairwise representations
                    # might include pairs that don't include the target
                    # property, so we need to check for this.
                    if not(axiom.getProperties().contains(entity)):
                        continue

                    for pexp in axiom.getPropertiesMinus(entity):
                        if not(pexp.isAnonymous()):
                            entset.add(pexp.asOWLObjectProperty())
                            axiomset.add(axiom)

        return (entset, axiomset)

    def _getRelComponentsForDataProp(self, entity, rel_types, include_imports):
        """
        Gets all entities and axioms that are directly related to a data
        property by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships.

        entity: An OWL API OWLEntity object for a data property.
        rel_types: A set of related axiom type constants.
        include_imports: Whether to search the ontology's imports closure.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self._getAxioms(
                OWLSubDataPropertyOfAxiom, OWLDataPropertyExpression,
                entity, include_imports, IN_SUB_POSITION
            )
            for axiom in axioms:
                super_pe = axiom.getSuperProperty()
                if not(super_pe.isAnonymous()):
                    entset.add(super_pe.asOWLDataProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            axioms = self._getAxioms(
                OWLSubDataPropertyOfAxiom, OWLDataPropertyExpression,
                entity, include_imports, IN_SUPER_POSITION
            )
            for axiom in axioms:
                sub_pe = axiom.getSubProperty()
                if not(sub_pe.isAnonymous()):
                    entset.add(sub_pe.asOWLDataProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DOMAINS in rel_types:
            axioms = self._getAxioms(
                OWLDataPropertyDomainAxiom, OWLDataPropertyExpression, entity,
                include_imports
            )
            for axiom in axioms:
                cexp = axiom.getDomain()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.RANGES in rel_types:
            axioms = self._getAxioms(
                OWLDataPropertyRangeAxiom, OWLDataPropertyExpression, entity,
                include_imports
            )
            for axiom in axioms:
                axiomset.add(axiom)

        if rel_axiom_types.EQUIVALENTS in rel_types:
            rawaxioms = self._getAxioms(
                OWLEquivalentDataPropertiesAxiom, OWLDataPropertyExpression,
                entity, include_imports
            )
            for rawaxiom in rawaxioms:
                # Only examine pairwise axioms so we don't add axioms with
                # unnamed property expressions.
                for axiom in rawaxiom.asPairwiseAxioms():
                    # Converting a set of axioms to pairwise representations
                    # might include pairs that don't include the target
                    # property, so we need to check for this.
                    if not(axiom.getProperties().contains(entity)):
                        continue

                    for pexp in axiom.getPropertiesMinus(entity):
                        if not(pexp.isAnonymous()):
                            entset.add(pexp.asOWLDataProperty())
                            axiomset.add(axiom)

        if rel_axiom_types.DISJOINTS in rel_types:
            rawaxioms = self._getAxioms(
                OWLDisjointDataPropertiesAxiom, OWLDataPropertyExpression,
                entity, include_imports
            )
            for rawaxiom in rawaxioms:
                # Only examine pairwise axioms so we don't add axioms with
                # unnamed property expressions.
                for axiom in rawaxiom.asPairwiseAxioms():
                    # Converting a set of axioms to pairwise representations
                    # might include pairs that don't include the target
                    # property, so we need to check for this.
                    if not(axiom.getProperties().contains(entity)):
                        continue

                    for pexp in axiom.getPropertiesMinus(entity):
                        if not(pexp.isAnonymous()):
                            entset.add(pexp.asOWLDataProperty())
                            axiomset.add(axiom)

        return (entset, axiomset)

    def _getRelComponentsForAnnotProp(self, entity, rel_types, include_imports):
        """
        Gets all entities and axioms that are directly related to an annotation
        property by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships.

        entity: An OWL API OWLEntity object for an annotation property.
        rel_types: A set of related axiom type constants.
        include_imports: Whether to search the ontology's imports closure.
        """
        entset = set()
        axiomset = set()

        # The get() method in the OWL API Internals object does not handle
        # annotation property sub/super relationships, so we cannot use the
        # _getAxioms() method implemented above.  Instead, we implement the
        # searches directly using the filterAxioms() method of OWLAxiomIndex,
        # which in turn calls filterAxioms() in Internals.

        if include_imports:
            importsval = Imports.INCLUDED
        else:
            importsval = Imports.EXCLUDED
        
        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self.owlont.filterAxioms(
                Filters.subAnnotationWithSub, entity, importsval
            )
            for axiom in axioms:
                entset.add(axiom.getSuperProperty())
                axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            axioms = self.owlont.filterAxioms(
                Filters.subAnnotationWithSuper, entity, importsval
            )
            for axiom in axioms:
                entset.add(axiom.getSubProperty())
                axiomset.add(axiom)

        return (entset, axiomset)

    def _getRelComponentsForIndividual(self, entity, rel_types, include_imports):
        """
        Gets all entities and axioms that are directly related to a named
        individual.  Returns a tuple containing two sets: 1) A set of all
        related entities; and 2) a set of axioms that define the relationships.

        entity: An OWL API OWLEntity object for a named individual.
        rel_types: A set of related axiom type constants.
        include_imports: Whether to search the ontology's imports closure.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.TYPES in rel_types:
            axioms = self._getAxioms(
                OWLClassAssertionAxiom, OWLIndividual, entity, include_imports
            )
            for axiom in axioms:
                cexp = axiom.getClassExpression()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.PROPERTY_ASSERTIONS in rel_types:
            axioms = self._getAxioms(
                OWLObjectPropertyAssertionAxiom, OWLIndividual, entity,
                include_imports
            )
            axioms.update(self._getAxioms(
                OWLNegativeObjectPropertyAssertionAxiom, OWLIndividual, entity,
                include_imports
            ))
            for axiom in axioms:
                pexp = axiom.getProperty()
                indv = axiom.getObject()
                if not(pexp.isAnonymous()) and indv.isNamed():
                    entset.add(pexp.asOWLObjectProperty())
                    entset.add(indv.asOWLNamedIndividual())
                    axiomset.add(axiom)

            axioms = self._getAxioms(
                OWLDataPropertyAssertionAxiom, OWLIndividual, entity,
                include_imports
            )
            axioms.update(self._getAxioms(
                OWLNegativeDataPropertyAssertionAxiom, OWLIndividual, entity,
                include_imports
            ))
            for axiom in axioms:
                pexp = axiom.getProperty()
                if not(pexp.isAnonymous()):
                    entset.add(pexp.asOWLDataProperty())
                    axiomset.add(axiom)

        return (entset, axiomset)

