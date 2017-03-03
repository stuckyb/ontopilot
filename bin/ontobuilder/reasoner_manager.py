
# Python imports.
from ontobuilder import logger

# Java imports.
from org.semanticweb.elk.owlapi import ElkReasonerFactory
from org.semanticweb import HermiT


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
        "reasoner_name".  Supported values are "ELK" or "HermiT" (the strings
        are not case sensitive).  ReasonerManager ensures that reasoner
        instances are effectively singletons (that is, subsequent requests for
        the same reasoner type return the same reasoner instance).

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
                rfact = HermiT.ReasonerFactory()

            if rfact != None:
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

