# Copyright (C) 2018 Brian J. Stucky
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
# Provides a single class, EntityFinder, that implements methods for finding
# entities in one or more ontologies that are possible matches for a given
# search string.  Matching is based on the labels and synonyms of ontology
# entities, and matching can be "fuzzy" based on Porter's stemming algorithm.
#

# Python imports.
from __future__ import unicode_literals
from ontopilot import logger

# Java imports.
from org.semanticweb.owlapi.model import AxiomType
from org.semanticweb.owlapi.model import OWLLiteral, IRI


PREFIXES = {
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#',
    'skos': 'http://www.w3.org/2004/02/skos/core#'
}


class EntityFinder:
    """
    Finds ontology entities that are potential matches for search strings.
    Searching is based on entities' labels and synonyms.
    """
    # Define the IRIs of label and synonym annotation properties.  Each list
    # entry is an (IRI object, short IRI string) pair.
    LABEL_IRIS = [
        # The IRI for rdfs:label.
        ( IRI.create(PREFIXES['rdfs'] + 'label'), 'rdfs:label' ),

        # All of the synonym annotation properties from OboInOwl.
        ( IRI.create(PREFIXES['oboInOwl'] + 'hasSynonym'),
            'oboInOwl:hasSynonym' ),
        ( IRI.create(PREFIXES['oboInOwl'] + 'hasExactSynonym'),
            'oboInOwl:hasExactSynonym' ),
        ( IRI.create(PREFIXES['oboInOwl'] + 'hasNarrowSynonym'),
            'oboInOwl:hasNarrowSynonym' ),
        ( IRI.create(PREFIXES['oboInOwl'] + 'hasBroadSynonym'),
            'oboInOwl:hasBroadSynonym' ),
        ( IRI.create(PREFIXES['oboInOwl'] + 'hasRelatedSynonym'),
            'oboInOwl:hasRelatedSynonym' ),

        # The SKOS lexical label annotation properties.
        ( IRI.create(PREFIXES['skos'] + 'prefLabel'), 'skos:prefLabel' ),
        ( IRI.create(PREFIXES['skos'] + 'altLabel'), 'skos:altLabel' ),
        ( IRI.create(PREFIXES['skos'] + 'hiddenLabel'), 'skos:hiddenLabel' )
    ]

    def __init__(self):
        """
        Initializes this EntityFinder.
        """
        # Dictionary for the entities lookup table.  Each key in the dictionary
        # is a term (either a label or synonym, possibly stemmed), and each
        # value is a set of (_OntologyEntity object, IRI, label text) triples,
        # where "IRI" is the IRI of the annotation property that linked the
        # ontology entity to the term name and "label text" is the text literal
        # for the annotation.
        self.emap = {}

    def addOntologyEntities(self, ontology):
        """
        Adds entities from an ontology, including its imports closure, to this
        EntityFinder.

        ontology: An Ontology object (*not* an OWL API OWLOntology object).
        """
        owlont = ontology.getOWLOntology()

        for annotation_axiom in owlont.getAxioms(AxiomType.ANNOTATION_ASSERTION, True):
            avalue = annotation_axiom.getValue()
            aproperty = annotation_axiom.getProperty()
            asubject = annotation_axiom.getSubject()

            # See if the annotation property matches any of the target
            # properties.
            irimatch = False
            propiri = ''
            for prop_pair in self.LABEL_IRIS:
                if prop_pair[0].equals(aproperty.getIRI()):
                    irimatch = True
                    propiri = prop_pair[1]
                    break

            if irimatch:
                if isinstance(avalue, OWLLiteral) and isinstance(asubject, IRI):
                    literalval = avalue.getLiteral()
                    entity = ontology.getExistingEntity(asubject)

                    if literalval not in self.emap:
                        self.emap[literalval] = set()
                    self.emap[literalval].add((entity, propiri, literalval))

        print self.emap
    def findEntities(self, searchstr):
        """
        Searches for entities that match the given search string.  Returns a
        list of matching (_OntologyEntity object, IRI string, label text)
        pairs, where "IRI string" is the IRI of the annotation property that
        connects the label text to the ontology entity and "label text" is the
        text literal for the matching annotation.

        searchstr: A string to match to entities.
        """
        res = []
        if searchstr in self.emap:
            res = list(self.emap[searchstr])

        return res

