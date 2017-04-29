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
from __future__ import unicode_literals

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
    This class is required by _MoreAdvancedEntityChecker to build a functioning
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
    handles data property names, unlike the OWL API version.  For each
    getOWL*() method, the general strategy is to first attempt looking up the
    entity name using the OWL API's ShortFormEntityChecker, which can resolve
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
        (enclosed in single quotes, with or without a prefix), full IRI,
        relative IRI, "short form" IRI (no prefix), prefix IRI, or OBO ID.

        name: The identifier to resolve.
        Returns: An OWL API IRI object.
        """
        if (name[0] == '<') and (name[-1] == '>'):
            # Handle full IRIs.
            return IRI.create(name[1:-1])
        else:
            # Handle everything else (labels, prefix IRIs, OBO IDs, etc.).
            return self.ontology.resolveIdentifier(name)

    def getOWLClass(self, name):
        classobj = self.sf_checker.getOWLClass(name)
        if classobj is None:
            termIRI = self._resolveName(name)
            classobj = self.ontology.getExistingClass(termIRI)

        if classobj is not None:
            return classobj.getOWLAPIObj()
        else:
            return None

    def getOWLObjectProperty(self, name):
        propobj = self.sf_checker.getOWLObjectProperty(name)
        if propobj is None:
            termIRI = self._resolveName(name)
            propobj = self.ontology.getExistingObjectProperty(termIRI)

        if propobj is not None:
            return propobj.getOWLAPIObj()
        else:
            return None

    def getOWLDataProperty(self, name):
        propobj = self.sf_checker.getOWLDataProperty(name)
        if propobj is None:
            termIRI = self._resolveName(name)
            propobj = self.ontology.getExistingDataProperty(termIRI)

        if propobj is not None:
            return propobj.getOWLAPIObj()
        else:
            return None

    def getOWLAnnotationProperty(self, name):
        propobj = self.sf_checker.getOWLAnnotationProperty(name)
        if propobj is None:
            termIRI = self._resolveName(name)
            propobj = self.ontology.getExistingAnnotationProperty(termIRI)

        if propobj is not None:
            return propobj.getOWLAPIObj()
        else:
            return None

    def getOWLDatatype(self, name):
        return self.sf_checker.getOWLDatatype(name)

    def getOWLIndividual(self, name):
        indvobj = self.sf_checker.getOWLIndividual(name)
        if indvobj is None:
            indvIRI = self._resolveName(name)
            indvobj = self.ontology.getExistingIndividual(indvIRI)

        if indvobj is not None:
            return indvobj.getOWLAPIObj()
        else:
            return None


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

    def parseLiteral(self, literal_ms_exp):
        """
        Parses the "literal" production of Manchester Syntax.
        """
        self.parser.setStringToParse(literal_ms_exp);

        return self.parser.parseLiteral(None)

    def parseDataRange(self, datarange_ms_exp):
        """
        Parses the "dataRange" production of Manchester Syntax.
        """
        self.parser.setStringToParse(datarange_ms_exp);

        return self.parser.parseDataRange()

    def parseClassExpression(self, manchester_exp):
        """
        Parses the "description" production of Manchester Syntax.  Returns OWL
        API class expression objects.
        """
        self.parser.setStringToParse(manchester_exp);

        return self.parser.parseClassExpression()

