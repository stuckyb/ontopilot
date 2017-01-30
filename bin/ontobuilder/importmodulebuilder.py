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
from tablereaderfactory import TableReaderFactory
from tablereader import TableRowError
import ontobuilder
from ontobuilder import TRUE_STRS
from ontology import Ontology
from rfc3987 import rfc3987

# Java imports.
from java.util import HashSet
from org.semanticweb.owlapi.model import IRI, OWLClassExpression
from org.semanticweb.owlapi.model import OWLObjectPropertyExpression
from org.semanticweb.owlapi.model import OWLObjectProperty


class ImportModSpecError(TableRowError):
    """
    An exception class for errors encountered in import module specifications
    in tabular input files.
    """
    def __init__(self, error_msg, tablerow):
        self.tablerow = tablerow

        new_msg = (
            'Error encountered in import module specification in '
            + self._generateContextStr(tablerow) + ':\n' + error_msg
        )

        RuntimeError.__init__(self, new_msg)


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
    REQUIRED_COLS = ('ID',)

    # Fields for which no warnings are issued if the field is missing.
    OPTIONAL_COLS = ('Exclude', 'Seed descendants', 'Reasoner', 'Ignore')

    # Default values for input table columns.
    DEFAULT_COL_VALS = {'Reasoner': 'HermiT'}

    def __init__(self, base_IRI, module_suffix, outputdir):
        """
        base_IRI: The base IRI string to use when generating module IRIs.
        module_suffix: The suffix string for generating module file names.
        outputdir: The directory in which to save the module OWL files.
        """
        self.progbar = None
        self.sourceOntologyIRI = ''

        self.base_IRI = base_IRI
        self.mod_suffix = module_suffix
        self.outputdir = os.path.abspath(outputdir)

        # Generate the directory name for local copies of source ontologies.
        self.ontcachedir = os.path.join(outputdir, 'source_ontologies')

        # Define the strings that indicate TRUE in the input files.  Note that
        # variants of these strings with different casing will also be
        # recognized.
        TRUE_STRS = ['t', 'true', 'y', 'yes']

    def _checkOutputDirs(self):
        """
        Verifies that the output directory and ontology cache directory both
        exist.  If the cache directory does not exist, _checkOutputDirs()
        attempts to create it.
        """
        # Check the main build directory.
        if not(os.path.isdir(self.outputdir)):
            raise RuntimeError('The build directory could not be found: {0}.'.format(self.outputdir))

        # Check the downloaded ontologies cache directory.
        if not(os.path.isdir(self.ontcachedir)):
            if not(os.path.exists(self.ontcachedir)):
                os.mkdir(self.ontcachedir)
            else:
                raise RuntimeError('A file with the name of the ontology cache directory already exists: {0}.  Please delete or rename the conflicting file.'.format(self.ontcachedir))

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

    def _getOutputFileName(self, ontologyIRI):
        """
        Constructs the file name for the output import module file.
        """
        # Extract the name of the source ontology file from the IRI.
        ontfile = os.path.basename(ontologyIRI)

        # Generate the file name for the ouput ontology OWL file.
        outputfile = os.path.splitext(ontfile)[0] + self.mod_suffix

        return outputfile

    def getModuleIRIStr(self, ontologyIRI):
        """
        Returns the IRI string that will be used for an import module.

        ontologyIRI: The IRI of the ontology to import.
        """
        if self.base_IRI == '':
            return ''

        outputfile = self._getOutputFileName(ontologyIRI)

        # Generate the IRI for the output ontology OWL file by parsing the base
        # path from the base IRI and then adding the new module file name to
        # the base path.
        try:
            parts = rfc3987.parse(self.base_IRI, rule='absolute_IRI')
        except ValueError as err:
            raise RuntimeError('"{0}" is not a valid base IRI for generating import module IRIs.'.format(self.base_IRI))

        newpath = os.path.join(parts['path'], outputfile)
        parts['path'] = newpath
        
        return rfc3987.compose(**parts)

    def isBuildNeeded(self, ontologyIRI, termsfile_path):
        """
        Tests whether an import module actually needs to be built.

        ontologyIRI: The IRI of the imported ontology.
        termsfile_path: The input file containing the terms to import.
        """
        # Verify that the terms file exists.
        if not(os.path.isfile(termsfile_path)):
            raise RuntimeError('Could not find the input terms file "'
                    + termsfile_path + '".')

        outputfile = self._getOutputFileName(ontologyIRI)
        outputpath = os.path.join(self.outputdir, outputfile)
    
        # If the output file already exists and the terms file was not
        # modified/created more recently, there is nothing to do.
        if os.path.isfile(outputpath):
            if os.path.getmtime(outputpath) > os.path.getmtime(termsfile_path):
                return False

        return True
        
    def buildModule(self, ontologyIRI, termsfile_path):
        """
        Builds an import module from a single external ontology and an input
        file containing a set of terms to import.  The import module will be
        saved as an OWL file with a name generated by appending self.mod_suffix
        to the base of the source ontology file name.

        ontologyIRI: The IRI of the source ontology.
        termsfile_path: The input file containing the terms to import.
        """
        # Verify that the terms file exists.
        if not(os.path.isfile(termsfile_path)):
            raise RuntimeError('Could not find the input terms file "'
                    + termsfile_path + '".')

        # Check the output directories.
        self._checkOutputDirs()

        # Extract the name of the source ontology file from the IRI and
        # generate the path to it on the local filesystem.
        ontfile = os.path.basename(ontologyIRI)
        ontfile = os.path.join(self.ontcachedir, ontfile)

        # Generate the file name and IRI for the output ontology OWL file.
        outputfile = self._getOutputFileName(ontologyIRI)
        ont_IRI = IRI.create(self.getModuleIRIStr(ontologyIRI))

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
        with TableReaderFactory(termsfile_path) as reader:
            # Read the terms to import from each table in the input file, add
            # each term to the signature set for module extraction, and add the
            # descendants of each term, if desired.
            for table in reader:
                table.setRequiredColumns(self.REQUIRED_COLS)
                table.setOptionalColumns(self.OPTIONAL_COLS)
                table.setDefaultValues(self.DEFAULT_COL_VALS)

                for row in table:
                    if not(row['Ignore'].lower() in TRUE_STRS):
                        idstr = row['ID']
                        ontobuilder.logger.info('Processing entity "' + idstr + '".')
                        owlent = sourceont.getExistingEntity(idstr)
                        if owlent == None:
                            raise ImportModSpecError(
                                'The entity "' + idstr
                                + '" could not be found in the source ontology.',
                                row
                            )
                        owlent = owlent.getOWLAPIObj()
        
                        if row['Exclude'].lower() in TRUE_STRS:
                            excluded_ents.append(owlent)
                        else:
                            self._addEntityToSignature(owlent, signature, row, reasoner_man)

        if signature.size() == 0:
            raise RuntimeError('No terms to import were found in the terms file.')
        
        reasoner_man.disposeReasoners()

        module = sourceont.extractModule(signature, ont_IRI)

        # Remove any entities that should be excluded from the final module.
        for ent in excluded_ents:
            module.removeEntity(ent)

        outputpath = os.path.join(self.outputdir, outputfile)
        module.saveOntology(outputpath)

    def _addEntityToSignature(self, owlent, signature, trow, reasoner_man):
        """
        Adds an entity to a signature set for an import module extraction.  If
        requested, also finds all descendents of a given ontology entity (class
        or property) and adds them to the signature set, too.
    
        owlent: An OWL API ontology entity object.
        signature: A Java Set.
        trow: A row from an input table.
        reasoner_man: A _ReasonerManager from which to obtain an OWL reasoner.
        """
        signature.add(owlent)
                
        if trow['Seed descendants'].lower() in TRUE_STRS:
            # Get the reasoner name, using HermiT as the default.
            reasoner_name = trow['Reasoner']
    
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

    def disposeReasoners(self):
        for reasoner_name in self.reasoners:
            self.reasoners[reasoner_name].dispose()

        self.reasoners = {}

