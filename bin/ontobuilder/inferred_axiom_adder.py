#
# Provides methods for adding inferred axioms to an ontology.
#

# Python imports.
from labelmap import LabelMap
from obohelper import isOboID, oboIDToIRI
from ontology_entities import _OntologyClass, _OntologyDataProperty
from ontology_entities import _OntologyObjectProperty, _OntologyAnnotationProperty
from reasoner_manager import ReasonerManager
from rfc3987 import rfc3987

# Java imports.
from java.io import File, FileOutputStream
from java.util import HashSet
from java.lang import UnsupportedOperationException
from org.semanticweb.owlapi.apibinding import OWLManager
from org.semanticweb.owlapi.model import IRI, OWLOntologyID
from org.semanticweb.owlapi.model import AddAxiom, AddImport, RemoveImport
from org.semanticweb.owlapi.model import SetOntologyID, AxiomType, OWLOntology
from org.semanticweb.owlapi.model import AddOntologyAnnotation
from org.semanticweb.owlapi.model import OWLRuntimeException
from org.semanticweb.owlapi.formats import RDFXMLDocumentFormat
from uk.ac.manchester.cs.owlapi.modularity import SyntacticLocalityModuleExtractor
from uk.ac.manchester.cs.owlapi.modularity import ModuleType
from com.google.common.base import Optional
from org.semanticweb.owlapi.io import OWLOntologyCreationIOException
from org.semanticweb.owlapi.model import OWLOntologyFactoryNotFoundException
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum
from org.semanticweb.owlapi.reasoner import InferenceType
from org.semanticweb.owlapi.util import InferredSubClassAxiomGenerator
from org.semanticweb.owlapi.util import InferredEquivalentClassAxiomGenerator
from org.semanticweb.owlapi.util import InferredSubDataPropertyAxiomGenerator
from org.semanticweb.owlapi.util import InferredSubObjectPropertyAxiomGenerator
from org.semanticweb.owlapi.util import InferredClassAssertionAxiomGenerator
from org.semanticweb.owlapi.util import InferredDisjointClassesAxiomGenerator
from org.semanticweb.owlapi.util import InferredOntologyGenerator


class InferredAxiomAdder:
    """
    Provides a high-level interface for generating inferred axioms and adding
    them to an ontology.  Besides just adding inferred axioms, this class also
    does a number of more sophisticated procedures, including de-duplicating
    the final axiom set, removing trivial axioms, etc.
    """
    # The IRI for the "dc:source" annotation property.
    SOURCE_PROP_IRI = IRI.create('http://purl.org/dc/elements/1.1/source')

    # The IRI for inferred axiom annotation.
    INFERRED_ANNOT_IRI = IRI.create(
        'http://www.geneontology.org/formats/oboInOwl#is_inferred'
    )

    def __init__(self, ontology, reasoner_str):
        """
        sourceont: The ontology on which to run the reasoner and for which to
            add inferred axioms.
        reasoner_str: A string indicating the type of reasoner to use.
        """
        self.ont = ontology
        self.setReasoner(reasoner_str)

    def setReasoner(self, reasoner_str):
        """
        Sets the reasoner type to use for generating inferred axioms.

        reasoner_str: A string indicating the type of reasoner to use.
        """
        self.reasoner = self.ont.getReasonerManager().getReasoner(reasoner_str)

    def _getGeneratorsList(self, include_disjoint):
        """
        Returns a list of AxiomGenerators for a reasoner that match the
        capabilities of the reasoner.

        include_disjoint: Whether to include a disjointness axioms generator.
        """
        # By default, only use generators that are supported by the ELK
        # reasoner.  Assume that all reasoners have these capabilities.
        generators = [
            InferredSubClassAxiomGenerator(),
            InferredEquivalentClassAxiomGenerator(),
            InferredClassAssertionAxiomGenerator()
        ]

        if include_disjoint:
            generators.append(InferredDisjointClassesAxiomGenerator())

        # Check for data property hierarchy inferencing support.
        hasmethod = True
        try:
            testprop = self.ont.df.getOWLDataProperty(IRI.create('test'))
            self.reasoner.getSuperDataProperties(testprop, True)
        except UnsupportedOperationException as err:
            hasmethod = False
        if hasmethod:
            generators.append(InferredSubDataPropertyAxiomGenerator())

        # Check for object property hierarchy inferencing support.
        hasmethod = True
        try:
            testprop = self.ont.df.getOWLObjectProperty(IRI.create('test'))
            self.reasoner.getSuperObjectProperties(testprop, True)
        except UnsupportedOperationException as err:
            hasmethod = False
        if hasmethod:
            generators.append(InferredSubObjectPropertyAxiomGenerator())

        return generators

    def _getRedundantSubclassOfAxioms(self):
        """
        Returns a set of all "subclass of" axioms in this ontology that are
        redundant.  In this context, "redundant" means that a class is asserted
        to have two or more different superclasses that are part of the same
        class hierarchy.  Only the superclass nearest to the subclass is
        retained; all other axioms are considered to be redundant.  This
        situation can easily arise after inferred "subclass of" axioms are
        added to an ontology.
        """
        redundants = set()
        owlont = self.ont.getOWLOntology()

        for classobj in owlont.getClassesInSignature():
            # Get the set of direct superclasses for this class.
            supersset = self.reasoner.getSuperClasses(classobj, True).getFlattened()

            # Examine each "subclass of" axiom for this class.  If the
            # superclass asserted in an axiom is not a direct superclass, then
            # the axiom can be considered redundant.
            axioms = owlont.getSubClassAxiomsForSubClass(classobj)
            for axiom in axioms:
                superclass = axiom.getSuperClass()
                if not(superclass.isAnonymous()):
                    if not(supersset.contains(superclass.asOWLClass())):
                        redundants.add(axiom)

        return redundants

    def addInferredAxioms(self, include_disjoint=False, annotate=False):
        """
        Runs a reasoner on this ontology and adds the inferred axioms.  The
        reasoner instance should be obtained from one of the get*Reasoner()
        methods of this ontology.

        include_disjoint: Whether to include inferred disjointness axioms.
        annotate: If true, annotate inferred axioms to mark them as inferred.
        """
        # The general approach is to first get the set of all axioms in the
        # ontology prior to reasoning so that this set can be used for
        # de-duplication later.  Then, inferred axioms are added to a new
        # ontology.  This makes it easy to compare explicit and inferred
        # axioms and to annotate inferred axioms.  Trivial axioms are removed
        # from the inferred axiom set, and the inferred axioms are merged into
        # the main ontology.

        owlont = self.ont.getOWLOntology()
        ontman = self.ont.ontman
        df = self.ont.df
        oldaxioms = owlont.getAxioms(ImportsEnum.INCLUDED)

        self.reasoner.precomputeInferences(InferenceType.CLASS_HIERARCHY)
        self.reasoner.precomputeInferences(InferenceType.CLASS_ASSERTIONS)

        generators = self._getGeneratorsList(include_disjoint)
        iog = InferredOntologyGenerator(self.reasoner, generators)

        inferredont = ontman.createOntology()
        iog.fillOntology(self.ont.df, inferredont)

        # Delete axioms in the inferred set that are explicitly stated in the
        # source ontology (or its imports closure).
        delaxioms = HashSet()
        for axiom in inferredont.getAxioms():
            if oldaxioms.contains(axiom):
                delaxioms.add(axiom)
        ontman.removeAxioms(inferredont, delaxioms)

        # Delete trivial axioms (e.g., subclass of owl:Thing, etc.).
        trivial_entities = [
            df.getOWLThing(), df.getOWLNothing(),
            df.getOWLTopDataProperty(), df.getOWLTopObjectProperty()
        ]
        delaxioms.clear()
        for axiom in inferredont.getAxioms():
            for trivial_entity in trivial_entities:
                if axiom.containsEntityInSignature(trivial_entity):
                    delaxioms.add(axiom)
                    break
        ontman.removeAxioms(inferredont, delaxioms)

        if annotate:
            # Annotate all of the inferred axioms.
            annotprop = df.getOWLAnnotationProperty(self.INFERRED_ANNOT_IRI)
            annotval = df.getOWLLiteral('true')
            for axiom in inferredont.getAxioms():
                annot = df.getOWLAnnotation(annotprop, annotval)
                newaxiom = axiom.getAnnotatedAxiom(HashSet([annot]))
                ontman.removeAxiom(inferredont, axiom)
                ontman.addAxiom(inferredont, newaxiom)

        # Merge the inferred axioms into the main ontology.
        ontman.addAxioms(owlont, inferredont.getAxioms())

        # Find and remove redundant "subclass of" axioms.
        redundants = self._getRedundantSubclassOfAxioms()
        ontman.removeAxioms(owlont, redundants)

