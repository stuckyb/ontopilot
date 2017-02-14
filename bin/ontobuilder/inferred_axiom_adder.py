#
# Provides methods for adding inferred axioms to an ontology.
#

# Python imports.
import ontobuilder

# Java imports.
from java.util import HashSet
from java.lang import UnsupportedOperationException
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.model.parameters import Imports as ImportsEnum
from org.semanticweb.owlapi.util import InferredSubClassAxiomGenerator
from org.semanticweb.owlapi.util import InferredEquivalentClassAxiomGenerator
from org.semanticweb.owlapi.util import InferredSubDataPropertyAxiomGenerator
from org.semanticweb.owlapi.util import InferredSubObjectPropertyAxiomGenerator
from org.semanticweb.owlapi.util import InferredClassAssertionAxiomGenerator
from org.semanticweb.owlapi.util import InferredDisjointClassesAxiomGenerator
from org.semanticweb.owlapi.util import InferredOntologyGenerator
from org.semanticweb.owlapi.util import InferredInverseObjectPropertiesAxiomGenerator
from org.semanticweb.owlapi.util import InferredPropertyAssertionGenerator


# Strings for identifying supported types of inferences for generating inferred
# ontology axioms.
INFERENCE_TYPES = (
    'subclasses', 'subdata properties', 'subobject properties', 'types',
    'equivalent classes', 'disjoint classes', 'inverse object properties',
    'property values'
)


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

    def _getGeneratorsList(self, inference_types):
        """
        Returns a list of AxiomGenerators for a reasoner that match the
        capabilities of the reasoner.

        inference_types: A list of strings specifying the kinds of inferred
            axioms to generate.  Valid values are detailed in the sample
            configuration file.
        """
        # Get a string for the reasoner class for error reporting.
        reasoner_name = (
            self.reasoner.__class__.__module__ + '.'
            + self.reasoner.__class__.__name__
        )

        # Examine each inference type string, check if it is supported by the
        # current reasoner, and if so, add an appropriate generator to the list
        # of generators.
        generators = []
        for inference_type in inference_types:
            if inference_type == 'subclasses':
                # Check for class hierarchy inferencing support.
                try:
                    testent = self.ont.df.getOWLClass(IRI.create('test'))
                    self.reasoner.getSuperClasses(testent, True)
                    generators.append(InferredSubClassAxiomGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support subclass inferences.'.format(
                            reasoner_name
                        )
                    )

            elif inference_type == 'equivalent classes':
                # Check for class equivalency inferencing support.
                try:
                    testent = self.ont.df.getOWLClass(IRI.create('test'))
                    self.reasoner.getEquivalentClasses(testent)
                    generators.append(InferredEquivalentClassAxiomGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support class equivalency inferences.'.format(
                            reasoner_name
                        )
                    )

            elif inference_type == 'disjoint classes':
                # Check for class disjointness inferencing support.
                try:
                    testent = self.ont.df.getOWLClass(IRI.create('test'))
                    self.reasoner.getDisjointClasses(testent)
                    generators.append(InferredDisjointClassesAxiomGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support class disjointness inferences.'.format(
                            reasoner_name
                        )
                    )

            elif inference_type == 'subdata properties':
                # Check for data property hierarchy inferencing support.
                try:
                    testent = self.ont.df.getOWLDataProperty(IRI.create('test'))
                    self.reasoner.getSuperDataProperties(testent, True)
                    generators.append(InferredSubDataPropertyAxiomGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support data property hierarchy inferences.'.format(
                            reasoner_name
                        )
                    )

            elif inference_type == 'subobject properties':
                # Check for object property hierarchy inferencing support.
                try:
                    testent = self.ont.df.getOWLObjectProperty(IRI.create('test'))
                    self.reasoner.getSuperObjectProperties(testent, True)
                    generators.append(InferredSubObjectPropertyAxiomGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support object property hierarchy inferences.'.format(
                            reasoner_name
                        )
                    )

            elif inference_type == 'inverse object properties':
                # Check for inverse object property inferencing support.
                try:
                    testent = self.ont.df.getOWLObjectProperty(IRI.create('test'))
                    self.reasoner.getInverseObjectProperties(testent)
                    generators.append(InferredInverseObjectPropertiesAxiomGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support inverse object property inferences.'.format(
                            reasoner_name
                        )
                    )

            elif inference_type == 'types':
                # Check for class assertion inferencing support.
                try:
                    testent = self.ont.df.getOWLNamedIndividual(IRI.create('test'))
                    self.reasoner.getTypes(testent, True)
                    generators.append(InferredClassAssertionAxiomGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support class assertion inferences.'.format(
                            reasoner_name
                        )
                    )

            elif inference_type == 'property values':
                # Check for individual property value inferencing support.
                try:
                    testent = self.ont.df.getOWLNamedIndividual(IRI.create('test'))
                    dprop = self.ont.df.getOWLDataProperty(IRI.create('dprop'))
                    oprop = self.ont.df.getOWLObjectProperty(IRI.create('oprop'))
                    self.reasoner.getDataPropertyValues(testent, dprop)
                    self.reasoner.getObjectPropertyValues(testent, oprop)
                    generators.append(InferredPropertyAssertionGenerator())
                except UnsupportedOperationException as err:
                    ontobuilder.logging.warning(
                        'The reasoner "{0}" does not support property assertion inferences.'.format(
                            reasoner_name
                        )
                    )

            else:
                raise RuntimeError(
                    'Unsupported inference type: "{0}".'.format(inference_type)
                )

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

    def addInferredAxioms(self, inference_types, annotate=False):
        """
        Runs a reasoner on this ontology and adds the inferred axioms.

        inference_types: A list of strings specifying the kinds of inferred
            axioms to generate.  Valid values are detailed in the sample
            configuration file.
        annotate: If true, annotate inferred axioms to mark them as inferred.
        """
        # First, make sure that the ontology is consistent; otherwise, all
        # inference attempts will fail.
        report = self.ont.checkEntailmentErrors()
        if not(report['is_consistent']):
            raise RuntimeError(
                'The ontology is inconsistent.  Inferred axioms cannot be '
                + 'generated for inconsistent ontologies.'
            )

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

        generators = self._getGeneratorsList(inference_types)
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
            df.getOWLTopDataProperty(), df.getOWLTopObjectProperty(),
            df.getOWLBottomDataProperty(), df.getOWLBottomObjectProperty()
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

