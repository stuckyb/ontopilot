"""
Provides a single class, LabelMap, that implements methods for mapping term
labels to term IRIs in a given ontology.  A major challenge with using labels
to identify terms is deciding how to deal with label collisions, which are
nearly inevitable given a large enough imports closure.  LableMap takes the
approach of issuing non-fatal warnings when collisions are encountered while
building the label lookup table.  However, LabelMap keeps track of all known
ambiguous labels, and if client code attempts to look up the IRI for an
ambiguous label, an exception is thrown.
"""

# Python imports.
import logging

# Java imports.
from org.semanticweb.owlapi.model import AxiomType
from org.semanticweb.owlapi.model import OWLLiteral, IRI


class LabelMap:
    """
    Maintains a lookup table for an ontology that maps term labels to their
    associated term IRIs.
    """
    def __init__(self, ontology):
        """
        Initializes this LabelMap with an existing ontology.

        ontology: An OWL API OWLOntology object.
        """
        # Dictionary for the labels lookup table.
        self.lmap = {}

        # Dictionary to keep track of ambiguous labels and the IRIs to which
        # they refer.
        self.ambiglabels = {}

        self.ontology = ontology

        self._makeMap(ontology)

    def lookupIRI(self, label, IRI_root=''):
        """
        Retrieve the IRI associated with a given term label.  If IRI_root is
        provided, it will be used to confirm the retrieved IRI and, in the case
        of ambiguous labels (i.e., labes associated with more than one IRI), it
        will be used to attempt to disambiguate the label reference.  If the
        label (possibly with an IRI_root) is ambiguous, an exception is thrown.

        label: A label string.
        IRI_root: A string containing the root of the term IRI.
        Returns: The OWl API IRI object associated with the label.
        """
        if label not in self.ambiglabels:
            labelIRI = self.lmap[label]
            if str(labelIRI).startswith(IRI_root):
                return labelIRI
            else:
                raise RuntimeError(
                    'The provided IRI root, <' + IRI_root
                    + '>, does not match the IRI associated with the label "'
                    + label + '" (<' + str(labelIRI) + '>.'
                )
        else:
            # Check if IRI_root can disambiguate the label reference.
            lastmatch = None
            matchcnt = 0
            for labelIRI in self.ambiglabels[label]:
                if str(labelIRI).startswith(IRI_root):
                    lastmatch = labelIRI
                    matchcnt += 1

            if matchcnt == 1:
                return lastmatch
            else:
                raise RuntimeError(
                    'Attempted to use an ambiguous label: The label "' + label
                    + '" is used for multiple terms in the ontology <'
                    + str(self.ontology.getOntologyID().getOntologyIRI().get())
                    + '>, including its imports closure.  The label "' + label
                    + '" is associated with the following IRIs: ' + '<'
                    + '>, <'.join([str(labelIRI) for labelIRI in self.ambiglabels[label]])
                    + '>.'
                )

    def _addAmbiguousLabel(self, label, termIRI):
        """
        Adds a label, along with its term IRI, to the set of ambiguous labels.
        """
        if label not in self.ambiglabels:
            self.ambiglabels[label] = [self.lmap[label], termIRI]
        else:
            self.ambiglabels[label].append(termIRI)

    def add(self, label, termIRI):
        """
        Adds an IRI/label pair to this LabelMap.  If the label is already in
        use in the ontology, a warning is issued.

        label: A string containing the label text.
        termIRI: An OWl API IRI object.
        """
        if label not in self.lmap:
            self.lmap[label] = termIRI
        else:
            if not(self.lmap[label].equals(termIRI)):
                self._addAmbiguousLabel(label, termIRI)
                logging.warning(
                    'The label "' + label +
                    '" is used for more than one IRI in the ontology <'
                    + str(self.ontology.getOntologyID().getOntologyIRI().get())
                    + '>, including its imports closure.  The label "' + label
                    + '" is associated with the following IRIs: ' + '<'
                    + '>, <'.join([str(labelIRI) for labelIRI in self.ambiglabels[label]])
                    + '>.'
                )

    def _makeMap(self, ontology):
        """
        Creates label lookup table entries for a given ontology, including its
        imports closure, that map class labels (i.e., the values of rdfs:label
        axioms) to their corresponding class IRIs.  This function verifies that
        none of the labels are ambiguous; that is, that no label is used for
        more than one IRI.  If an ambiguous label is encountered, a warning is
        issued.
        """
        for annotation_axiom in ontology.getAxioms(AxiomType.ANNOTATION_ASSERTION, True):
            avalue = annotation_axiom.getValue()
            aproperty = annotation_axiom.getProperty()
            asubject = annotation_axiom.getSubject()
            if aproperty.isLabel():
                if isinstance(avalue, OWLLiteral) and isinstance(asubject, IRI):
                    literalval = avalue.getLiteral()
                    self.add(literalval, asubject)

