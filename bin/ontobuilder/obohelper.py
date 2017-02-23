#
# Provides constants and functions for working with OBO ID strings and
# converting them to/from OWL API IRI objects and IRI strings.
#

# Python imports.
import re

# Java imports.
from org.semanticweb.owlapi.model import IRI


OBO_BASE_IRI = 'http://purl.obolibrary.org/obo/'

# Compile a regular expression for matching OBO ID strings.  The precise format
# for a valid OBO ID string is taken from
# http://www.obofoundry.org/id-policy.html.
oboid_re = re.compile('[A-Za-z]+(_[A-Za-z]+)?:\d+$')

# Compile a regular expression for parsing "raw" OBO IDs taken from OBO Foundry
# IRIs.  Use named regular expession match groups to avoid incorrect group
# references when getting the results from the MatchObject result.
raw_oboid_re = re.compile(
    '(?P<idspace>[A-Za-z]+(_[A-Za-z]+)?)_(?P<localid>\d+)$'
)

# Compile a regular expression for recognizing valid OBO prefixes (also known
# as OBO "ID spaces").
obo_prefix_re = re.compile('[A-Za-z]+(_[A-Za-z]+)?$')


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

    termIRI: The IRI of the ontology term.  Can be either an IRI object or a
        string.
    """
    if isinstance(termIRI, IRI):
        termIRIstr = termIRI.toString()
    else:
        termIRIstr = termIRI

    invalid_IRI_msg = (
        'The IRI <{0}> is not an OBO Foundry-compliant IRI, so it cannot be '
        'converted to an OBO ID.'.format(termIRIstr)
    )

    # First, verify that the IRI is OBO Foundry compliant.
    if not(termIRIstr.startswith(OBO_BASE_IRI)):
        raise RuntimeError(invalid_IRI_msg)

    rawID = termIRIstr.replace(OBO_BASE_IRI, '', 1)
    res = raw_oboid_re.match(rawID)

    if res == None:
        raise RuntimeError(invalid_IRI_msg)
    
    # Convert it to an OBO ID.
    obIDstr = res.group('idspace') + ':' + res.group('localid')

    return obIDstr

def oboIDToIRI(oboID):
    """
    Converts an OBO ID string (i.e., a string of the form "PO:0000003") to
    an IRI.
    """
    oboID = oboID.strip()

    if not(isOboID(oboID)):
        raise RuntimeError(
            'The string "{0}" is not a valid OBO ID, so it cannot be '
            'converted to an OBO Foundry IRI.'.format(oboID)
        )

    tIRI = IRI.create(OBO_BASE_IRI + oboID.replace(':', '_'))

    return tIRI

def getIRIForOboPrefix(obo_prefix):
    """
    Returns the IRI string that maps to a given OBO prefix (the prefix is also
    called the OBO "ID space").
    """
    # Verify that we have a valid OBO prefix.
    res = obo_prefix_re.match(obo_prefix)

    if res == None:
        raise RuntimeError(
            'The string "{0}" is not a valid OBO prefix (also known as as the '
            '"ID space" for OBO identifiers), so it cannot be converted to an '
            'OBO Foundry IRI.'.format(obo_prefix)
        )

    return OBO_BASE_IRI + obo_prefix

