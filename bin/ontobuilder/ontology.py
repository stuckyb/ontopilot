#
# Provides a convenience Ontology class that implements a high-level interface
# for interacting with an OWL ontology.
#

# Python imports.
from idresolver import IDResolver
from ontology_entities import _OntologyClass, _OntologyDataProperty
from ontology_entities import _OntologyObjectProperty, _OntologyAnnotationProperty
from reasoner_manager import ReasonerManager
from observable import Observable

# Java imports.
from java.io import File, FileOutputStream
from java.util import HashSet
from org.semanticweb.owlapi.apibinding import OWLManager
from org.semanticweb.owlapi.model import IRI, OWLOntologyID
from org.semanticweb.owlapi.model import AddAxiom, AddImport, RemoveImport
from org.semanticweb.owlapi.model import SetOntologyID, AxiomType, OWLOntology
from org.semanticweb.owlapi.model import AddOntologyAnnotation
from org.semanticweb.owlapi.formats import RDFXMLDocumentFormat
from uk.ac.manchester.cs.owlapi.modularity import SyntacticLocalityModuleExtractor
from uk.ac.manchester.cs.owlapi.modularity import ModuleType
from com.google.common.base import Optional
from org.semanticweb.owlapi.io import OWLOntologyCreationIOException
from org.semanticweb.owlapi.model import OWLOntologyFactoryNotFoundException
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum


class Ontology(Observable):
    """
    Provides a high-level interface to the OWL API's ontology object system.
    Conceptually, instances of this class represent a single OWL ontology.
    """
    # The IRI for the "dc:source" annotation property.
    SOURCE_PROP_IRI = IRI.create('http://purl.org/dc/elements/1.1/source')

    # The IRI for inferred axiom annotation.
    INFERRED_ANNOT_IRI = IRI.create(
        'http://www.geneontology.org/formats/oboInOwl#is_inferred'
    )

    def __init__(self, ontology_source):
        """
        Initialize this Ontology instance.  The argument "ontology_source"
        should either be a path to an OWL ontology file on the local file
        system or an instance of an OWL API OWLOntology object.
        """
        if isinstance(ontology_source, basestring): 
            # Load the ontology from the source file.
            self.ontman = OWLManager.createOWLOntologyManager()
            ontfile = File(ontology_source)
            self.ontology = self.ontman.loadOntologyFromOntologyDocument(ontfile)
        elif isinstance(ontology_source, OWLOntology):
            self.ontology = ontology_source
            self.ontman = self.ontology.getOWLOntologyManager()
        else:
            raise RuntimeError('Unrecognized type for initializing an Ontology object: '
                + str(ontology_source))

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
        string containing: a label (with or without a prefix), a prefix IRI
        (i.e., a curie, such as "owl:Thing"), a relative IRI, a full IRI, a
        label (either with or without an OBO or IRI prefix), or an OBO ID
        (e.g., a string of the form "PO:0000003").  Returns an OWL API IRI
        object.  Labels, except for their prefix, must be enclosed in single
        quotes (e.g., 'some label' or prefix:'some label').  This method
        delegates to an IDResolver instance.

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
        if prop == None:
            prop = self.getExistingAnnotationProperty(propIRI)
        if prop == None:
            prop = self.getExistingDataProperty(propIRI)

        # If no matching data property was found, prop == None.
        return prop

    def getExistingEntity(self, ent_id):
        """
        Searches for an entity in the ontology using an identifier.  The entity
        is assumed to be either a class, object property, data property, or
        annotation property.  Both the main ontology and its imports closure
        are searched for the target entity.  If the entity is found, an
        _OntologyEntity object representing the entity is returned.  Otherwise,
        None is returned.
        
        ent_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a label (with or without a prefix),
            a prefix IRI (i.e., a curie, such as "owl:Thing"), a relative IRI,
            a full IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
            Labels should be enclosed in single quotes (e.g., 'label text' or
            prefix:'label txt').
        """
        eIRI = self.resolveIdentifier(ent_id)

        entity = self.getExistingClass(eIRI)
        if entity == None:
            entity = self.getExistingProperty(eIRI)

        # If no matching data property was found, entity == None.
        return entity

    def getExistingIndividual(self, indv_id):
        """
        Searches for an existing individual in the ontology.  If the individual
        is declared either directly in the ontology or is declared in its
        transitive imports closure, an OWL API object representing the
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
                return indvobj

        return None

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

    def addTermAxiom(self, owl_axiom):
        """
        Adds a new term axiom to this ontology.  In this context, "term axiom"
        means an axiom with an OWL class or property as its subject.  The
        argument "owl_axiom" should be an instance of an OWL API axiom object.
        """
        # If this is a label annotation, notify observers about the new label.
        if owl_axiom.isOfType(AxiomType.ANNOTATION_ASSERTION):
            if owl_axiom.getProperty().isLabel():
                labeltxt = owl_axiom.getValue().getLiteral()

                # If we are adding a label, we should be guaranteed that the
                # subject of the annotation is an IRI (i.e, not anonymous).
                subjIRI = owl_axiom.getSubject()
                if not(isinstance(subjIRI, IRI)):
                    raise RuntimeError('Attempted to add the label "'
                        + labeltxt + '" as an annotation of an anonymous class.')
                self.notifyObservers('label_added', (labeltxt, subjIRI))

        self.ontman.applyChange(AddAxiom(self.ontology, owl_axiom))

    def removeEntity(self, entity, remove_annotations=True):
        """
        Removes an entity from the ontology (including its imports closure).
        Optionally, any annotations referencing the deleted entity can also be
        removed (this is the default behavior).

        entity: An OWL API entity object.
        remove_annotations: If True, annotations referencing the entity will
            also be removed.
        """
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
                            if asubject.equals(entity.getIRI()):
                                del_axioms.add(axiom)
                # See if this axiom includes the target entity (e.g., a
                # declaration axiom for the target entity).
                elif axiom.getSignature().contains(entity):
                    del_axioms.add(axiom)

            self.ontman.removeAxioms(ont, del_axioms)

    def setOntologyID(self, ont_iri, version_iri=''):
        """
        Sets the ID for the ontology (i.e., the values of the ontology IRI and
        version IRI).
        
        ont_iri: The IRI (i.e., ID) of the ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
        version_iri: The version IRI of the ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
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

        source_iri: The IRI of the source ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
        load_import: If True, the new import will be automatically loaded and
            its terms labels will be added to the internal LabelMap.
        """
        sourceIRI = self.idr.expandIRI(source_iri)
        owlont = self.getOWLOntology()
        
        # Check if the imported ontology is already included in an imports
        # declaration.  If so, there's nothing to do.
        if owlont.getDirectImportsDocuments().contains(sourceIRI):
            return

        importdec = self.df.getOWLImportsDeclaration(sourceIRI)
        self.ontman.applyChange(
            AddImport(owlont, importdec)
        )

        if load_import:
            # Manually load the newly added import.
            try:
                importont = self.ontman.loadOntology(sourceIRI)
            except (
                OWLOntologyFactoryNotFoundException,
                OWLOntologyCreationIOException
            ) as err:
                raise RuntimeError('The import module ontology at <{0}> could not be loaded.  Please make sure that the IRI is correct and that the import module ontology is accessible.'.format(source_iri))

            # Notify observers that a new ontology was imported.
            self.notifyObservers('ontology_added', (importont,))

    def mergeOntology(self, source_iri):
        """
        Merges the axioms from an external ontology into this ontology.  Also
        manages collisions with import declarations, so that if the merged
        ontology is declared as an import in the target ontology (i.e., this
        ontology), the import declaration will be deleted.

        source_iri: The IRI of the source ontology.  Can be either an IRI
            object or a string containing a relative IRI, prefix IRI, or full
            IRI.
        """
        sourceIRI = self.idr.expandIRI(source_iri)
        owlont = self.getOWLOntology()

        try:
            importont = self.ontman.loadOntology(sourceIRI)
        except (
            OWLOntologyFactoryNotFoundException,
            OWLOntologyCreationIOException
        ) as err:
            raise RuntimeError('The import module ontology at <{0}> could not be loaded.  Please make sure that the IRI is correct and that the import module ontology is accessible.'.format(source_iri))

        # Add the axioms from the external ontology to this ontology.
        axiomset = importont.getAxioms(ImportsEnum.EXCLUDED)
        self.ontman.addAxioms(owlont, axiomset)

        # See if the merged ontology was already in the imports declarations
        # for the target ontology; if so, remove it.  Do this by gathering
        # invalidated imports declarations into a set so that they can be
        # deleted after looping over an ontology's imports declarations rather
        # than in the loop, to avoid the risk of invalidating the iteration.
        del_decs = HashSet()
        for importsdec in owlont.getImportsDeclarations():
            if importsdec.getIRI().equals(sourceIRI):
                del_decs.add(importsdec)

        for dec in del_decs:
            self.ontman.applyChange(RemoveImport(owlont, dec))

        if del_decs.isEmpty():
            # If the merged ontology was not already imported, notify observers
            # about the merged ontology.
            self.notifyObservers('ontology_added', (importont,))

    def checkEntailmentErrors(self):
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
        reasoner = self.getReasonerManager().getReasoner('hermit')

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

        sourceprop = self.df.getOWLAnnotationProperty(self.SOURCE_PROP_IRI)
        s_annot = self.df.getOWLAnnotation(sourceprop, sourceIRI)
        self.ontman.applyChange(
            AddOntologyAnnotation(self.getOWLOntology(), s_annot)
        )

    def saveOntology(self, filepath):
        """
        Saves the ontology to a file.
        """
        oformat = RDFXMLDocumentFormat()
        foutputstream = FileOutputStream(File(filepath))
        self.ontman.saveOntology(self.ontology, oformat, foutputstream)
        foutputstream.close()

    def extractModule(self, signature, mod_iri):
        """
        Extracts a module that is a subset of the entities in this ontology.
        The result is returned as an Ontology object.

        signature: A Java Set of all entities to include in the module.
        mod_iri: The IRI for the extracted ontology module.  Can be either an
            IRI object or a string containing a relative IRI, prefix IRI, or
            full IRI.
        """
        modIRI = self.idr.expandIRI(mod_iri)

        slme = SyntacticLocalityModuleExtractor(
            self.ontman, self.getOWLOntology(), ModuleType.STAR
        )
        modont = Ontology(slme.extractAsOntology(signature, modIRI))

        # Add an annotation for the source of the module.
        sourceIRI = None
        ontid = self.getOWLOntology().getOntologyID()
        if ontid.getVersionIRI().isPresent():
            sourceIRI = ontid.getVersionIRI().get()
        elif ontid.getOntologyIRI().isPresent():
            sourceIRI = ontid.getOntologyIRI().get()

        if sourceIRI != None:
            modont.setOntologySource(sourceIRI)

        return modont

