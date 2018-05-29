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
import unicodedata
import string
import re
from nltk.stem import PorterStemmer
from ontopilot import logger

# Java imports.
from org.semanticweb.owlapi.model import AxiomType
from org.semanticweb.owlapi.model import OWLLiteral, IRI


# Define IRI prefix constants for the label/synonym annotation properties.
PREFIXES = {
    'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
    'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#',
    'skos': 'http://www.w3.org/2004/02/skos/core#'
}

# Define constants for the match types.
# Full term matches; that is, the matching entity text is the complete term
# label or synonym.
MATCH_FULL = 0
# Sub-phrase matches; that is, the matching entity text is a sub-phrase of the
# full term label or synonym.
MATCH_SUBPHRASE = 1

# Define the standard and typographic apostrophe characters.
APOST_CHARS = ["'", unichr(8217)]

# Add typographic double quotes and single quote to the set of punctuation
# characters.
punctchars = string.punctuation + unichr(8220) + unichr(8221) + unichr(8217)
punct_re = re.compile('[' + punctchars + ']')

# Define the stop words that should not be considered phrases by themselves.
# This is taken from nltk version 3.3 and is copied here directly to streamline
# the code.  The list is almost as in NLTK, except contractions have the
# letters after the apostrophe added back on.  E.g., the stop word 'doesn' in
# NLTK is listed here as 'doesnt'.
STOPWORDS = set([
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
    'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their',
    'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
    'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'can', 'will', 'just', 'dont', 'should', 'now', 'd',
    'll', 'm', 'o', 're', 've', 'y', 'aint', 'arent', 'couldnt', 'didnt',
    'doesnt', 'hadnt', 'hasnt', 'havent', 'isnt', 'ma', 'mightnt', 'mustnt',
    'neednt', 'shant', 'shouldnt', 'wasnt', 'werent', 'wont', 'wouldnt'
])
# The same set of stop words after stemming each stop word using NLTK's Porter
# stemmer.  For execution efficiency, the set is provided as a literal rather
# than generated dynamically by instantiating a PorterStemmer.
STEMMED_STOPWORDS = set([
    'hi', 'been', 'shouldnt', 'hasnt', 'about', 'your', 'when', 'doesnt',
    'these', 'veri', 'her', 'if', 'between', 'you', 'they', 'in', 'myself',
    'mustnt', 'havent', 'is', 'them', 'it', 'then', 'am', 'an', 'each',
    'himself', 'itself', 'as', 'befor', 'at', 're', 'didnt', 'doe', 'isnt',
    'other', 'be', 'against', 'wouldnt', 'our', 'out', 'into', 'how',
    'couldnt', 'same', 'are', 'too', 'by', 'have', 'whom', 'where', 'after',
    'so', 'ourselv', 'a', 'd', 'onc', 'more', 'themselv', 'i', 'yourselv', 'm',
    'off', 'o', 'the', 'such', 's', 't', 'thi', 'hadnt', 'y', 'to', 'under',
    'did', 'but', 'through', 'll', 'own', 'had', 'do', 'while', 'down', 'him',
    'mightnt', 'that', 'ma', 'arent', 'than', 'me', 'should', 'few',
    'yourself', 'from', 'up', 'those', 'which', 'all', 'below', 'onli', 'wont',
    'dure', 'my', 'both', 've', 'neednt', 'most', 'she', 'were', 'whi',
    'herself', 'dont', 'who', 'here', 'some', 'no', 'aint', 'becaus', 'for',
    'their', 'wa', 'we', 'nor', 'can', 'not', 'werent', 'wasnt', 'and', 'of',
    'now', 'just', 'ani', 'on', 'over', 'or', 'abov', 'will', 'again', 'with',
    'what', 'there', 'shant', 'ha', 'until', 'further', 'he'
])
#STEMMED_STOPWORDS = set()
#stemmer = PorterStemmer()
#for stopword in STOPWORDS:
#    STEMMED_STOPWORDS.add(stemmer.stem(stopword))
#print STEMMED_STOPWORDS


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
        # Dictionaries for the entities lookup tables.  Each key in the
        # dictionaries is a stemmed term (either a label or synonym) or a
        # sub-phrase of a term, and each value is a set of _OntologyEntity
        # object, IRI, label text) triples, where "IRI" is the IRI of the
        # annotation property that linked the ontology entity to the term name
        # and "label text" is the text literal for the annotation.  emap_full
        # contains full term labels/synonyms, while emap_partial contains
        # sub-phrases of full term labels/synonyms.  For example, if the full
        # label is 'some words', emap_full would have the key 'some word' (the
        # stemmed version of 'some words', and emap_partial would have the keys
        # 'some' and 'word').
        self.emap_full = {}
        self.emap_partial = {}

        # Tracks the maximum encountered term size (in words).
        self.max_termsize = 0

        self.pstemmer = PorterStemmer()

    def _depunctuate(self, text):
        """
        "De-punctuates" a sentence or phrase by removing all punctuation and
        possessive forms.
        """
        # Remove possessive forms.
        for apost_char in APOST_CHARS:
            text = text.replace(apost_char + 's ', ' ')
            text = text.replace(apost_char + ' ', ' ')
    
        # Remove remaining punctuation.
        text = punct_re.sub('', text)
            
        return text

    def _stemPhrase(self, phrase):
        """
        Given a string of one or more space-separated words, returns a list of
        words in sentence order in which each word has been reduced to its
        stem.
        """
        result = []
        for word in phrase.split():
            result.append(self.pstemmer.stem(word))

        return result
    
    def _getSubPhrases(self, words):
        """
        Given a list of words (strings) in a sentence (in sentence order),
        returns a list of all possible sub-phrases in the sentence (that is,
        not including the full sentence).  Does not include phrases that
        consist solely of stop words.
        """
        maxlen = len(words) - 1

        phrases = []

        curword = 0
        while curword < len(words):
            curlen = 1
            while (curword + curlen) <= len(words) and curlen <= maxlen:
                phrasewords = words[curword:(curword + curlen)]

                # Check if the current phrase is only stopwords.
                sw_cnt = 0
                for pword in phrasewords:
                    if (pword in STOPWORDS) or (pword in STEMMED_STOPWORDS):
                        sw_cnt += 1

                if sw_cnt < len(phrasewords):
                    phrases.append(' '.join(phrasewords))

                curlen += 1

            curword += 1

        return phrases

    def _addTerm(self, entity, propiri, termstr):
        """
        Adds a term and all sub-phrases to the lookup tables.

        entity: An _OntologyEntity object.
        propiri (string): An annotation property IRI.
        termstr (string): The term text to add.
        """
        lowered = termstr.lower()

        # Apply the unicode compatibility decomposition to the string.  This
        # will, e.g., replace ligatures with their expanded equivalents and
        # replace non-standard space characters with regular space characters.
        termstr = unicodedata.normalize('NFKD', lowered)

        termstr = self._depunctuate(lowered)

        words = self._stemPhrase(lowered)

        if len(words) > self.max_termsize:
            self.max_termsize = len(words)

        stemterm = ' '.join(words)

        if stemterm not in self.emap_full:
            self.emap_full[stemterm] = set()
        self.emap_full[stemterm].add((entity, propiri, termstr))

        phrases = self._getSubPhrases(words)
        
        for phrase in phrases:
            if phrase not in self.emap_partial:
                self.emap_partial[phrase] = set()
            self.emap_partial[phrase].add((entity, propiri, termstr))

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

                    self._addTerm(entity, propiri, literalval)

    def findEntities(self, searchstr):
        """
        Searches for entities that match the given search string.  Returns a
        list of matching (_OntologyEntity object, IRI string, label text, match
        type) tuples, where "IRI string" is the IRI of the annotation property
        that connects the label text to the ontology entity, "label text" is
        the text literal for the matching annotation, and "match type" is one
        of the match type constants.

        searchstr: A string to match to entities.
        """
        searchstr = searchstr.lower()

        # Apply the unicode compatibility decomposition to the string.  This
        # will, e.g., replace ligatures with their expanded equivalents and
        # replace non-standard space characters with regular space characters.
        searchstr = unicodedata.normalize('NFKD', searchstr)

        searchstr = self._depunctuate(searchstr)

        stemwords = self._stemPhrase(searchstr)
        stemval = ' '.join(stemwords)
        subphrases = self._getSubPhrases(stemwords)

        res = []

        # Search for the full search term, and keep track of matching tuples.
        matches = set()
        if stemval in self.emap_full:
            for mtuple in self.emap_full[stemval]:
                res.append(mtuple + (MATCH_FULL,))
                matches.add(mtuple)

        if stemval in self.emap_partial:
            for mtuple in self.emap_partial[stemval]:
                res.append(mtuple + (MATCH_SUBPHRASE,))
                matches.add(mtuple)

        # Search for subphrases of the search term.  Make sure we don't return
        # entities we already found while searching for the full phrase or with
        # other partial matches.
        for subphrase in subphrases:
            if subphrase in self.emap_full:
                for mtuple in self.emap_full[subphrase]:
                    if mtuple not in matches:
                        res.append(mtuple + (MATCH_SUBPHRASE,))
                        matches.add(mtuple)

            if subphrase in self.emap_partial:
                for mtuple in self.emap_partial[subphrase]:
                    if mtuple not in matches:
                        res.append(mtuple + (MATCH_SUBPHRASE,))
                        matches.add(mtuple)

        return res

