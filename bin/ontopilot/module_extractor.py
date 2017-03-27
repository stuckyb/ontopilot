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


# Define constants for the supported extraction methods.
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

