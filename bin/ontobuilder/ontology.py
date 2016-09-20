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
from org.semanticweb.owlapi.model import SetOntologyID, AxiomType
from org.obolibrary.macro import ManchesterSyntaxTool
from org.semanticweb.owlapi.manchestersyntax.renderer import ParserException
from org.semanticweb.owlapi.formats import RDFXMLDocumentFormat
from org.semanticweb import HermiT
from com.google.common.base import Optional


# The base IRI for all new classes.
OBO_BASE_IRI = 'http://purl.obolibrary.org/obo/'

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
        if isinstance(parent_iri, basestring):
            parentIRI = IRI.create(parent_iri)
        else:
            parentIRI = parent_iri
 
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
    def __init__(self, ontology_path):
        """
        Initialize this Ontology instance.  The argument "ontology_path" should
        be a path to an OWL ontology file on the local file system.
        """
        # Load the ontology.
        self.ontman = OWLManager.createOWLOntologyManager()
        ontfile = File(ontology_path)
        self.ontology = self.ontman.loadOntologyFromOntologyDocument(ontfile)

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
        Searches for an entity in the ontology using an OBO ID string.
        """
        eIRI = oboIDToIRI(oboID)

        entity = self.getExistingClass(eIRI)

    def getExistingClass(self, classIRI):
        """
        Searches for an existing class in the ontology.  If the class is
        declared either directly in the ontology or is declared in its
        transitive imports closure, an OWL API object representing the class is
        returned.  Otherwise, None is returned.

          classIRI: An IRI object.
        """
        classobj = self.df.getOWLClass(classIRI)

        ontset = self.ontology.getImportsClosure()
        for ont in ontset:
            if ont.getDeclarationAxioms(classobj).size() > 0:
                return classobj

        return None

    def getHermitReasoner(self):
        """
        Returns an instance of a HermiT reasoner for this ontology.
        """
        return HermiT.Reasoner(self.getOWLOntolog())
    
    def createNewClass(self, class_iri):
        """
        Creates a new OWL class, adds it to the ontology, and returns an
        associated _OntologyClass object.

          class_iri: The IRI to use for the new class.  Can be either a string
                     or an IRI object.
        """
        if isinstance(class_iri, basestring):
            classIRI = IRI.create(class_iri)
        else:
            classIRI = class_iri

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

    def setOntologyID(self, iri_str):
        """
        Sets the ID for the ontology (i.e., the value of the "rdf:about"
        attribute).  The argument iri_str should be an IRI string.
        """
        ont_iri = IRI.create(iri_str)
        newoid = OWLOntologyID(Optional.fromNullable(ont_iri), Optional.absent())
        self.ontman.applyChange(SetOntologyID(self.ontology, newoid))

    def saveOntology(self, filepath):
        """
        Saves the ontology to a file.
        """
        oformat = RDFXMLDocumentFormat()
        foutputstream = FileOutputStream(File(filepath))
        self.ontman.saveOntology(self.ontology, oformat, foutputstream)
        foutputstream.close()

