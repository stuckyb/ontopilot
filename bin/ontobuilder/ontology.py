#
# Provides convenience classes that "wrap" OWL API classes and implement a
# higher-level interface for interacting with OWL ontologies.  The only class
# that should be directly instantiated by client code is Ontology.  Other
# functionality should be accessed through Ontology's public interface, except
# fo the two public convenience methods for converting OBO IDs to/from IRIs.
#

# Python imports.
from labelmap import LabelMap
from obohelper import isOboID, oboIDToIRI
from mshelper import ManchesterSyntaxParserHelper

# Java imports.
from java.io import File, FileOutputStream
from org.semanticweb.owlapi.apibinding import OWLManager
from org.semanticweb.owlapi.model import IRI, AddAxiom, OWLOntologyID
from org.semanticweb.owlapi.model import SetOntologyID, AxiomType, OWLOntology
from org.semanticweb.owlapi.model import AddOntologyAnnotation
from org.semanticweb.owlapi.model import OWLRuntimeException
from org.semanticweb.owlapi.formats import RDFXMLDocumentFormat
from org.semanticweb import HermiT
from uk.ac.manchester.cs.owlapi.modularity import SyntacticLocalityModuleExtractor
from uk.ac.manchester.cs.owlapi.modularity import ModuleType
from org.semanticweb.owlapi.manchestersyntax.renderer import ParserException
from com.google.common.base import Optional


class _OntologyClass:
    """
    Provides a high-level interface to the OWL API's ontology object system
    for OWL classes.  Conceptually, instances of this class represent a single
    OWL class in an OWL ontology.  This class should not be instantiated
    directly; instead, instances should be obtained through Ontology's public
    interface.
    """
    # The IRI for the property for definition annotations.
    DEFINITION_IRI = oboIDToIRI('IAO:0000115')

    def __init__(self, classIRI, classobj, ontology):
        """
        Initializes this _OntologyClass.

          class_iri: The IRI object of the class.
          classobj: The OWL API class object of the class.
          ontology: The ontology to which this class belongs.
        """
        self.ontology = ontology
        self.df = ontology.df
        self.classIRI = classIRI
        self.owlclass = classobj
        
    def addDefinition(self, deftxt):
        """
        Adds a definition annotation to this class (i.e., adds an annotation
        for "definition", IAO:0000115).
        """
        deftxt = deftxt.strip()

        defannot = self.df.getOWLAnnotation(
            self.df.getOWLAnnotationProperty(self.DEFINITION_IRI),
            self.df.getOWLLiteral(deftxt)
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.classIRI, defannot)

        self.ontology.addTermAxiom(annotaxiom)

    def addLabel(self, labeltxt):
        """
        Adds an rdfs:label for this class.
        """
        labeltxt = labeltxt.strip()

        labelannot = self.df.getOWLAnnotation(
            self.df.getRDFSLabel(), self.df.getOWLLiteral(labeltxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.classIRI, labelannot)

        self.ontology.addTermAxiom(annotaxiom)

    def addSuperclass(self, parent_id):
        """
        Adds a parent class for this class.

        parent_id: The identifier of the parent class.   Can be either an OWL
            API IRI object or a string containing: a prefix IRI (i.e., a curie,
            such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of
            the form "PO:0000003").
        """
        parentIRI = self.ontology.expandIdentifier(parent_id)

        # Get the OWLClass object of the parent class, making sure that it is
        # actually defined.
        parentclass = self.ontology.getExistingClass(parentIRI)
        if parentclass == None:
            raise RuntimeError('The designated superclass, ' + str(parent_id)
                    + ', could not be found in the source ontology.')
        
        # Add the subclass axiom to the ontology.
        newaxiom = self.df.getOWLSubClassOfAxiom(self.owlclass, parentclass)
        self.ontology.addTermAxiom(newaxiom)

    def addClassExpression(self, manchester_exp):
        """
        Adds a class expression as either an equivalency axiom or a subclass
        axiom.  The class expression should be written in Manchester Syntax.
        """
        formaldef = manchester_exp

        if formaldef != '':
            try:
                #self.ontology.mparser = ManchesterSyntaxTool(self.ontology.ontology)
                #cexp = self.ontology.mparser.parseManchesterExpression(formaldef)
                parser = ManchesterSyntaxParserHelper(self.ontology)
                cexp = parser.parseClassExpression(manchester_exp);
            except ParserException as err:
                print err
                raise RuntimeError('Error parsing "' + err.getCurrentToken()
                        + '" at line ' + str(err.getLineNumber()) + ', column '
                        + str(err.getColumnNumber())
                        + ' of the formal term definition (Manchester Syntax expected).')
            ecaxiom = self.df.getOWLEquivalentClassesAxiom(cexp, self.owlclass)
            self.ontology.addTermAxiom(ecaxiom)


class _OntologyDataProperty:
    """
    Provides a high-level interface to the OWL API's ontology object system
    for OWL data properties.  Conceptually, instances of this class represent a
    single OWL data property in an OWL ontology.  This class should not be
    instantiated directly; instead, instances should be obtained through
    Ontology's public interface.
    """
    # The IRI for the property for definition annotations.
    DEFINITION_IRI = oboIDToIRI('IAO:0000115')

    def __init__(self, propIRI, propobj, ontology):
        """
        Initializes this _OntologyClass.

          class_iri: The IRI object of the class.
          classobj: The OWL API class object of the class.
          ontology: The ontology to which this class belongs.
        """
        self.ontology = ontology
        self.df = ontology.df
        self.propIRI = propIRI
        self.propobj = propobj
        
    def addDefinition(self, deftxt):
        """
        Adds a definition annotation to this property (i.e., adds an annotation
        for "definition", IAO:0000115).
        """
        deftxt = deftxt.strip()

        defannot = self.df.getOWLAnnotation(
            self.df.getOWLAnnotationProperty(self.DEFINITION_IRI),
            self.df.getOWLLiteral(deftxt)
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.propIRI, defannot)

        self.ontology.addTermAxiom(annotaxiom)

    def addLabel(self, labeltxt):
        """
        Adds an rdfs:label for this property.
        """
        labeltxt = labeltxt.strip()

        labelannot = self.df.getOWLAnnotation(
            self.df.getRDFSLabel(), self.df.getOWLLiteral(labeltxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.propIRI, labelannot)

        self.ontology.addTermAxiom(annotaxiom)

    def addSuperproperty(self, parent_id):
        """
        Adds a parent property for this property.

        parent_id: The identifier of the parent property.  Can be either an OWL
            API IRI object or a string containing: a prefix IRI (i.e., a curie,
            such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of
            the form "PO:0000003").
        """
        parentIRI = self.ontology.expandIdentifier(parent_id)

        # Get the OWL property object of the parent class, making sure that it
        # is actually defined.
        parentprop = self.ontology.getExistingProperty(parentIRI)
        if parentprop == None:
            raise RuntimeError('The designated superproperty, ' + str(parent_id)
                    + ', could not be found in the source ontology.')

        # Add the subproperty axiom to the ontology.
        newaxiom = self.df.getOWLSubDataPropertyOfAxiom(self.propobj, parentprop)
        self.ontology.addTermAxiom(newaxiom)

    def setDomain(self, domain_id):
        """
        Sets the domain of this data property.

        domain_id: The identifier of a class.  Can be either an OWL API IRI
            object or a string containing: a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of the form
            "PO:0000003").
        """
        domainIRI = self.ontology.expandIdentifier(domain_id)

        # Get the class object for the domain.  We do not require that the
        # class is already declared, because properties might have to be
        # declared before the classes to which they apply.
        classobj = self.df.getOWLClass(domainIRI)

        # Add the declaration axiom.
        daxiom = self.df.getOWLDataPropertyDomainAxiom(self.propobj, classobj)
        self.ontology.addTermAxiom(daxiom)


class Ontology:
    """
    Provides a high-level interface to the OWL API's ontology object system.
    Conceptually, instances of this class represent a single OWL ontology.
    """
    # The IRI for the "dc:source" annotation property.
    SOURCE_PROP_IRI = IRI.create('http://purl.org/dc/elements/1.1/source')

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

        self.labelmap = LabelMap(self.ontology)

        # Create an OWL data factory, which is required for creating new OWL
        # entities and looking up existing entities.
        self.df = OWLManager.getOWLDataFactory()

    def __del__(self):
        """
        A class "destructor" that disposes the Manchester Syntax parser when
        this Ontology instance is no longer needed.
        """
        self.mparser.dispose()

    def getOWLOntology(self):
        """
        Returns the OWL API ontology object contained by this Ontology object.
        """
        return self.ontology

    def labelToIRI(self, labeltxt):
        """
        Given a class label, returns the associated class IRI.
        """
        try:
            cIRI = self.labelmap.lookupIRI(labeltxt)
        except KeyError:
            raise RuntimeError('The class label, "' + labeltxt
                + '", could not be matched to a term IRI.')

        return cIRI

    def expandIRI(self, iri):
        """
        If iri is a prefix IRI (i.e. a curie, such as "owl:Thing"), iri will be
        expanded using the prefixes defined in the ontology.  If the string is
        not a prefix IRI, then it is assumed to be a full IRI.

        iri: The IRI to expand.  Can be either a string or an OWL API IRI
            object.  In the latter case, iri is returned as is.

        TODO: Could use the "rfc3987" package to further validate IRI strings.
        """
        prefix_df = self.ontman.getOntologyFormat(self.ontology).asPrefixOWLOntologyFormat()

        if isinstance(iri, basestring):
            try:
                # If iri is not a prefix IRI, the OWL API will throw an
                # OWLRuntimeException.
                fullIRI = prefix_df.getIRI(iri)
            except OWLRuntimeException:
                fullIRI = IRI.create(iri)
        elif isinstance(iri, IRI):
            fullIRI = IRI
        else:
            raise RuntimeError('Unsupported type for conversion to IRI.')

        return fullIRI

    def expandIdentifier(self, id_obj):
        """
        Converts an object representing an identifier into a fully expanded
        IRI.  The argument id_obj can be either an OWL API IRI object or a
        string containing: a prefix IRI (i.e., a curie, such as "owl:Thing"),
        a full IRI, or an OBO ID (e.g., a string of the form "PO:0000003").
        Returns an OWL API IRI object.
        """
        if isinstance(id_obj, basestring):
            if isOboID(id_obj):
                IRIobj = oboIDToIRI(id_obj)
            else:
                IRIobj = self.expandIRI(id_obj)
        elif isinstance(id_obj, IRI):
            IRIobj = id_obj
        else:
            raise RuntimeError('Unsupported type for conversion to IRI.')

        return IRIobj

    def getEntityByID(self, ent_id):
        """
        Searches for an entity in the ontology using an identifier.  The entity
        is assumed to be either a class, object property, data property, or
        annotation property.
        
        ent_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of the form
            "PO:0000003").
        """
        eIRI = self.expandIdentifier(ent_id)

        entity = self.getExistingClass(eIRI)
        if entity == None:
            entity = self.getExistingProperty(eIRI)

        return entity

    def getExistingClass(self, class_id):
        """
        Searches for an existing class in the ontology.  If the class is
        declared either directly in the ontology or is declared in its
        transitive imports closure, an OWL API object representing the class is
        returned.  Otherwise, None is returned.

        class_id: The identifier of the class to search for.  Can be either an
            OWL API IRI object or a string containing: a prefix IRI (i.e., a
            curie, such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").
        """
        classIRI = self.expandIdentifier(class_id)

        classobj = self.df.getOWLClass(classIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(classobj).size() > 0:
                return classobj

        return None

    def getExistingDataProperty(self, prop_id):
        """
        Searches for an existing data property in the ontology.  If the
        property is declared either directly in the ontology or is declared in
        its transitive imports closure, an OWL API object representing the
        property is returned.  Otherwise, None is returned.

        prop_id: The identifier of the property to search for.  Can be either
            an OWL API IRI object or a string containing: a prefix IRI (i.e., a
            curie, such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").
        """
        propIRI = self.expandIdentifier(prop_id)

        propobj = self.df.getOWLDataProperty(propIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(propobj).size() > 0:
                return propobj

        return None

    def getExistingObjectProperty(self, prop_id):
        """
        Searches for an existing object property in the ontology.  If the
        property is declared either directly in the ontology or is declared in
        its transitive imports closure, an OWL API object representing the
        property is returned.  Otherwise, None is returned.

        prop_id: The identifier of the property to search for.  Can be either
            an OWL API IRI object or a string containing: a prefix IRI (i.e., a
            curie, such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").
        """
        propIRI = self.expandIdentifier(prop_id)

        propobj = self.df.getOWLObjectProperty(propIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(propobj).size() > 0:
                return propobj

        return None

    def getExistingProperty(self, prop_id):
        """
        Searches for an existing property in the ontology.  If the property is
        declared either directly in the ontology or is declared in its
        transitive imports closure, an OWL API object representing the property
        is returned.  Otherwise, None is returned.  Object properties, data
        properties, and annotation properties are all considered; ontology
        properties are not.

        prop_iri: The identifier of the property to search for.  Can be either
            an OWL API IRI object or a string containing: a prefix IRI (i.e., a
            curie, such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a
            string of the form "PO:0000003").
        """
        propIRI = self.expandIdentifier(prop_id)

        obj_prop = self.df.getOWLObjectProperty(propIRI)
        annot_prop = self.df.getOWLAnnotationProperty(propIRI)
        data_prop = self.df.getOWLDataProperty(propIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(obj_prop).size() > 0:
                return obj_prop
            elif ont.getDeclarationAxioms(annot_prop).size() > 0:
                return annot_prop
            elif ont.getDeclarationAxioms(data_prop).size() > 0:
                return data_prop

        return None

    def createNewClass(self, class_id):
        """
        Creates a new OWL class, adds it to the ontology, and returns an
        associated _OntologyClass object.

        class_id: The identifier for the new class.  Can be either an OWL API
            IRI object or a string containing: a prefix IRI (i.e., a curie,
            such as "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of
            the form "PO:0000003").
        """
        classIRI = self.expandIdentifier(class_id)

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
        propIRI = self.expandIdentifier(prop_id)

        owldprop = self.df.getOWLDataProperty(propIRI)

        declaxiom = self.df.getOWLDeclarationAxiom(owldprop)
        self.ontman.applyChange(AddAxiom(self.ontology, declaxiom))

        return _OntologyDataProperty(propIRI, owldprop, self)

    def preloadLabelIdPair(self, label_str, ent_id):
        """
        Preloads an entity's label and IRI into the label lookup table.  This
        allows label mappings to be specified prior to entity definition, which
        is necessary to support forward references to labels in term
        definitions.

        label_str: A string containing the label text.
        ent_id: The identifier of the entity.  Can be either an OWL API IRI
            object or a string containing: a prefix IRI (i.e., a curie, such as
            "owl:Thing"), a full IRI, or an OBO ID (e.g., a string of the form
            "PO:0000003").
        """
        entIRI = self.expandIdentifier(ent_id)
        self.labelmap.add(label_str, entIRI)

    def addTermAxiom(self, owl_axiom):
        """
        Adds a new term axiom to this ontology.  In this context, "term axiom"
        means an axiom with an OWL class or property as its subject.  The
        argument "owl_axiom" should be an instance of an OWL API axiom object.
        """
        # If this is a label annotation, update the label lookup dictionary.
        if owl_axiom.isOfType(AxiomType.ANNOTATION_ASSERTION):
            if owl_axiom.getProperty().isLabel():
                labeltxt = owl_axiom.getValue().getLiteral()

                # If we are adding a label, we should be guaranteed that the
                # subject of the annotation is an IRI (i.e, not anonymous).
                subjIRI = owl_axiom.getSubject()
                if not(isinstance(subjIRI, IRI)):
                    raise RuntimeError('Attempted to add the label "'
                        + labeltxt + '" as an annotation of an anonymous class.')
                self.labelmap.add(labeltxt, subjIRI)

        self.ontman.applyChange(AddAxiom(self.ontology, owl_axiom))

    def setOntologyID(self, ont_iri):
        """
        Sets the ID for the ontology (i.e., the value of the "rdf:about"
        attribute).
        
          ont_iri: The IRI (i.e., ID) of the ontology.  Can be either an IRI
                   object or a string.
        """
        ontIRI = self.expandIRI(ont_iri)

        newoid = OWLOntologyID(Optional.fromNullable(ontIRI), Optional.absent())
        self.ontman.applyChange(SetOntologyID(self.ontology, newoid))

    def setOntologySource(self, source_iri):
        """
        Sets the value of the "dc:source" annotation property for this ontology.

          source_iri: The IRI of the source ontology.  Can be either an IRI
                      object or a string.
        """
        sourceIRI = self.expandIRI(source_iri)

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

    def getHermitReasoner(self):
        """
        Returns an instance of a HermiT reasoner for this ontology.
        """
        rfact = HermiT.ReasonerFactory()

        return rfact.createReasoner(self.getOWLOntology())
    
    def extractModule(self, signature, mod_iri):
        """
        Extracts a module that is a subset of the entities in this ontology.
        The result is returned as an Ontology object.

        signature: A Java Set of all entities to include in the module.
        mod_iri: The IRI of the ontology module.  Can be either an IRI object
            or a string.
        """
        modIRI = self.expandIRI(mod_iri)

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

