#
# Provides classes to support parsing Manchester Syntax (MS) statements.  The
# most important of these is ManchesterSyntaxParserHelper, which implements a
# simple, high-level interface for parsing MS statements.
#
# A very annoying detail of the OWL API is that, when parsing class expressions
# in Manchester Syntax, rdfs:labels and full IRIs are properly handled for all
# OWL entities *except for* data properties and annotation properties.  This
# means that if a class expression references a data property or annotation
# property by its label or full IRI, the OWL API parser will fail.  The OWL
# API's Manchester Syntax parser, using the default AdvancedEntityChecker, will
# only accept "short form" names for data properties and annotation properties.
# I have carefully examined the OWL API source code to confirm this behavior.
# This is true in both the version 4 code and the most recent (as of Oct. 5,
# 2016) version 5 code.
#
# There are at least two ways to deal with this.  The first is to preprocess
# all MS class expressions by replacing data property and annotation property
# references with their "short form" equivalents, then passing the expression
# to the parser.  The second is to write a custom implementation of the
# OWLEntityChecker interface and hand this to an instance of
# ManchesterOWLSyntaxParserImpl as a replacement for the OWL API's
# AdvancedEntityChecker.  I took the latter approach here, which seemed like
# the cleanest solution.
#

# Python imports.

# Java imports.
from java.util import HashSet
from org.semanticweb.owlapi.model import IRI
from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxParserImpl
from org.semanticweb.owlapi import OWLAPIConfigProvider
from org.semanticweb.owlapi.util import SimpleIRIShortFormProvider
from org.semanticweb.owlapi.util import ShortFormProvider
from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter
from org.semanticweb.owlapi.expression import OWLEntityChecker
from org.semanticweb.owlapi.expression import ShortFormEntityChecker


class _BasicShortFormProvider(ShortFormProvider):
    """
    This class is required by MoreAdvancedEntityChecker to build a functioning
    ShortFormEntityChecker.
    """
    def __init__(self):
        self.iri_sfp = SimpleIRIShortFormProvider()

    def dispose():
        pass

    def getShortForm(self, owl_entity):
        """
        Given an OWL API entity object, returns the "short form" version of the
        entity's IRI.
        """
        return self.iri_sfp.getShortForm(owl_entity.getIRI())


class _MoreAdvancedEntityChecker(OWLEntityChecker):
    """
    This is a replacement for AdvancedEntityChecker that is part of the
    Manchester Syntax parser of the OWL API.  This implementation correctly
    handles data property names, unlike the OWL API version.  For each get___()
    function, the general strategy is to first attempt looking up the entity
    name using the OWL API's ShortFormEntityChecker, which can resolve
    "simpleIRI" names as defined in the MS grammar (these are basically short-
    form IRIs without a prefix).  If this lookup fails, then name resolution
    falls to the lookup services of the Ontology class.
    """
    def __init__(self, ontology):
        self.ontology = ontology
        
        # Create a ShortFormEntityChecker.  This allows looking up "local" IRI
        # names to retrieve the corresponding OWL entity.  These IRIs are the
        # "simpleIRI" production of the Manchester Syntax grammar.
        ontset = HashSet(1)
        ontset.add(self.ontology.getOWLOntology())
        self.sf_checker = ShortFormEntityChecker(
            BidirectionalShortFormProviderAdapter(
                self.ontology.ontman, ontset, _BasicShortFormProvider()
            )
        )

    def _resolveName(self, name):
        """
        Attempts to resolve an entity name in a Manchester Syntax statement to
        a valid IRI.  Entity names must be one of the following: rdfs:label
        (enclosed in single quotes), full IRI, "short form" IRI (no prefix),
        prefix IRI, or OBO ID.
        """
        if (name[0] == "'") and (name[-1] == "'"):
            # Handle rdfs:labels.
            return self.ontology.labelToIRI(name[1:-1])
        elif (name[0] == '<') and (name[-1] == '>'):
            # Handle full IRIs.
            return IRI.create(name[1:-1])
        else:
            # Handle everything else (prefix IRIs, OBO IDs).
            return self.ontology.expandIdentifier(name)

    def getOWLClass(self, name):
        classobj = self.sf_checker.getOWLClass(name)
        if classobj == None:
            termIRI = self._resolveName(name)
            classobj = self.ontology.getExistingClass(termIRI)

        return classobj

    def getOWLObjectProperty(self, name):
        propobj = self.sf_checker.getOWLObjectProperty(name)
        if propobj == None:
            termIRI = self._resolveName(name)
            propobj = self.ontology.getExistingObjectProperty(termIRI)

        return propobj

    def getOWLDataProperty(self, name):
        propobj = self.sf_checker.getOWLDataProperty(name)
        if propobj == None:
            termIRI = self._resolveName(name)
            propobj = self.ontology.getExistingDataProperty(termIRI)

        return propobj

    def getOWLAnnotationProperty(self, name):
        propobj = self.sf_checker.getOWLAnnotationProperty(name)
        if propobj == None:
            termIRI = self._resolveName(name)
            propobj = self.ontology.getExistingAnnotationProperty(termIRI)

        return propobj

    def getOWLDatatype(self, name):
        return self.sf_checker.getOWLDatatype(name)

    def getOWLIndividual(self, name):
        indvobj = self.sf_checker.getOWLIndividual(name)
        if indvobj == None:
            indvIRI = self._resolveName(name)
            indvobj = self.ontology.getExistingIndividual(indvIRI)

        return indvobj


class ManchesterSyntaxParserHelper:
    """
    Provides a simple interface for parsing Manchester Syntax statements.
    """
    def __init__(self, ontology):
        self.ontology = ontology

        self.parser = ManchesterOWLSyntaxParserImpl(
                OWLAPIConfigProvider(), self.ontology.df
        )
        self.parser.setOWLEntityChecker(_MoreAdvancedEntityChecker(self.ontology))

    
    def parseDataRange(self, datarange_ms_exp):
        """
        Parses the "dataRange" production of Manchester Syntax.
        """
        self.parser.setStringToParse(datarange_ms_exp);

        return self.parser.parseDataRange()

    def parseClassExpression(self, manchester_exp):
        """
        Parses the "description" production of Manchester Syntax.
        """
        self.parser.setStringToParse(manchester_exp);

        return self.parser.parseClassExpression()

