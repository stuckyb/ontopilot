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
from ontology import Ontology

# Java imports.
from org.semanticweb.owlapi.model import AxiomType
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
        ax_types = set()

        type_strs = ax_types_str.split(',')

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
    Extracts import "modules" from existing OWL ontologies.
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

    def addEntity(self, entity_id, method, include_branch=False, include_ancestors=False):
        """
        Adds an entity to the module signature.  If include_branch is True, all
        descendants of the entity will be retrieved and added to the signature.
        If include_ancestors is True, all ancestors of the entity will be
        retrieved and added to the signature.  The final module will preserve
        all parent/child relationships in the retrieved hierarchies.

        entity_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a label (with or without a prefix),
            a prefix IRI (i.e., a curie, such as "owl:Thing"), a relative IRI,
            a full IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label text' or
            prefix:'label txt').
        method: The extraction method to use for this entity.
        include_branch: If True, all descendants of the entity will also be
            added to the signature.
        include_ancestors: If True, all ancestors of the entity will also be
            added to the signature.
        """
        entity = self.ontology.getExistingEntity(entity_id)
        if entity == None:
            raise RuntimeError(
                'The entity "{0}" could not be found in the source '
                'ontology.'.format(entity_id)
            )

        owlent = entity.getOWLAPIObj()

        entset = {owlent}
        if include_branch:
            br_ents, br_axioms = self._getBranch(owlent)
            entset.update(br_ents)
            self.saved_axioms.update(br_axioms)

        if include_ancestors:
            an_ents, an_axioms = self._getAncestors(owlent)
            entset.update(an_ents)
            self.saved_axioms.update(an_axioms)

        self.signatures[method].update(entset)

    def excludeEntity(self, entity_id, exclude_branch=False, exclude_ancestors=False):
        """
        Adds an entity to exclude from the final module.  If exclude_branch is
        True, all descendants of the entity will be retrieved and excluded.  If
        exclude_ancestors is True, all ancestors of the entity will be
        retrieved and excluded.

        entity_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a label (with or without a prefix),
            a prefix IRI (i.e., a curie, such as "owl:Thing"), a relative IRI,
            a full IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label text' or
            prefix:'label txt').
        exclude_branch: If True, all descendants of the entity will be
            excluded.
        exclude_ancestors: If True, all ancestors of the entity will be
            excluded.
        """
        entity = self.ontology.getExistingEntity(entity_id)
        if entity == None:
            raise RuntimeError(
                'The entity "{0}" could not be found in the source '
                'ontology.'.format(entity_id)
            )

        owlent = entity.getOWLAPIObj()

        entset = {owlent}
        if exclude_branch:
            br_ents, br_axioms = self._getBranch(owlent)
            entset.update(br_ents)

        if exclude_ancestors:
            an_ents, an_axioms = self._getAncestors(owlent)
            entset.update(an_ents)

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

        # Add any subclass/subproperty axioms.
        for axiom in self.saved_axioms:
            modont.addEntityAxiom(axiom)

        # Remove any entities that should be excluded from the final module.
        for ent in self.excluded_entities:
            modont.removeEntity(ent)

        # Add an annotation for the source of the module.
        sourceIRI = None
        ontid = self.owlont.getOntologyID()
        if ontid.getVersionIRI().isPresent():
            sourceIRI = ontid.getVersionIRI().get()
        elif ontid.getOntologyIRI().isPresent():
            sourceIRI = ontid.getOntologyIRI().get()

        if sourceIRI != None:
            modont.setOntologySource(sourceIRI)

        return modont

    def _getDirectlyRelatedComponents(self, entity, rel_types):
        """
        Gets all entities and axioms that are directly related to the target
        entity by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships plus any additional required axioms.

        entity: An OWL API OWLEntity object.
        rel_types: A set of related axiom type constants.
        """
        if entity.getEntityType() == EntityType.CLASS:
            return self._getRelComponentsForClass(entity, rel_types)

        elif entity.getEntityType() == EntityType.OBJECT_PROPERTY:
            return self._getRelComponentsForObjectProp(entity, rel_types)

        elif entity.getEntityType() == EntityType.DATA_PROPERTY:
            return self._getRelComponentsForDataProp(entity, rel_types)

        elif entity.getEntityType() == EntityType.ANNOTATION_PROPERTY:
            return self._getRelComponentsForAnnotProp(entity, rel_types)

        elif entity.getEntityType() == EntityType.NAMED_INDIVIDUAL:
            return self._getRelComponentsForIndividual(entity, rel_types)

    def _getRelComponentsForClass(self, entity, rel_types):
        """
        Gets all entities and axioms that are directly related to a class by
        the specified axiom types.  Returns a tuple containing two sets: 1) A
        set of all related entities; and 2) a set of axioms that define the
        relationships.

        entity: An OWL API OWLEntity object for a class.
        rel_types: A set of related axiom type constants.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self.owlont.getSubClassAxiomsForSubClass(entity)
            for axiom in axioms:
                super_ce = axiom.getSuperClass()
                if not(super_ce.isAnonymous()):
                    entset.add(super_ce.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            axioms = self.owlont.getSubClassAxiomsForSuperClass(entity)
            for axiom in axioms:
                sub_ce = axiom.getSubClass()
                if not(sub_ce.isAnonymous()):
                    entset.add(sub_ce.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.EQUIVALENTS in rel_types:
            rawaxioms = self.owlont.getEquivalentClassesAxioms(entity)
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
            rawaxioms = self.owlont.getDisjointClassesAxioms(entity)
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

    def _getRelComponentsForObjectProp(self, entity, rel_types):
        """
        Gets all entities and axioms that are directly related to an object
        property by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships.

        entity: An OWL API OWLEntity object for an object property.
        rel_types: A set of related axiom type constants.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self.owlont.getObjectSubPropertyAxiomsForSubProperty(
                entity
            )
            for axiom in axioms:
                super_pe = axiom.getSuperProperty()
                if not(super_pe.isAnonymous()):
                    entset.add(super_pe.asOWLObjectProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            axioms = self.owlont.getObjectSubPropertyAxiomsForSuperProperty(
                entity
            )
            for axiom in axioms:
                sub_pe = axiom.getSubProperty()
                if not(sub_pe.isAnonymous()):
                    entset.add(sub_pe.asOWLObjectProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DOMAINS in rel_types:
            axioms = self.owlont.getObjectPropertyDomainAxioms(entity)
            for axiom in axioms:
                cexp = axiom.getDomain()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.RANGES in rel_types:
            axioms = self.owlont.getObjectPropertyRangeAxioms(entity)
            for axiom in axioms:
                cexp = axiom.getRange()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.INVERSES in rel_types:
            axioms = self.owlont.getInverseObjectPropertyAxioms(entity)
            for axiom in axioms:
                for pexp in axiom.getPropertiesMinus(entity):
                    if not(pexp.isAnonymous()):
                        entset.add(pexp.asOWLObjectProperty())
                        axiomset.add(axiom)

        if rel_axiom_types.EQUIVALENTS in rel_types:
            rawaxioms = self.owlont.getEquivalentObjectPropertiesAxioms(entity)
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
            rawaxioms = self.owlont.getDisjointObjectPropertiesAxioms(entity)
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

    def _getRelComponentsForDataProp(self, entity, rel_types):
        """
        Gets all entities and axioms that are directly related to a data
        property by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships.

        entity: An OWL API OWLEntity object for a data property.
        rel_types: A set of related axiom type constants.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self.owlont.getDataSubPropertyAxiomsForSubProperty(
                entity
            )
            for axiom in axioms:
                super_pe = axiom.getSuperProperty()
                if not(super_pe.isAnonymous()):
                    entset.add(super_pe.asOWLDataProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            axioms = self.owlont.getDataSubPropertyAxiomsForSuperProperty(
                entity
            )
            for axiom in axioms:
                sub_pe = axiom.getSubProperty()
                if not(sub_pe.isAnonymous()):
                    entset.add(sub_pe.asOWLDataProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DOMAINS in rel_types:
            axioms = self.owlont.getDataPropertyDomainAxioms(entity)
            for axiom in axioms:
                cexp = axiom.getDomain()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.RANGES in rel_types:
            axioms = self.owlont.getDataPropertyRangeAxioms(entity)
            for axiom in axioms:
                axiomset.add(axiom)

        if rel_axiom_types.EQUIVALENTS in rel_types:
            rawaxioms = self.owlont.getEquivalentDataPropertiesAxioms(entity)
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
            rawaxioms = self.owlont.getDisjointDataPropertiesAxioms(entity)
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

    def _getRelComponentsForAnnotProp(self, entity, rel_types):
        """
        Gets all entities and axioms that are directly related to an annotation
        property by the specified axiom types.  Returns a tuple containing two
        sets: 1) A set of all related entities; and 2) a set of axioms that
        define the relationships.

        entity: An OWL API OWLEntity object for an annotation property.
        rel_types: A set of related axiom type constants.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.ANCESTORS in rel_types:
            axioms = self.owlont.getSubAnnotationPropertyOfAxioms(entity)
            for axiom in axioms:
                    entset.add(axiom.getSuperProperty())
                    axiomset.add(axiom)

        if rel_axiom_types.DESCENDANTS in rel_types:
            # The OWL API does not include a method to retrieve annotation
            # subproperty axioms by the parent property, so we instead examine
            # all annotation subproperty axioms to see which ones have the
            # current entity as a superproperty.
            axioms = self.owlont.getAxioms(
                AxiomType.SUB_ANNOTATION_PROPERTY_OF, True
            )
            for axiom in axioms:
                if axiom.getSuperProperty().equals(entity):
                    entset.add(axiom.getSubProperty())
                    axiomset.add(axiom)

        return (entset, axiomset)

    def _getRelComponentsForIndividual(self, entity, rel_types):
        """
        Gets all entities and axioms that are directly related to a named
        individual.  Returns a tuple containing two sets: 1) A set of all
        related entities; and 2) a set of axioms that define the relationships.

        entity: An OWL API OWLEntity object for a named individual.
        rel_types: A set of related axiom type constants.
        """
        entset = set()
        axiomset = set()

        if rel_axiom_types.TYPES in rel_types:
            axioms = self.owlont.getClassAssertionAxioms(entity)
            for axiom in axioms:
                cexp = axiom.getClassExpression()
                if not(cexp.isAnonymous()):
                    entset.add(cexp.asOWLClass())
                    axiomset.add(axiom)

        if rel_axiom_types.PROPERTY_ASSERTIONS in rel_types:
            axioms = self.owlont.getObjectPropertyAssertionAxioms(entity)
            axioms.update(
                self.owlont.getNegativeObjectPropertyAssertionAxioms(entity)
            )
            for axiom in axioms:
                pexp = axiom.getProperty()
                indv = axiom.getObject()
                if not(pexp.isAnonymous()) and indv.isNamed():
                    entset.add(pexp.asOWLObjectProperty())
                    entset.add(indv.asOWLNamedIndividual())
                    axiomset.add(axiom)

            axioms = self.owlont.getDataPropertyAssertionAxioms(entity)
            axioms.update(
                self.owlont.getNegativeDataPropertyAssertionAxioms(entity)
            )
            for axiom in axioms:
                pexp = axiom.getProperty()
                if not(pexp.isAnonymous()):
                    entset.add(pexp.asOWLDataProperty())
                    axiomset.add(axiom)

        return (entset, axiomset)

    def _getAncestors(self, leaf_entity):
        """
        Returns two sets: 1) a set of OntologyEntity objects that includes the
        leaf entity and all entities in the ancestor hierarchy of the leaf
        entity; and 2) a set of all subclass/subproperty axioms needed to
        create the entity hierarhy.

        leaf_entity: An OWL API OWLEntity object.
        """
        hierset = set()
        axiomset = set()

        # Initialize a list to serve as a stack for tracking the "recursion"
        # up the entity hierarchy.
        entstack = [leaf_entity]

        while len(entstack) > 0:
            entity = entstack.pop()

            hierset.add(entity)

            if entity.getEntityType() == EntityType.CLASS:
                axioms = self.owlont.getSubClassAxiomsForSubClass(entity)
                for axiom in axioms:
                    super_ce = axiom.getSuperClass()
                    if not(super_ce.isAnonymous()):
                        superclass = super_ce.asOWLClass()
                        axiomset.add(axiom)

                        # Check whether the parent class has already been
                        # processed so we don't get stuck in cyclic
                        # relationship graphs.
                        if not(superclass in hierset):
                            entstack.append(superclass)

            elif entity.getEntityType() == EntityType.OBJECT_PROPERTY:
                axioms = self.owlont.getObjectSubPropertyAxiomsForSubProperty(
                    entity
                )
                for axiom in axioms:
                    super_pe = axiom.getSuperProperty()
                    if not(super_pe.isAnonymous()):
                        superprop = super_pe.asOWLObjectProperty()
                        axiomset.add(axiom)

                        # Check whether the parent property has already been
                        # processed so we don't get stuck in cyclic
                        # relationship graphs.
                        if not(superprop in hierset):
                            entstack.append(superprop)

            elif entity.getEntityType() == EntityType.DATA_PROPERTY:
                axioms = self.owlont.getDataSubPropertyAxiomsForSubProperty(
                    entity
                )
                for axiom in axioms:
                    super_pe = axiom.getSuperProperty()
                    if not(super_pe.isAnonymous()):
                        superprop = super_pe.asOWLDataProperty()
                        axiomset.add(axiom)

                        # Check whether the parent property has already been
                        # processed so we don't get stuck in cyclic
                        # relationship graphs.
                        if not(superprop in hierset):
                            entstack.append(superprop)

            elif entity.getEntityType() == EntityType.ANNOTATION_PROPERTY:
                axioms = self.owlont.getSubAnnotationPropertyOfAxioms(entity)
                for axiom in axioms:
                    superprop = axiom.getSuperProperty()
                    axiomset.add(axiom)

                    # Check whether the parent property has already been
                    # processed so we don't get stuck in cyclic relationship
                    # graphs.
                    if not(superprop in hierset):
                        entstack.append(superprop)

        return (hierset, axiomset)

    def _getBranch(self, root_entity):
        """
        Retrieves all entities that are descendants of the root entity.
        Returns two sets: 1) a set of all entities in the branch; and 2) a set
        of all subclass/subproperty axioms relating the entities in the branch.

        root_entity: An OWL API OWLEntity object.
        """
        # Initialize the results sets.
        br_entset = set()
        br_axiomset = set()

        # Initialize a list to serve as a stack for tracking the "recursion"
        # through the branch.
        entstack = [root_entity]

        while len(entstack) > 0:
            entity = entstack.pop()

            br_entset.add(entity)

            if entity.getEntityType() == EntityType.CLASS:
                axioms = self.owlont.getSubClassAxiomsForSuperClass(entity)
                for axiom in axioms:
                    sub_ce = axiom.getSubClass()
                    if not(sub_ce.isAnonymous()):
                        subclass = sub_ce.asOWLClass()
                        br_axiomset.add(axiom)

                        # Check whether the child class has already been
                        # processed so we don't get stuck in cyclic
                        # relationship graphs.
                        if not(subclass in br_entset):
                            entstack.append(subclass)

            elif entity.getEntityType() == EntityType.OBJECT_PROPERTY:
                axioms = self.owlont.getObjectSubPropertyAxiomsForSuperProperty(
                    entity
                )
                for axiom in axioms:
                    sub_pe = axiom.getSubProperty()
                    if not(sub_pe.isAnonymous()):
                        subprop = sub_pe.asOWLObjectProperty()
                        br_axiomset.add(axiom)

                        # Check whether the child property has already been
                        # processed so we don't get stuck in cyclic
                        # relationship graphs.
                        if not(subprop in br_entset):
                            entstack.append(subprop)

            elif entity.getEntityType() == EntityType.DATA_PROPERTY:
                axioms = self.owlont.getDataSubPropertyAxiomsForSuperProperty(
                    entity
                )
                for axiom in axioms:
                    sub_pe = axiom.getSubProperty()
                    if not(sub_pe.isAnonymous()):
                        subprop = sub_pe.asOWLDataProperty()
                        br_axiomset.add(axiom)

                        # Check whether the child property has already been
                        # processed so we don't get stuck in cyclic
                        # relationship graphs.
                        if not(subprop in br_entset):
                            entstack.append(subprop)

            elif entity.getEntityType() == EntityType.ANNOTATION_PROPERTY:
                # The OWL API does not include a method to retrieve annotation
                # subproperty axioms by the parent property, so we instead
                # examine all annotation subproperty axioms to see which ones
                # have the current entity as a superproperty.
                axioms = self.owlont.getAxioms(
                    AxiomType.SUB_ANNOTATION_PROPERTY_OF, True
                )
                for axiom in axioms:
                    if axiom.getSuperProperty().equals(entity):
                        br_axiomset.add(axiom)

                        # Check whether the child property has already been
                        # processed so we don't get stuck in cyclic
                        # relationship graphs.
                        subprop = axiom.getSubProperty()
                        if not(subprop in br_entset):
                            entstack.append(subprop)

        return (br_entset, br_axiomset)

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

                    if target.getExistingAnnotationProperty(prop_iri) == None:
                        annot_ent = self.ontology.getExistingAnnotationProperty(prop_iri)
                        # Built-in annotation properties, such as rdfs:label,
                        # will not "exist" because they have no declaration
                        # axioms, so we need to check for this.
                        if annot_ent != None:
                            signature.add(annot_ent.getOWLAPIObj())

