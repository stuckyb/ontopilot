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


# Python imports.
from __future__ import unicode_literals
from ontopilot import logger

# Java imports.
from org.semanticweb.elk.owlapi import ElkReasonerFactory
from org.semanticweb.HermiT import ReasonerFactory as HermiTReasonerFactory
from com.clarkparsia.pellet.owlapiv3 import PelletReasonerFactory
from uk.ac.manchester.cs.jfact import JFactFactory


class ReasonerManager:
    """
    Manages DL reasoners for Ontology objects.  Given a string designating a
    reasoner type and a source ontology, ReasonerManager will return a
    corresponding reasoner object and ensure that only one instance of each
    reasoner type is created.  ReasonerManagers will also ensure that the
    reasoner instances they manage remain synchronized with their source
    ontologies by only instantiating non-buffering reasoners.
    """
    def __init__(self, ontology):
        self.ontology = ontology

        # A dictionary to keep track of instantiated reasoners.
        self.reasoners = {}

    def getOntology(self):
        """
        Returns the Ontology object associated with this ReasonerManager.
        """
        return self.ontology

    def getReasoner(self, reasoner_name):
        """
        Returns an instance of a reasoner matching the value of the string
        "reasoner_name".  Supported values are "ELK", "HermiT", "Pellet", or
        "JFact" (the strings are not case sensitive).  ReasonerManager ensures
        that reasoner instances are effectively singletons (that is, subsequent
        requests for the same reasoner type return the same reasoner instance).

        reasoner_name: A string specifying the type of reasoner to instantiate.
        """
        reasoner_name = reasoner_name.lower().strip()

        if reasoner_name not in self.reasoners:
            owlont = self.getOntology().getOWLOntology()

            rfact = None
            if reasoner_name == 'elk':
                logger.info('Creating ELK reasoner...')
                rfact = ElkReasonerFactory()
            elif reasoner_name == 'hermit':
                logger.info('Creating HermiT reasoner...')
                rfact = HermiTReasonerFactory()
            elif reasoner_name == 'pellet':
                logger.info('Creating Pellet reasoner...')
                rfact = PelletReasonerFactory()
            elif reasoner_name == 'jfact':
                logger.info('Creating JFact reasoner...')
                rfact = JFactFactory()

            if rfact is not None:
                self.reasoners[reasoner_name] = rfact.createNonBufferingReasoner(owlont)
            else:
                raise RuntimeError(
                    'Unrecognized DL reasoner name: '
                    + reasoner_name + '.'
                )

        return self.reasoners[reasoner_name]

    def disposeReasoners(self):
        """
        Runs the dispose() operation on all reasoner instances.  Note that this
        is not implemented as an automatic "destructor" because there is no
        guarantee that instances of reasoners returned by ReasonerManager will
        not outlive the ReasonerManager instance.
        """
        for reasoner_name in self.reasoners:
            self.reasoners[reasoner_name].dispose()

        self.reasoners = {}

