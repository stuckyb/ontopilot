#
# Provides a single class, OWLOntologyBuilder, that implements methods for
# parsing descriptions of ontology classes (e.g., from CSV files) and
# converting them into classes in an OWL ontology.
#

# Python imports.
import re
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
from com.google.common.base import Optional


# The base IRI for all new classes.
OBO_BASE_IRI = 'http://purl.obolibrary.org/obo/'


class _OntologyClass:
    """
    Provides a high-level interface to the OWL API's ontology object system
    for OWL classes.  Conceptually, instances of this class represent a single
    OWL class in an OWL ontology.  This class should not be instantiated
    directly; instead, instances should be obtained through Ontology's public
    interface.
    """
    # The IRI for the property for definition annotations.
    DEFINITION_IRI = IRI.create(OBO_BASE_IRI + 'IAO_0000115')

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
        parentclass = self.df.getOWLClass(parentIRI)
        # The method below of checking for class declaration does not work for
        # classes from imports.  TODO: Find another way to do this.
        #if (base_ontology.getDeclarationAxioms(parentclass).size() == 0):
        #    raise RuntimeError('The parent class for ' + classdesc['ID'] + ' (row '
        #            + str(rowcnt) + ') could not be found.')
        
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


class OWLOntologyBuilder:
    """
    Builds an OWL ontology using Python dictionaries that describe new classes
    to add to an existing "base" ontology.  Typically, the new class
    descriptions will correspond with rows in an input CSV file.
    """
    def __init__(self, base_ont_path):
        # Load the base ontology.
        self.ontology = Ontology(base_ont_path)

    def getOntology(self):
        """
        Returns the Ontology object contained by this OWLOntologyBuilder.
        """
        return self.ontology

    def addClass(self, classdesc, expanddef=True):
        """
        Adds a new class to the ontology, based on a class description provided
        as the dictionary classdesc (i.e., the single explicit argument).  If
        expanddef is True, then term labels in the text definition for the new
        class will be expanded to include the terms' OBO IDs.
        """
        # Create the new class.
        newclass = self.ontology.createNewClass(
                IRI.create(OBO_BASE_IRI + classdesc['ID'].replace(':', '_'))
        )
        
        # Make sure we have a label and add it to the new class.
        labeltext = classdesc['Label'].strip()
        if labeltext == '':
            raise RuntimeError('No label was provided for ' + classdesc['ID']
                    + '.')
        newclass.addLabel(labeltext)
        
        # Add the text definition to the class, if we have one.
        textdef = classdesc['Text definition'].strip()
        if textdef != '':
            if expanddef:
                textdef = self._expandDefinition(textdef)

            newclass.addDefinition(textdef)
        
        # Get the OWLClass object of the parent class, making sure that it is
        # actually defined.
        parentIRI = self._getParentIRIFromDesc(classdesc)
        newclass.addSuperclass(parentIRI)
    
        # Add the formal definition (specified as a class expression in
        # Manchester Syntax), if we have one.
        formaldef = classdesc['Formal definition'].strip()
        if formaldef != '':
            newclass.addClassExpression(formaldef)
 
    def _getParentIRIFromDesc(self, classdesc):
        """
        Parses a superclass (parent) IRI from a class description dictionary.
        The parent class information should have the key "Parent class".
        Either a class label, ID, or both can be provided.  The general format
        is: "'class label' (CLASS_ID)".  For example:
        "'whole plant' (PO:0000003)".  If both a label and ID are provided,
        this method will verify that they correspond.
        """
        tdata = classdesc['Parent class'].strip()
        if tdata == '':
            raise RuntimeError('No parent class was provided.')
    
        # Check if we have a class label.
        if tdata.startswith("'"):
            if tdata.find("'") == tdata.rfind("'"):
                raise RuntimeError('Missing closing quote in parent class specification: '
                            + tdata + '".')
            label = tdata.split("'")[1]

            # Get the class IRI associated with the label.
            labelIRI = self.ontology.labelToIRI(label)
    
            # See if we also have an ID.
            if tdata.find('(') > -1:
                tdID = tdata.split('(')[1]
                if tdID.find(')') > -1:
                    tdID = tdID.rstrip(')')
                    tdIRI = IRI.create(OBO_BASE_IRI + tdID.replace(':', '_'))
                else:
                    raise RuntimeError('Missing closing parenthesis in parent class specification: '
                            + tdata + '".')
        else:
            # We only have an ID.
            labelIRI = None
            tdIRI = IRI.create(OBO_BASE_IRI + tdata.replace(':', '_'))
    
        if labelIRI != None:
            if tdIRI != None:
                if labelIRI.equals(tdIRI):
                    return labelIRI
                else:
                    raise RuntimeError('Class label does not match ID in parent class specification: '
                            + tdata + '".')
            else:
                return labelIRI
        else:
            return tdIRI
    
    def _termIRIToOboID(self, termIRI):
        """
        Converts an IRI for an ontology term into an OB ID; that is, a string
        of the form "PO:0000003".
        """
        termIRIstr = termIRI.toString()
        IRIpath = urlparse.urlsplit(termIRIstr).path
        rawID = os.path.split(IRIpath)[1]

        return rawID.replace('_', ':')
    
    def _expandDefinition(self, deftext):
        """
        Modifies a text definition for an ontology term by adding OBO IDs for
        all term labels in braces ('{' and '}') in the definition.  For
        example, if the definition contains the text "A {whole plant} that...",
        it will be converted to "A whole plant (PO:0000003) that...".
        """
        labelre = re.compile(r'(\{[A-Za-z _]+\})')
        defparts = labelre.split(deftext)

        newdef = ''
        for defpart in defparts:
            if labelre.match(defpart) != None:
                label = defpart.strip("{}")

                # Get the class IRI associated with this label.
                labelIRI = self.ontology.labelToIRI(label)

                labelID = self._termIRIToOboID(labelIRI)
                newdef += label + ' (' + labelID + ')'
            else:
                newdef += defpart

        if len(defparts) == 0:
            newdef = deftext

        return newdef

