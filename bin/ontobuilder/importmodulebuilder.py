#
# Provides a class, ImportModuleBuilder, for building import module OWL files
# by extracting terms from an existing ontology.
#

# Python imports.
import csv
import os
from urllib import FancyURLopener
from urllib2 import HTTPError
import logging
from progressbar import ProgressBar, Percentage, Bar, ETA
import math
import ontobuilder
from ontology import Ontology

# Java imports.
from java.util import HashSet
from org.semanticweb.owlapi.model import IRI, OWLClassExpression
from org.semanticweb.owlapi.model import OWLObjectPropertyExpression
from org.semanticweb.owlapi.model import OWLObjectProperty


class URLOpenerWithErrorHandling(FancyURLopener):
    """
    Extends FancyURLopener by adding better error handling for unrecoverable
    HTTP errors (e.g., 404).
    """
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        raise HTTPError(url, errcode, errmsg, headers, fp)


class ImportModuleBuilder:
    """
    Builds import modules using terms from an external ontology.  The argument
    "base_IRI" is the base IRI string to use when generating IRIs for module
    OWL files.
    """
    # Required fields (i.e., keys) for all import term specifications.
    REQUIRED_FIELDS = ('ID')

    # Fields for which no warnings are issued if the field is missing.
    NO_WARN_FIELDS = ('Exclude', 'Seed descendants', 'Reasoner')

    def _getDescField(self, desc, key, defaultval=''):
        """
        Retrieves the value of a field from a dictionary describing a term to
        import from a source ontology, with all beginning and ending white
        space removed.  If the field (i.e., key) does not exist in the
        dictionary and the field is required, an exception is thrown.  If the
        key does not exist and the field is optional, a warning is issued
        (unless the field is listed in NO_WARN_FIELDS) and defaultval is
        returned.
        """
        if key in desc:
            return desc[key].strip()
        else:
            if key in self.REQUIRED_FIELDS:
                raise RuntimeError(
                    'The required field "' + key
                    + '" was missing in the import term description.'
                )
            elif key not in self.NO_WARN_FIELDS:
                logging.warning(
                    'The field "' + key
                    + '" was missing in the description of the import term "'
                    + self._getDescField(desc, 'ID') + '".'
                )
                return defaultval
            else:
                return defaultval

    def __init__(self, base_IRI):
        self.progbar = None
        self.sourceOntologyIRI = ''

        self.base_IRI = base_IRI

        # Define the strings that indicate TRUE in the CSV files.  Note that
        # variants of these strings with different casing will also be
        # recognized.
        self.true_strs = ['t', 'true', 'y', 'yes']

    def _updateDownloadProgress(self, blocks_transferred, blocksize, filesize):
        """
        Instantiates and updates a console-based progress bar to indicate
        ontology download progress.  This method should be passed to the
        retrieve() method of URLOpenerWithErrorHandling.
        """
        #print blocks_transferred, blocksize, filesize
        if blocks_transferred == 0:
            self.progbar = ProgressBar(
                widgets=[Percentage(), '', Bar(marker='-', left='[', right=']'), ' ' , ETA()],
                maxval=int(math.ceil(float(filesize) / blocksize))
            )
            print '\nDownloading ' + self.sourceOntologyIRI
            self.progbar.start()
        else:
            self.progbar.update(blocks_transferred)
            if blocks_transferred == self.progbar.maxval:
                self.progbar.finish()
                print

    def _getOutputFileName(self, ontologyIRI, outputsuffix):
        """
        Constructs the file name for the output import module file.
        """
        # Extract the name of the source ontology file from the IRI.
        ontfile = os.path.basename(ontologyIRI)

        # Generate the file name for the ouput ontology OWL file.
        outputfile = os.path.splitext(ontfile)[0] + outputsuffix

        return outputfile

    def isBuildNeeded(self, ontologyIRI, termsfile_path, outputsuffix):
        """
        Tests whether an import module actually needs to be built.  If the file
        located at termsfile_path has 
        """
        outputfile = self._getOutputFileName(ontologyIRI, outputsuffix)
    
        # If the output file already exists and the terms file was not
        # modified/created more recently, there is nothing to do.
        if os.path.isfile(outputfile):
            if os.path.getmtime(outputfile) > os.path.getmtime(termsfile_path):
                return False

        return True
        
    def buildModule(self, ontologyIRI, termsfile_path, outputsuffix):
        """
        Builds an import module from a single external ontology and a CSV file
        containing a set of terms to import.  The import module will be saved
        as an OWL file with a name generated by appending outputsuffix to the
        base of the source ontology file name.

          ontologyIRI: The IRI of the source ontology.
          termsfile_path: The CSV file containing the terms to import.
          outputsuffix: A string to use when generating file names for the
                        import module OWL files.
        """
        # Verify that the terms file exists.
        if not(os.path.isfile(termsfile_path)):
            raise RuntimeError('Could not find the terms CSV file "'
                    + termsfile_path + '".')

        # Extract the name of the source ontology file from the IRI.
        ontfile = os.path.basename(ontologyIRI)

        # Generate the file name and IRI for the ouput ontology OWL file.
        outputfile = self._getOutputFileName(ontologyIRI, outputsuffix)
        ont_IRI = IRI.create(self.base_IRI + outputfile)

        # Verify that the source ontology file exists; if not, download it.
        if not(os.path.isfile(ontfile)):
            opener = URLOpenerWithErrorHandling()
            try:
                self.sourceOntologyIRI = ontologyIRI
                opener.retrieve(ontologyIRI, ontfile, self._updateDownloadProgress)
            except HTTPError as err:
                raise RuntimeError('Unable to download the external ontology at "'
                        + ontologyIRI + '": ' + str(err))

        ontobuilder.logger.info('Loading source ontology from file ' + ontfile + '.')
        sourceont = Ontology(ontfile)
        reasoner_man = _ReasonerManager(sourceont)

        signature = HashSet()
        excluded_ents = []
        with open(termsfile_path) as filein:
            reader = csv.DictReader(filein)
        
            # Read the terms to import from the CSV file, add each term to the
            # signature set for module extraction, and add the descendents of
            # each term, if desired.
            for row in reader:
                idstr = self._getDescField(row, 'ID')
                ontobuilder.logger.info('Processing entity ' + idstr + '.')
                owlent = sourceont.getEntityByID(idstr)
                if owlent == None:
                    raise RuntimeError(idstr + ' could not be found in the source ontology')

                if self._getDescField(row, 'Exclude') in self.true_strs:
                    excluded_ents.append(owlent)
                else:
                    signature.add(owlent)
    
                    if self._getDescField(row, 'Seed descendants') in self.true_strs:
                        # Get the reasoner name from the input file, using
                        # HermiT as the default.
                        reasoner_name = self._getDescField(row, 'Reasoner', 'HermiT')

                        # Get the reasoner instance.
                        reasoner = reasoner_man.getReasoner(reasoner_name)
    
                        # Get the entity's subclasses or subproperties.
                        ontobuilder.logger.info('Adding descendant entities of ' + str(owlent) + '.')
                        if isinstance(owlent, OWLClassExpression):
                            signature.addAll(reasoner.getSubClasses(owlent, False).getFlattened())
                        elif isinstance(owlent, OWLObjectPropertyExpression):
                            propset = reasoner.getSubObjectProperties(owlent, False).getFlattened()
                            # Note that getSubObjectProperties() can return both
                            # named properties and ObjectInverseOf (i.e., unnamed)
                            # properties, so we need to check the type of each
                            # property before adding it to the module signature.
                            for prop in propset:
                                if isinstance(prop, OWLObjectProperty):
                                    signature.add(prop)

        if signature.size() == 0:
            raise RuntimeError('No terms to import were found in the terms file.')
        
        if reasoner != None:
            reasoner.dispose()

        module = sourceont.extractModule(signature, ont_IRI)

        # Remove any entities that should be excluded from the final module.
        for ent in excluded_ents:
            module.removeEntity(ent)

        module.saveOntology(outputfile)


class _ReasonerManager:
    """
    Manages DL reasoners for ImportModuleBuilder objects.  Given a string
    designating a reasoner type and a source ontology, _ReasonerManager will
    return a corresponding reasoner object and ensure that only one instance of
    each reasoner type is created.
    """
    def __init__(self, ontology):
        self.ontology = ontology

        # A dictionary to keep track of instantiated reasoners.
        self.reasoners = {}

    def getReasoner(self, reasoner_name):
        reasoner_name = reasoner_name.lower().strip()

        if reasoner_name not in self.reasoners:
            if reasoner_name == 'elk':
                ontobuilder.logger.info('Creating ELK reasoner...')
                self.reasoners[reasoner_name] = self.ontology.getELKReasoner()
            elif reasoner_name == 'hermit':
                ontobuilder.logger.info('Creating HermiT reasoner...')
                self.reasoners[reasoner_name] = self.ontology.getHermitReasoner()
            else:
                raise RuntimeError(
                    'Unrecognized DL reasoner name: '
                    + reasoner_name + '.'
                )

        return self.reasoners[reasoner_name]

