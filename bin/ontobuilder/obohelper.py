#
# Provides constants and functions for working with OBO ID strings and
# converting them to/from OWL API IRI objects.
#

# Python imports.
import re
import os
import urlparse

# Java imports.
from org.semanticweb.owlapi.model import IRI


OBO_BASE_IRI = 'http://purl.obolibrary.org/obo/'

# Compile a regular expression for matching OBO ID strings.
oboid_re = re.compile('[A-Za-z]+:\d{7}')


def isOboID(termIDstr):
    """
    Tries to determine if a given text string is an OBO ID; that is, an ID of
    the form "PO:0000003".  Returns True if the string is an OBO ID.
    """
    res = oboid_re.match(termIDstr)

    return res != None

def termIRIToOboID(termIRI):
    """
    Converts an IRI for an ontology term into an OB ID; that is, a string
    of the form "PO:0000003".

      termIRI: The IRI of the ontology term.  Can be either an IRI object
               or a string.
    """
    if isinstance(termIRI, IRI):
        termIRIstr = termIRI.toString()
    else:
        termIRIstr = termIRI

    IRIpath = urlparse.urlsplit(termIRIstr).path
    rawID = os.path.split(IRIpath)[1]

    return rawID.replace('_', ':')

def oboIDToIRI(oboID):
    """
    Converts an OBO ID string (i.e., a string of the form "PO:0000003") to
    an IRI.
    """
    oboID = oboID.strip()
    tIRI = IRI.create(OBO_BASE_IRI + oboID.replace(':', '_'))

    return tIRI

