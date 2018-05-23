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

#
# Provides a convenience Ontology class that implements a high-level interface
# for interacting with an OWL ontology.
#

# Python imports.
from __future__ import unicode_literals
from ontopilot import logger
import oom_manager
from idresolver import IDResolver
from ontology_entities import _OntologyClass, _OntologyDataProperty
from ontology_entities import _OntologyObjectProperty, _OntologyAnnotationProperty
from ontology_entities import _OntologyIndividual, _OntologyEntity
from reasoner_manager import ReasonerManager
from observable import Observable
import nethelper

# Java imports.
from java.io import File, FileOutputStream, InputStream
from java.lang import System as JavaSystem
from java.util import HashSet
from org.semanticweb.owlapi.apibinding import OWLManager
from org.semanticweb.owlapi.model import IRI, OWLOntologyID
from org.semanticweb.owlapi.model import AddAxiom, AddImport, RemoveImport
from org.semanticweb.owlapi.model import SetOntologyID, AxiomType, OWLOntology
from org.semanticweb.owlapi.model import AddOntologyAnnotation
from org.semanticweb.owlapi.formats import (
    RDFXMLDocumentFormat, TurtleDocumentFormat, OWLXMLDocumentFormat,
    ManchesterSyntaxDocumentFormat
)
from com.google.common.base import Optional
from org.semanticweb.owlapi.model import OWLOntologyDocumentAlreadyExistsException
from org.semanticweb.owlapi.model import OWLOntologyAlreadyExistsException
from org.semanticweb.owlapi.io import OWLOntologyCreationIOException
from org.semanticweb.owlapi.model import OWLOntologyFactoryNotFoundException
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum


# Define constants for the supported output formats.
OUTPUT_FORMATS = ('RDF/XML', 'Turtle', 'OWL/XML', 'Manchester')


class Ontology(Observable):
    """
    Provides a high-level interface to the OWL API's ontology object system.
    Conceptually, instances of this class represent a single OWL ontology.
    """
    # The IRI for the "dc:source" annotation property.
    SOURCE_ANNOT_IRI = IRI.create('http://purl.org/dc/elements/1.1/source')

    # The IRI for inferred axiom annotations.
    INFERRED_ANNOT_IRI = IRI.create(
        'http://www.geneontology.org/formats/oboInOwl#is_inferred'
    )

    # The IRI for the 'imported from' annotation property.
    IMPORTED_FROM_IRI = IRI.create(
        'http://purl.obolibrary.org/obo/IAO_0000412'
    )

    def __init__(self, ontology_source=None):
        """
        Initialize this Ontology instance.  The argument "ontology_source"
        should either be a path to an OWL ontology file on the local file
        system, an instance of an OWL API OWLOntology object, or a Java
        InputStream.  If ontology_source is not provided (i.e., is None), an
        "empty" ontology will be created.
        """
        if isinstance(ontology_source, InputStream):
            # Load the ontology from the InputStream.
            self.ontman = oom_manager.getNewOWLOntologyManager()
            self.ontology = self.ontman.loadOntologyFromOntologyDocument(
                ontology_source
            )
        elif isinstance(ontology_source, basestring): 
            # Load the ontology from the source file.
            self.ontman = oom_manager.getNewOWLOntologyManager()
            self.ontology = self.ontman.loadOntologyFromOntologyDocument(
                File(ontology_source)
            )
        elif isinstance(ontology_source, OWLOntology):
            self.ontology = ontology_source
            self.ontman = self.ontology.getOWLOntologyManager()
        elif ontology_source is None:
            self.ontman = oom_manager.getNewOWLOntologyManager()
            self.ontology = self.ontman.createOntology()
        else:
            raise RuntimeError(
                'Unrecognized type for initializing an Ontology object: '
                '{0}.'.format(ontology_source)
            )

        # Create an OWL data factory, which is required for creating new OWL
        # entities and looking up existing entities.
        self.df = OWLManager.getOWLDataFactory()

        self.reasonerman = ReasonerManager(self)

        # Define the events that external observers can watch.  The events are
        # as follows.
        # "label_added": Triggers any time a label axiom is added to the
        #   ontology.  Arguments are the label text and subject IRI.
        # "ontology_added": Triggers any time an external ontology is added
        #   to this ontology, either by importing it or merging it.  The single
        #   argument is the external ontology instance.
        self.defineObservableEvents(['label_added', 'ontology_added'])

        self.idr = IDResolver(self)

    def getOWLOntology(self):
        """
        Returns the OWL API ontology object contained by this Ontology object.
        """
        return self.ontology

    def getOntologyManager(self):
        """
        Returns the OWL API ontology manager object contained by this Ontology.
        """
        return self.ontman

    def getReasonerManager(self):
        """
        Returns a ReasonerManager instance for this ontology.
        """
        return self.reasonerman

    def resolveLabel(self, labeltxt):
        """
        Resolves an entity label (either with or without a prefix) to an
        absolute IRI.  The label, excluding its prefix, must be enclosed in
        single quotes (e.g., 'some label' or prefix:'some label').  This method
        delegates to an IDResolver instance.

        labeltxt: The label to resolve.
        Returns: An OWL API IRI object.
        """
        return self.idr.resolveLabel(labeltxt)

    def resolveIdentifier(self, id_obj):
        """
        Converts an object representing an identifier into a fully expanded
        IRI.  The argument id_obj can be either an OWL API IRI object or a
        string containing: a prefix IRI (i.e., a curie, such as "owl:Thing"), a
        relative IRI, a full IRI, a label (either with or without an OBO or IRI
        prefix), or an OBO ID (e.g., a string of the form "PO:0000003").
        Returns an OWL API IRI object.  Labels, except for their prefix, must
        be enclosed in single quotes (e.g., 'some label' or prefix:'some
        label').  This method delegates to an IDResolver instance.

        id_obj: The identifier to resolve to an absolute IRI.
        Returns: An OWL API IRI object.
        """
        return self.idr.resolveIdentifier(id_obj)

    def getExistingClass(self, class_id):
        """
        Searches for an existing class in the ontology.  If the class is
        declared either directly in the ontology or is declared in its
        transitive imports closure, an _OntologyEntity object representing the
        class is returned.  Otherwise, None is returned.

        class_id: The identifier of the class to search for.  Can be either an
            OWL API IRI object or a string containing: a label (with or without
            a prefix), a prefix IRI (i.e., a curie, such as "owl:Thing"), a
            relative IRI, a full IRI, or an OBO ID (e.g., a string of the form
            "PO:0000003").  Labels should be enclosed in single quotes (e.g.,
            'label text' or prefix:'label txt').
        """
        classIRI = self.resolveIdentifier(class_id)

        classobj = self.df.getOWLClass(classIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(classobj).size() > 0:
                return _OntologyClass(classIRI, classobj, self)

        return None

    def getExistingDataProperty(self, prop_id):
        """
        Searches for an existing data property in the ontology.  If the
        property is declared either directly in the ontology or is declared in
        its transitive imports closure, an _OntologyDataProperty object
        representing the property is returned.  Otherwise, None is returned.

        prop_id: The identifier of the property to search for.  Can be either
            an OWL API IRI object or a string containing: a label (with or
            without a prefix), a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a relative IRI, a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").  Labels should be enclosed in
            single quotes (e.g., 'label text' or prefix:'label txt').
        """
        propIRI = self.resolveIdentifier(prop_id)

        propobj = self.df.getOWLDataProperty(propIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(propobj).size() > 0:
                return _OntologyDataProperty(propIRI, propobj, self)

        return None

    def getExistingObjectProperty(self, prop_id):
        """
        Searches for an existing object property in the ontology.  If the
        property is declared either directly in the ontology or is declared in
        its transitive imports closure, an _OntologyObjectProperty object
        representing the property is returned.  Otherwise, None is returned.

        prop_id: The identifier of the property to search for.  Can be either
            an OWL API IRI object or a string containing: a label (with or
            without a prefix), a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a relative IRI, a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").  Labels should be enclosed in
            single quotes (e.g., 'label text' or prefix:'label txt').
        """
        propIRI = self.resolveIdentifier(prop_id)

        propobj = self.df.getOWLObjectProperty(propIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(propobj).size() > 0:
                return _OntologyObjectProperty(propIRI, propobj, self)

        return None

    def getExistingAnnotationProperty(self, prop_id):
        """
        Searches for an existing annotation property in the ontology.  If the
        property is declared either directly in the ontology or is declared in
        its transitive imports closure, an _OntologyAnnotationProperty object
        representing the property is returned.  Otherwise, None is returned.

        prop_id: The identifier of the property to search for.  Can be either
            an OWL API IRI object or a string containing: a label (with or
            without a prefix), a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a relative IRI, a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").  Labels should be enclosed in
            single quotes (e.g., 'label text' or prefix:'label txt').
        """
        propIRI = self.resolveIdentifier(prop_id)

        propobj = self.df.getOWLAnnotationProperty(propIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(propobj).size() > 0:
                return _OntologyAnnotationProperty(propIRI, propobj, self)

        return None

    def getExistingProperty(self, prop_id):
        """
        Searches for an existing property in the ontology.  If the property is
        declared either directly in the ontology or is declared in its
        transitive imports closure, an _OntologyEntity object representing the
        property is returned.  Otherwise, None is returned.  Object properties,
        data properties, and annotation properties are all considered; ontology
        properties are not.

        prop_id: The identifier of the property to search for.  Can be either
            an OWL API IRI object or a string containing: a label (with or
            without a prefix), a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a relative IRI, a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").  Labels should be enclosed in
            single quotes (e.g., 'label text' or prefix:'label txt').
        """
        propIRI = self.resolveIdentifier(prop_id)

        prop = self.getExistingObjectProperty(propIRI)
        if prop is None:
            prop = self.getExistingAnnotationProperty(propIRI)
        if prop is None:
            prop = self.getExistingDataProperty(propIRI)

        # If no matching data property was found, prop is None.
        return prop

    def getExistingIndividual(self, indv_id):
        """
        Searches for an existing named individual in the ontology.  If the
        individual is declared either directly in the ontology or is declared
        in its transitive imports closure, an OWL API object representing the
        individual is returned.  Otherwise, None is returned.

        indv_id: The identifier of the individual to search for.  Can be either
            an OWL API IRI object or a string containing: a label (with or
            without a prefix), a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a relative IRI, a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").  Labels should be enclosed in
            single quotes (e.g., 'label text' or prefix:'label txt').
        """
        indvIRI = self.resolveIdentifier(indv_id)

        indvobj = self.df.getOWLNamedIndividual(indvIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(indvobj).size() > 0:
                return _OntologyIndividual(indvIRI, indvobj, self)

        return None

    def getExistingEntity(self, ent_id):
        """
        Searches for an entity in the ontology using an identifier.  The entity
        is assumed to be either a class, object property, data property,
        annotation property, or named individual.  Both the main ontology and
        its imports closure are searched for the target entity.  If the entity
        is found, an _OntologyEntity object representing the entity is
        returned.  Otherwise, None is returned.
        
        ent_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a label (with or without a prefix),
            a prefix IRI (i.e., a curie, such as "owl:Thing"), a relative IRI,
            a full IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label text' or
            prefix:'label txt').
        """
        eIRI = self.resolveIdentifier(ent_id)

        entity = self.getExistingClass(eIRI)
        if entity is None:
            entity = self.getExistingProperty(eIRI)
        if entity is None:
            entity = self.getExistingIndividual(eIRI)

        # If no matching individual was found, entity is None.
        return entity

    def createNewClass(self, class_id):
        """
        Creates a new OWL class, adds it to the ontology, and returns an
        associated _OntologyClass object.

        class_id: The identifier for the new class.  Can be either an OWL API
            IRI object or a string containing: a prefix IRI (i.e., a curie,
            such as "owl:Thing"), a full IRI, a relative IRI, or an OBO ID
            (e.g., a string of the form "PO:0000003").
        """
        classIRI = self.idr.resolveNonlabelIdentifier(class_id)

        # Get the class object.
        owlclass = self.df.getOWLClass(classIRI)

        declaxiom = self.df.getOWLDeclarationAxiom(owlclass)
        self.ontman.applyChange(AddAxiom(self.ontology, declaxiom))

        return _OntologyClass(classIRI, owlclass, self)
    
    def createNewDataProperty(self, prop_id):
        """
        Creates a new OWL data property, adds it to the ontology, and returns
        an associated _OntologyDataProperty object.

        prop_iri: The identifier for the new property.  Can be either an OWL
            API IRI object or a string containing: a prefix IRI (i.e., a curie,
            such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of
            the form "PO:0000003").
        """
        propIRI = self.idr.resolveNonlabelIdentifier(prop_id)

        owldprop = self.df.getOWLDataProperty(propIRI)

        declaxiom = self.df.getOWLDeclarationAxiom(owldprop)
        self.ontman.applyChange(AddAxiom(self.ontology, declaxiom))

        return _OntologyDataProperty(propIRI, owldprop, self)

    def createNewObjectProperty(self, prop_id):
        """
        Creates a new OWL object property, adds it to the ontology, and returns
        an associated _OntologyObjectProperty object.

        prop_iri: The identifier for the new property.  Can be either an OWL
            API IRI object or a string containing: a prefix IRI (i.e., a curie,
            such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of
            the form "PO:0000003").
        """
        propIRI = self.idr.resolveNonlabelIdentifier(prop_id)

        owloprop = self.df.getOWLObjectProperty(propIRI)

        declaxiom = self.df.getOWLDeclarationAxiom(owloprop)
        self.ontman.applyChange(AddAxiom(self.ontology, declaxiom))

        return _OntologyObjectProperty(propIRI, owloprop, self)

    def createNewAnnotationProperty(self, prop_id):
        """
        Creates a new OWL annotation property, adds it to the ontology, and
        returns an associated _OntologyAnnotationProperty object.

        prop_iri: The identifier for the new property.  Can be either an OWL
            API IRI object or a string containing: a prefix IRI (i.e., a curie,
            such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of
            the form "PO:0000003").
        """
        propIRI = self.idr.resolveNonlabelIdentifier(prop_id)

        owloprop = self.df.getOWLAnnotationProperty(propIRI)

        declaxiom = self.df.getOWLDeclarationAxiom(owloprop)
        self.ontman.applyChange(AddAxiom(self.ontology, declaxiom))

        return _OntologyAnnotationProperty(propIRI, owloprop, self)

    def createNewIndividual(self, individual_id):
        """
        Creates a new OWL named individual, adds it to the ontology, and
        returns an associated _OntologyIndividual object.

        individual_id: The identifier for the new individual.  Can be either an
            OWL API IRI object or a string containing: a prefix IRI (i.e., a
            curie, such as "owl:Thing"), a full IRI, a relative IRI, or an OBO
            ID (e.g., a string of the form "PO:0000003").
        """
        individualIRI = self.idr.resolveNonlabelIdentifier(individual_id)

        # Get the individual object.
        owlobj = self.df.getOWLNamedIndividual(individualIRI)

        declaxiom = self.df.getOWLDeclarationAxiom(owlobj)
        self.ontman.applyChange(AddAxiom(self.ontology, declaxiom))

        return _OntologyIndividual(individualIRI, owlobj, self)
    
    def addEntityAxiom(self, owl_axiom):
        """
        Adds a new entity axiom to this ontology.  In this context, "entity
        axiom" means an axiom with an OWL class, property, or individual as its
        subject.  The argument "owl_axiom" should be an instance of an OWL API
        axiom object.
        """
        if owl_axiom.isOfType(AxiomType.ANNOTATION_ASSERTION):
            if owl_axiom.getProperty().isLabel():
                labeltxt = owl_axiom.getValue().getLiteral()

                # If we are adding a label, we should be guaranteed that the
                # subject of the annotation is an IRI (i.e, not anonymous).
                subjIRI = owl_axiom.getSubject()
                if not(isinstance(subjIRI, IRI)):
                    raise RuntimeError('Attempted to add the label "'
                        + labeltxt + '" as an annotation of an anonymous class.')

                # Notify observers about the new label.
                self.notifyObservers('label_added', (labeltxt, subjIRI))

        self.ontman.applyChange(AddAxiom(self.ontology, owl_axiom))

    def removeEntity(self, entity, remove_annotations=True):
        """
        Removes an entity from the ontology (including its imports closure).
        Optionally, any annotations referencing the deleted entity can also be
        removed (this is the default behavior).

        entity: An _OntologyEntity object or an OWL API entity object.
        remove_annotations: If True, annotations referencing the entity will
            also be removed.
        """
        if isinstance(entity, _OntologyEntity):
            owlent = entity.getOWLAPIObj()
        else:
            owlent = entity

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            # A set for gathering axioms to remove so that axioms can be
            # deleted after looping over an ontology's axioms rather than in
            # the loop, to avoid the risk of invalidating the iteration.
            del_axioms = HashSet()

            for axiom in ont.getAxioms():
                # See if this axiom is an annotation axiom.
                if axiom.getAxiomType() == AxiomType.ANNOTATION_ASSERTION:
                    if remove_annotations:
                        # Check if this annotation axiom refers to the target
                        # entity.
                        asubject = axiom.getSubject()
                        if isinstance(asubject, IRI):
                            if asubject.equals(owlent.getIRI()):
                                del_axioms.add(axiom)
                # See if this axiom includes the target entity (e.g., a
                # declaration axiom for the target entity).
                elif axiom.getSignature().contains(owlent):
                    del_axioms.add(axiom)

            self.ontman.removeAxioms(ont, del_axioms)

    def setOntologyID(self, ont_iri, version_iri=''):
        """
        Sets the ID for the ontology (i.e., the values of the ontology IRI and
        version IRI).
        
        ont_iri: The IRI (i.e., ID) of the ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
        version_iri (optional): The version IRI of the ontology.  Can be either
            an IRI object or a string containing a relative IRI, prefix IRI, or
            full IRI.
        """
        ontIRI = self.idr.expandIRI(ont_iri)

        if version_iri != '':
            verIRI = self.idr.expandIRI(version_iri)
        else:
            verIRI = None

        newoid = OWLOntologyID(
            Optional.fromNullable(ontIRI), Optional.fromNullable(verIRI)
        )
        self.ontman.applyChange(SetOntologyID(self.ontology, newoid))

    def hasImport(self, import_iri):
        """
        Returns True if this ontology has the specified ontology as a direct
        import.  Returns False otherwise.

        import_iri: The IRI of an ontology.  Can be either an IRI object or a
            string containing a relative IRI, prefix IRI, or full IRI.
        """
        importIRI = self.idr.expandIRI(import_iri)
        owlont = self.getOWLOntology()
        
        return owlont.getDirectImportsDocuments().contains(importIRI)

    def getImports(self):
        """
        Returns a list of the IRIs of ontologies that are imported into this
        ontology (i.e., via OWL import statements).
        """
        importslist = list(self.ontology.getDirectImportsDocuments())

        return importslist

    def addImport(self, source_iri, load_import=True):
        """
        Adds an OWL import statement to this ontology.

        source_iri: The IRI of the source ontology.  If there is no mapping of
            the source ontology IRI to a document IRI, then the ontology IRI is
            assumed to also be the document IRI.  Can be either an IRI object
            or a string containing a relative IRI, prefix IRI, or full IRI.
        load_import: If True, the new import will be automatically loaded and
            its terms labels will be added to the internal LabelMap.
        """
        sourceIRI = self.idr.expandIRI(source_iri)
        owlont = self.getOWLOntology()

        # First, check if the ontology IRI maps to a different document IRI.
        docIRI = oom_manager.lookupDocumentIRI(self.ontman, sourceIRI)
        if docIRI is None:
            docIRI = sourceIRI
        
        # Check if the imported ontology is already included as an import.  If
        # so, there's nothing to do.
        importdocs = owlont.getDirectImportsDocuments()
        if importdocs.contains(docIRI):
            return

        # Check if the import IRI redirects to another URI, in which case get
        # the true location and check if *it* is already included as an import.
        redir_iri = nethelper.checkForRedirect(docIRI)
        if redir_iri != '':
            if importdocs.contains(IRI.create(redir_iri)):
                return

        importdec = self.df.getOWLImportsDeclaration(sourceIRI)
        self.ontman.applyChange(
            AddImport(owlont, importdec)
        )

        if load_import:
            # Manually load the newly added import.
            try:
                # The call to makeLoadImportRequest() might seem redundant, and
                # in general, it is redundant if the new import's document IRI
                # is the same as its ontology IRI.  However, if those IRIs
                # differ, then without explicitly calling
                # makeLoadImportRequest(), the new import will not show up in
                # the main ontology's imports closure (true as of version 4.2.4
                # of the OWL API).  I examined the OWL API source code and
                # confirmed that if the ontology has already been loaded when
                # makeLoadImportRequest() is called, the already-loaded version
                # of the ontology is used (that is, it is not parsed again), so
                # these method calls should not hurt performance.
                importont = self.ontman.getOntology(sourceIRI)
                if importont is None:
                    importont = self.ontman.loadOntology(sourceIRI)
                self.ontman.makeLoadImportRequest(importdec)

            except (
                OWLOntologyFactoryNotFoundException,
                OWLOntologyCreationIOException
            ) as err:
                raise RuntimeError(
                    'The import ontology at <{0}> could not be loaded.  '
                    'Please make sure that the IRI is correct and that the '
                    'import ontology is accessible.'.format(source_iri)
                )

            # Notify observers that a new ontology was imported.
            self.notifyObservers('ontology_added', (importont,))

    def updateImportIRI(self, old_iri, new_iri):
        """
        Updates the IRI of an ontology that is a direct import of this
        ontology.  The *contents* of the ontology should be exactly the same;
        this method should only be used to update the IRI of an imported
        ontology if its location changes.  If the specified "old" IRI is not a
        direct import of this ontology, an exception is thrown.

        old_iri: The old IRI of the imported ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
        new_iri: The new IRI of the imported ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
        """
        oldIRI = self.idr.expandIRI(old_iri)
        newIRI = self.idr.expandIRI(new_iri)

        owlont = self.getOWLOntology()

        # Gather all import statements that refer to the old IRI.  Delete them
        # after looping over the ontology's imports declarations rather than in
        # the loop to avoid the risk of invalidating the iteration.
        del_decs = []
        for importsdec in owlont.getImportsDeclarations():
            if importsdec.getIRI().equals(oldIRI):
                del_decs.append(importsdec)

        if len(del_decs) == 0:
            raise RuntimeError(
                'The IRI <{0}> is not a direct import of the target ontology, '
                'so the import IRI could not be updated.'.format(old_iri)
            )

        # Delete the old declaration(s).
        for dec in del_decs:
            self.ontman.applyChange(RemoveImport(owlont, dec))

        # Add an import statement for the new IRI.
        importdec = self.df.getOWLImportsDeclaration(newIRI)
        self.ontman.applyChange(
            AddImport(owlont, importdec)
        )

    def _getImportedFromAnnotations(self, axiomset, sourceont):
        """
        For a given set of OWL API axioms, returns a set of annotation axioms
        that apply the 'imported from' annotation property (IAO:0000412), with
        the source ontology IRI as the annotation value, to all entities
        declared in the set of axioms.

        axiomset: A set of OWL API axioms.
        sourceont: An OWL API ontology object.
        """
        sourceIRI = None

        # By default, use the source ontology IRI as the value for the
        # 'imported from' annotations.
        if sourceont.getOntologyID().getOntologyIRI().isPresent():
            sourceIRI = sourceont.getOntologyID().getOntologyIRI().get()

        # Check if the source ontology has a "dc:source" annotation.  If so,
        # use that for the value of the 'imported from' annotations.
        for ont_annot in sourceont.getAnnotations():
            if ont_annot.getProperty().getIRI().equals(self.SOURCE_ANNOT_IRI):
                if ont_annot.getValue().asIRI().isPresent():
                    sourceIRI = ont_annot.getValue().asIRI().get()

        # If we don't have a source IRI, there is no point in generating
        # 'imported from' annotations, so return an empty axiom set.
        if sourceIRI is None:
            return set()

        # Make sure that the 'imported from' annotation property is in the
        # ontology; if not, add it.
        annotprop = self.getExistingAnnotationProperty(self.IMPORTED_FROM_IRI)
        if annotprop is None:
            annotprop = self.createNewAnnotationProperty(self.IMPORTED_FROM_IRI)
            annotprop.addLabel('imported from')

        annotprop_oao = annotprop.getOWLAPIObj()

        annot_axioms = set()

        for axiom in AxiomType.getAxiomsOfTypes(
            axiomset, AxiomType.DECLARATION
        ):
            annot = self.df.getOWLAnnotation(annotprop_oao, sourceIRI)
            newaxiom = self.df.getOWLAnnotationAssertionAxiom(
                axiom.getEntity().getIRI(), annot
            )

            annot_axioms.add(newaxiom)

        return annot_axioms

    def mergeOntology(self, source_iri, annotate_merged=True):
        """
        Merges the axioms from an external ontology into this ontology.  Also
        manages collisions with import declarations, so that if the merged
        ontology is declared as an import in the target ontology (i.e., this
        ontology), the import declaration will be deleted.

        source_iri: The IRI of the source ontology.  If there is no mapping of
            the source ontology IRI to a document IRI, then the ontology IRI is
            assumed to also be the document IRI.  Can be either an IRI object
            or a string containing a relative IRI, prefix IRI, or full IRI.
        annotate_merged: If True, merged entities will be annotated with the
            'imported from' annotation property (IAO:0000412).
        """
        sourceIRI = self.idr.expandIRI(source_iri)
        owlont = self.getOWLOntology()

        importont = self.ontman.getOntology(sourceIRI)
        if importont is None:
            try:
                importont = self.ontman.loadOntology(sourceIRI)
            except OWLOntologyDocumentAlreadyExistsException as err:
                logger.warning(
                    'There was a problem with the IRI of the merged/imported '
                    'ontology located at <{0}>.  The expected ontology IRI, '
                    '<{1}>, appears to be incorrect.  Please confirm that the '
                    'expected ontology IRI matches the merged/imported '
                    'ontology\'s IRI declaration.'.format(
                        err.getOntologyDocumentIRI(), sourceIRI
                    )
                )
                try: 
                    # We know this call will fail because the ontology document
                    # already exists (per the previous exception), but it
                    # appears to be the only way to get the actual ID of the
                    # loaded ontology.
                    importont = self.ontman.loadOntologyFromOntologyDocument(
                        err.getOntologyDocumentIRI()
                    )
                except OWLOntologyAlreadyExistsException as err:
                    importont = self.ontman.getOntology(err.getOntologyID())
            except (
                OWLOntologyFactoryNotFoundException,
                OWLOntologyCreationIOException
            ) as err:
                raise RuntimeError(
                    'The import module ontology at <{0}> could not be loaded.  '
                    'Please make sure that the IRI is correct and that the '
                    'import module ontology is accessible.'.format(source_iri)
                )

        # Add the axioms from the external ontology to this ontology.
        axiomset = importont.getAxioms(ImportsEnum.EXCLUDED)
        self.ontman.addAxioms(owlont, axiomset)

        # If requested, add 'imported from' annotations for all entities in the
        # imported axioms.
        if (annotate_merged):
            if_axioms = self._getImportedFromAnnotations(axiomset, importont)
            self.ontman.addAxioms(owlont, if_axioms)

        # See if the merged ontology was already in the imports declarations
        # for the target ontology; if so, remove it.  Do this by gathering
        # invalidated imports declarations into a set so that they can be
        # deleted after looping over an ontology's imports declarations rather
        # than in the loop, to avoid the risk of invalidating the iteration.
        del_decs = []
        for importsdec in owlont.getImportsDeclarations():
            if importsdec.getIRI().equals(sourceIRI):
                del_decs.append(importsdec)

        for dec in del_decs:
            self.ontman.applyChange(RemoveImport(owlont, dec))

        if len(del_decs) == 0:
            # If the merged ontology was not already imported, notify observers
            # about the merged ontology.
            self.notifyObservers('ontology_added', (importont,))

    def checkEntailmentErrors(self, reasoner='HermiT'):
        """
        Checks for and reports two common entailment errors: inconsistency and
        incoherence.  Returns a report object that is a dictionary with two
        elements.  The first, 'is_consistent', is a boolean.  The second,
        'unsatisfiable_classes', is a list of all named unsatisfiable classes,
        excluding owl:Nothing.  Note that if an ontology is inconsistent, it is
        generally not possible to infer the unsatisfiable classes, so
        'unsatisfiable_classes' will always be empty.
        """
        report = {
            'unsatisfiable_classes': []
        }
        reasoner = self.getReasonerManager().getReasoner(reasoner)

        report['is_consistent'] = reasoner.isConsistent()

        if report['is_consistent']:
            # If the ontology is inconsistent, any attempts to reason over it
            # will throw exceptions.
            owlnothing = self.df.getOWLNothing()
            unsatisfiables = reasoner.getUnsatisfiableClasses().getEntities()
            for unsatisfiable in unsatisfiables:
                if not(unsatisfiable.equals(owlnothing)):
                    report['unsatisfiable_classes'].append(unsatisfiable)

        return report

    def setOntologySource(self, source_iri):
        """
        Sets the value of the "dc:source" annotation property for this ontology.

        source_iri: The IRI of the source ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
        """
        sourceIRI = self.idr.expandIRI(source_iri)

        sourceprop = self.df.getOWLAnnotationProperty(self.SOURCE_ANNOT_IRI)
        s_annot = self.df.getOWLAnnotation(sourceprop, sourceIRI)
        self.ontman.applyChange(
            AddOntologyAnnotation(self.getOWLOntology(), s_annot)
        )

    def _writeToStream(self, ostream, format_str):
        """
        An internal method that writes the ontology to the specified output
        stream.
        """
        lcformat_str = format_str.lower()
        if lcformat_str == 'rdf/xml':
            oformat = RDFXMLDocumentFormat()
        elif lcformat_str == 'turtle':
            oformat = TurtleDocumentFormat()
        elif lcformat_str == 'owl/xml':
            oformat = OWLXMLDocumentFormat()
        elif lcformat_str == 'manchester':
            oformat = ManchesterSyntaxDocumentFormat()
        else:
            raise RuntimeError(
                'Invalid ontology format string: "{0}".  Supported values '
                'are: {1}.'.format(
                    format_str, '"' + '", "'.join(OUTPUT_FORMATS) + '"'
                )
            )

        iformat = self.ontman.getOntologyFormat(self.ontology)
        if (
            iformat.isPrefixOWLOntologyFormat() and
            oformat.isPrefixOWLOntologyFormat()
        ):
            oformat.copyPrefixesFrom(iformat.asPrefixOWLOntologyFormat())

        self.ontman.saveOntology(self.ontology, oformat, ostream)

    def printOntology(self, format_str='RDF/XML'):
        """
        Prints the ontology to standard output.
        """
        self._writeToStream(JavaSystem.out, format_str)

    def saveOntology(self, filepath, format_str='RDF/XML'):
        """
        Saves the ontology to a file.
        """
        foutputstream = FileOutputStream(File(filepath))
        try:
            self._writeToStream(foutputstream, format_str)
        finally:
            foutputstream.close()

