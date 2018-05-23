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
# Provides a single class, LabelMap, that implements methods for mapping term
# labels to term IRIs in a given ontology.  A major challenge with using labels
# to identify terms is deciding how to deal with label collisions, which are
# nearly inevitable given a large enough imports closure.  LabelMap takes the
# approach of issuing non-fatal warnings when collisions are encountered while
# building the label lookup table.  However, LabelMap keeps track of all known
# ambiguous labels, and if client code attempts to look up the IRI for an
# ambiguous label, an exception is thrown.  To further avoid ambiguous label
# references, client code can optionally supply a root IRI string that will be
# used to attempt to disambiguate label collisions.
#

# Python imports.
from __future__ import unicode_literals
import logging

# Java imports.
from org.semanticweb.owlapi.model import AxiomType
from org.semanticweb.owlapi.model import OWLLiteral, IRI


class LabelError(RuntimeError):
    """
    Top-level exception class for all label errors.
    """
    pass

class InvalidLabelError(LabelError):
    """
    An exception that indicates a label (potentially with an IRI root) could
    not be matched to any IRIs in the LabelMap.
    """
    pass

class AmbiguousLabelError(LabelError):
    """
    An exception that indicates a label (potentially with an IRI root) matched
    more than one IRI in the LabelMap.
    """
    pass


class LabelMap:
    """
    Maintains a lookup table for an ontology that maps term labels to their
    associated term IRIs.
    """
    def __init__(self, ontology):
        """
        Initializes this LabelMap with an existing ontology.

        ontology: An Ontology object (*not* an OWL API OWLOntology object).
        """
        # Dictionary for the labels lookup table.
        self.lmap = {}

        # Dictionary to keep track of ambiguous labels and the IRIs to which
        # they refer.
        self.ambiglabels = {}

        self.ontology = ontology
        self._makeMap(ontology.getOWLOntology())

        # Register as an observer of the ontology so we can track changes
        # (i.e., adding labels or ontologies to the source ontology).
        self.ontology.registerObserver('label_added', self.notifyLabelAdded)
        self.ontology.registerObserver(
            'ontology_added', self.notifyOntologyAdded
        )

    def notifyLabelAdded(self, labelstr, subjectIRI):
        """
        Responds to 'label_added' event notifications from the source ontology.
        """
        self.add(labelstr, subjectIRI)

    def notifyOntologyAdded(self, added_ont):
        """
        Responds to 'ontology_added' event notifications from the source
        ontology.
        """
        self.addOntologyTerms(added_ont)

    def lookupIRI(self, label, IRI_root=''):
        """
        Retrieve the IRI associated with a given term label.  If IRI_root is
        provided, it will be used to confirm the retrieved IRI and, in the case
        of ambiguous labels (i.e., labels associated with more than one IRI),
        it will be used to attempt to disambiguate the label reference.  If the
        label (possibly with an IRI_root) is ambiguous, an exception is thrown.

        label: A label string.
        IRI_root: A string containing the root of the term IRI.
        Returns: The OWl API IRI object associated with the label.
        """
        if label not in self.ambiglabels:
            if label not in self.lmap:
                raise InvalidLabelError(
                    'The provided label, "{0}", does not match any labels in '
                    'the source ontology or its imports closure.'.format(label)
                )

            labelIRI = self.lmap[label]
            if unicode(labelIRI).startswith(IRI_root):
                return labelIRI
            else:
                raise InvalidLabelError(
                    'The provided IRI root, <{0}>, does not match the IRI '
                    'associated with the label "{1}" (<{2}>).'.format(
                        IRI_root, label, labelIRI
                    )
                )
        else:
            # Check if IRI_root can disambiguate the label reference.
            lastmatch = None
            matchcnt = 0
            for labelIRI in self.ambiglabels[label]:
                if unicode(labelIRI).startswith(IRI_root):
                    lastmatch = labelIRI
                    matchcnt += 1

            if matchcnt == 1:
                return lastmatch
            elif matchcnt == 0:
                raise InvalidLabelError(
                    'The IRI root <{0}> did not match any entities in the '
                    'source ontology or its imports closure with the label '
                    '"{1}".'.format(IRI_root, label)
                )
            else:
                owlont = self.ontology.getOWLOntology()
                if owlont.getOntologyID().getOntologyIRI().isPresent():
                    ont_iri = owlont.getOntologyID().getOntologyIRI().get().toString()
                else:
                    ont_iri = 'anonymous'
                raise AmbiguousLabelError(
                    'Attempted to use an ambiguous label: The label "{0}" is '
                    'used for multiple terms in the ontology <{1}>, including '
                    'its imports closure.  The label "{0}" is associated with '
                    'the following IRIs: {2}.'.format(
                        label, ont_iri, '<'
                        + '>, <'.join(
                            [unicode(labelIRI) for labelIRI in self.ambiglabels[label]]
                        )
                        + '>'
                    )
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
                ontiri_opt = self.ontology.getOWLOntology().getOntologyID().getOntologyIRI()
                if ontiri_opt.isPresent():
                    ontidstr = unicode(ontiri_opt.get())
                else:
                    ontidstr = 'anonymous'

                logging.warning(
                    'The label "{0}" is used for more than one IRI in the '
                    'ontology <{1}>, including its imports closure.  The '
                    'label "{0}" is associated with the following IRIs: '
                    '<{2}>.'.format(
                        label, ontidstr,
                        '>, <'.join(
                            [unicode(labelIRI) for labelIRI in self.ambiglabels[label]]
                        )
                    )
                )

    def addOntologyTerms(self, ontology):
        """
        Adds terms from an ontology to this LabelMap.

        ontology: An OWL API ontology instance.
        """
        self._makeMap(ontology)

    def _makeMap(self, ontology):
        """
        Creates label lookup table entries for a given ontology, including its
        imports closure, that map class labels (i.e., the values of rdfs:label
        axioms) to their corresponding class IRIs.  This function verifies that
        none of the labels are ambiguous; that is, that no label is used for
        more than one IRI.  If an ambiguous label is encountered, a warning is
        issued.

        ontology: An OWL API ontology object.
        """
        for annotation_axiom in ontology.getAxioms(AxiomType.ANNOTATION_ASSERTION, True):
            avalue = annotation_axiom.getValue()
            aproperty = annotation_axiom.getProperty()
            asubject = annotation_axiom.getSubject()
            if aproperty.isLabel():
                if isinstance(avalue, OWLLiteral) and isinstance(asubject, IRI):
                    literalval = avalue.getLiteral()
                    self.add(literalval, asubject)

