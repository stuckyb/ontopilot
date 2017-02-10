
# Python imports.
from labelmap import LabelMap
from obohelper import isOboID, oboIDToIRI
from ontology_entities import _OntologyClass, _OntologyDataProperty
from ontology_entities import _OntologyObjectProperty, _OntologyAnnotationProperty
import ontobuilder
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
from org.semanticweb.elk.owlapi import ElkReasonerFactory
from org.semanticweb import HermiT
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


class ReasonerManager:
    """
    Manages DL reasoners for Ontology objects.  Given a string designating a
    reasoner type and a source ontology, ReasonerManager will return a
    corresponding reasoner object and ensure that only one instance of each
    reasoner type is created.  ReasonerManager also provides methods to manage
    generating inferred axioms for a source ontology.
    """
    def __init__(self, ontology):
        self.ontology = ontology

        # A dictionary to keep track of instantiated reasoners.
        self.reasoners = {}

    def getOntology(self):
        """
        Returns the Ontology object associated with this ReasonerManager.
        """
        return self.ontology

    def getReasoner(self, reasoner_name):
        reasoner_name = reasoner_name.lower().strip()

        if reasoner_name not in self.reasoners:
            if reasoner_name == 'elk':
                ontobuilder.logger.info('Creating ELK reasoner...')
                self.reasoners[reasoner_name] = self.ontology.getELKReasoner()
            elif reasoner_name == 'hermit':
                ontobuilder.logger.info('Creating HermiT reasoner...')
                self.reasoners[reasoner_name] = self.ontology.getHermitReasoner()
            else:
                raise RuntimeError(
                    'Unrecognized DL reasoner name: '
                    + reasoner_name + '.'
                )

        return self.reasoners[reasoner_name]

    def disposeReasoners(self):
        for reasoner_name in self.reasoners:
            self.reasoners[reasoner_name].dispose()

        self.reasoners = {}

