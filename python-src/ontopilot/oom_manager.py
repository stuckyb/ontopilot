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
# Manages creation and maintenance of OWL API OWLOntologyManager (OOM) objects.
# Provides methods for creating new OOM objects and updating the IRI mappings
# of existing OOM objects.  This allows client code to have distinct OOMs, if
# needed, while still ensuring that IRI mappings apply system wide.
#

# Python imports.
from __future__ import unicode_literals

# Java imports.
from org.semanticweb.owlapi.util import SimpleIRIMapper
from org.semanticweb.owlapi.apibinding import OWLManager


# Stores all custom mappings of ontology IRIs to document IRIs.
_IRImappings = {}

# Keeps track of all OOMs created by the OOM manager.  This implementation is
# somewhat inefficient, because OOMs will never be deallocated/garbage
# collected due to this list always keeping a reference to them.  In practice,
# this is unlikely to matter because few OOMs will be instantiated during a
# typical OntoPilot run.  Even when running the unit tests, which create a
# *lot* of OOMs, it hardly made a difference in overall memory consumption:
# e.g., for one pair of runs, I observed a peak of 722 MB without storing
# references and 733 MB with reference storing.  However, if needed, this could
# be optimized to improve memory management.
_ooms_list = []


def lookupDocumentIRI(oom, ontologyIRI):
    """
    Given an OOM, checks all IRI mappers registered with the OOM until a
    mapping for the ontology IRI is found.  If no mapping is found, returns
    None.  This is functionality that appears to be missing in the
    OWLOntologyManager public interface.

    oom: An OWLOntologyManager.
    ontologyIRI: An OWL API IRI object.
    """
    for mapper in oom.getIRIMappers():
        res = mapper.getDocumentIRI(ontologyIRI)
        if res is not None:
            return res

    return None

def addNewIRIMapping(ontologyIRI, documentIRI):
    """
    Adds a new mapping of an ontology IRI to a document IRI.  All previously
    created OOMs will be updated with the new mapping, and the new mapping will
    automatically be applied to any new OOMs that are created after the mapping
    is added.

    ontologyIRI: An OWL API IRI object.
    documentIRI: An OWL API IRI object.
    """
    if ontologyIRI.equals(documentIRI):
        return

    if ontologyIRI not in _IRImappings:
        _IRImappings[ontologyIRI] = documentIRI

        for oom in _ooms_list:
            if lookupDocumentIRI(oom, ontologyIRI) is None:
                oom.getIRIMappers().add(
                    SimpleIRIMapper(ontologyIRI, documentIRI)
                )

    elif not(_IRImappings[ontologyIRI].equals(documentIRI)):
        raise RuntimeError(
            'Could not create the mapping of <{0}> to <{1}>, because a '
            'conflicting mapping of <{0}> to <{2}> already exists.'.format(
                    ontologyIRI.toString(), documentIRI.toString(),
                    _IRImappings[ontologyIRI].toString()
            )
        )

def getNewOWLOntologyManager():
    """
    Creates and returns a new OWLOntologyManager.
    """
    oom = OWLManager.createOWLOntologyManager()
    _ooms_list.append(oom)

    # Add any missing IRI mappings.
    for ontologyIRI in _IRImappings:
        if lookupDocumentIRI(oom, ontologyIRI) is None:
            oom.getIRIMappers().add(
                SimpleIRIMapper(ontologyIRI, _IRImappings[ontologyIRI])
            )

    return oom

