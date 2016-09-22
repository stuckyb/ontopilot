#
# Provides convenience classes that "wrap" OWL API classes and implement a
# higher-level interface for interacting with OWL ontologies.  The only class
# that should be directly instantiated by client code is Ontology.  Other
# functionality should be accessed through Ontology's public interface, except
# fo the two public convenience methods for converting OBO IDs to/from IRIs.
#

# Python imports.
import urlparse
import os
from labelmap import LabelMap

# Java imports.
from java.io import File, FileOutputStream
from org.semanticweb.owlapi.apibinding import OWLManager
from org.semanticweb.owlapi.model import IRI, AddAxiom, OWLOntologyID
from org.semanticweb.owlapi.model import SetOntologyID, AxiomType, OWLOntology
from org.semanticweb.owlapi.model import AddOntologyAnnotation
from org.obolibrary.macro import ManchesterSyntaxTool
from org.semanticweb.owlapi.manchestersyntax.renderer import ParserException
from org.semanticweb.owlapi.formats import RDFXMLDocumentFormat
from org.semanticweb import HermiT
from uk.ac.manchester.cs.owlapi.modularity import SyntacticLocalityModuleExtractor
from uk.ac.manchester.cs.owlapi.modularity import ModuleType
from com.google.common.base import Optional


# The base IRI for all new classes.
OBO_BASE_IRI = 'http://purl.obolibrary.org/obo/'


def getIRI(irival):
    """
    Accepts either an IRI string or an OWL API IRI object, and returns an OWL
    API IRI object.  If irival is a string, a new IRI object is created.
    If irival is an IRI object, it is returned unaltered.
    """
    if isinstance(irival, basestring):
        IRIobj = IRI.create(irival)
    else:
        IRIobj = irival

    return IRIobj

def termIRIToOboID(termIRI):
    """
    Converts an IRI for an ontology term into an OB ID; that is, a string
    of the form "PO:0000003".

      termIRI: The IRI of the ontology term.  Can be either an IRI object
               or a string.
    """
    if isinstance(termIRI, IRI):
        termIRIstr = termIRI.toString()
    else:
        termIRIstr = termIRI

    IRIpath = urlparse.urlsplit(termIRIstr).path
    rawID = os.path.split(IRIpath)[1]

    return rawID.replace('_', ':')

def oboIDToIRI(oboID):
    """
    Converts an OBO ID string (i.e., a string of the form "PO:0000003") to
    an IRI.
    """
    oboID = oboID.strip()
    tIRI = IRI.create(OBO_BASE_IRI + oboID.replace(':', '_'))

    return tIRI


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
        deftxt = deftxt.strip()

        defannot = self.df.getOWLAnnotation(
            self.df.getOWLAnnotationProperty(self.DEFINITION_IRI),
            self.df.getOWLLiteral(deftxt)
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.classIRI, defannot)

        self.ontology.addClassAxiom(annotaxiom)

    def addLabel(self, labeltxt):
        labeltxt = labeltxt.strip()

        labelannot = self.df.getOWLAnnotation(
            self.df.getRDFSLabel(), self.df.getOWLLiteral(labeltxt, 'en')
        )
        annotaxiom = self.df.getOWLAnnotationAssertionAxiom(self.classIRI, labelannot)

        self.ontology.addClassAxiom(annotaxiom)

    def addSuperclass(self, parent_iri):
        """
        Adds a parent class for this class.

          parent_iri: The IRI of the parent class.  Can be either a string or
                      an IRI object.
        """
        parentIRI = getIRI(parent_iri)

        # Get the OWLClass object of the parent class, making sure that it is
        # actually defined.
        parentclass = self.ontology.getExistingClass(parentIRI)
        if parentclass == None:
            raise RuntimeError('The designated superclass, ' + str(parent_iri)
                    + ', could not be found in the source ontology.')
        
        # Add the subclass axiom to the ontology.
        newaxiom = self.df.getOWLSubClassOfAxiom(self.owlclass, parentclass)
        self.ontology.addClassAxiom(newaxiom)

    def addClassExpression(self, manchester_exp):
        """
        Adds a class expression as either an equivalency axiom or a subclass
        axiom.  The class expression should be written in Manchester Syntax.
        """
        # Add the formal definition (specified as a class expression in
        # Manchester Syntax), if we have one.
        formaldef = manchester_exp
        if formaldef != '':
            try:
                cexp = self.ontology.mparser.parseManchesterExpression(formaldef)
            except ParserException as err:
                raise RuntimeError('Error parsing "' + err.getCurrentToken()
                        + '" at line ' + str(err.getLineNumber()) + ', column '
                        + str(err.getColumnNumber())
                        + ' of the formal term definition (Manchester Syntax expected).')
            ecaxiom = self.df.getOWLEquivalentClassesAxiom(cexp, self.owlclass)
            self.ontology.addClassAxiom(ecaxiom)

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

        # Create an OWL data factory and Manchester Syntax parser.
        self.df = OWLManager.getOWLDataFactory()
        self.mparser = ManchesterSyntaxTool(self.ontology)

    def __del__(self):
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
        except KeyError as err:
            raise RuntimeError('The class label, "' + label
                + '", could not be matched to a term IRI.')

        return cIRI

    def getEntityByOboID(self, oboID):
        """
        Searches for an entity in the ontology using an OBO ID string.  The
        entity is assumed to be either a class, object property, data property,
        or annotation property.
        """
        eIRI = oboIDToIRI(oboID)

        entity = self.getExistingClass(eIRI)
        if entity == None:
            entity = self.getExistingProperty(eIRI)

        return entity

    def getExistingClass(self, class_iri):
        """
        Searches for an existing class in the ontology.  If the class is
        declared either directly in the ontology or is declared in its
        transitive imports closure, an OWL API object representing the class is
        returned.  Otherwise, None is returned.

          class_iri: The IRI of the class to search for.  Can be either an IRI
                     object or a string.
        """
        classIRI = getIRI(class_iri)

        classobj = self.df.getOWLClass(classIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(classobj).size() > 0:
                return classobj

        return None

    def getExistingProperty(self, prop_iri):
        """
        Searches for an existing property in the ontology.  If the property is
        declared either directly in the ontology or is declared in its
        transitive imports closure, an OWL API object representing the property
        is returned.  Otherwise, None is returned.  Object properties, data
        properties, and annotation properties are all considered; ontology
        properties are not.

          prop_iri: The IRI of the property to search for.  Can be either an
                    IRI object or a string.
        """
        propIRI = getIRI(prop_iri)

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

    def createNewClass(self, class_iri):
        """
        Creates a new OWL class, adds it to the ontology, and returns an
        associated _OntologyClass object.

          class_iri: The IRI to use for the new class.  Can be either a string
                     or an IRI object.
        """
        classIRI = getIRI(class_iri)

        # Get the class object.
        owlclass = self.df.getOWLClass(classIRI)

        declaxiom = self.df.getOWLDeclarationAxiom(owlclass)
        self.ontman.applyChange(AddAxiom(self.ontology, declaxiom))

        return _OntologyClass(classIRI, owlclass, self)

    def addClassAxiom(self, owl_axiom):
        """
        Adds a new class axiom to this ontology.  In this context, "class
        axiom" means an axiom with an OWL class as its subject.  The argument
        "owl_axiom" should be an instance of an OWL API axiom object.
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
        ontIRI = getIRI(ont_iri)

        newoid = OWLOntologyID(Optional.fromNullable(ontIRI), Optional.absent())
        self.ontman.applyChange(SetOntologyID(self.ontology, newoid))

    def setOntologySource(self, source_iri):
        """
        Sets the value of the "dc:source" annotation property for this ontology.

          source_iri: The IRI of the source ontology.  Can be either an IRI
                      object or a string.
        """
        sourceIRI = getIRI(source_iri)

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
        modIRI = getIRI(mod_iri)

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

