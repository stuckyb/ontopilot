#!/usr/bin/python

import csv
import subprocess
import os
from urllib import FancyURLopener
from urllib2 import HTTPError
from argparse import ArgumentParser
from progressbar import ProgressBar, Percentage, Bar, ETA
import math


class URLOpenerWithErrorHandling(FancyURLopener):
    """
    Extends FancyURLopener by adding better error handling for unrecoverable
    HTTP errors (e.g., 404).
    """
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        raise HTTPError(url, errcode, errmsg, headers, fp)

class ImportModuleBuilder:
    """
    Builds import modules using terms from an external ontology.
    """
    def __init__(self):
        self.progbar = None
        self.sourceOntologyIRI = ''

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
    
    def buildModule(self, ontologyIRI, termsfile_path, outputsuffix):
        """
        Builds an import module from a single external ontology and a CSV file
        containing a set of terms to import.  The import module will be saved
        as an OWL file with the name specified by outputfile.
        """
        # Verify that the source ontology file exists; if not, download it.
        ontfile = os.path.basename(ontologyIRI)
        if not(os.path.isfile(ontfile)):
            opener = URLOpenerWithErrorHandling()
            try:
                self.sourceOntologyIRI = ontologyIRI
                opener.retrieve(ontologyIRI, ontfile, self._updateDownloadProgress)
            except HTTPError as err:
                raise RuntimeError('Unable to download the external ontology at "'
                        + ontologyIRI + '": ' + str(err))
    
        # Verify that the terms file exists.
        if not(os.path.isfile(termsfile_path)):
            raise RuntimeError('Could not find the terms CSV file "'
                    + termsfile_path + '".')
    
        # Build two lists of the IDs of all terms to import: one for terms that define
        # the full seed set, and one for terms whose subclasses will also be pulled
        # into the seed set.
        termIDs = []
        termIDs_to_expand = []
        with open(termsfile_path) as filein:
            reader = csv.DictReader(filein)
        
            for row in reader:
                if row['seed_subclasses'].strip().lower() in true_strs:
                    termIDs_to_expand.append(row['ID'])
                else:
                    termIDs.append(row['ID'])
        
        # Use OWLTools to generate temporary import modules for each list of terms, and
        # keep a list of the generated temporary import modules.
        temp_modules = []
        
        # Generate the file name and IRI for the ouput ontology OWL file.
        outputfile = os.path.splitext(ontfile)[0] + outputsuffix
        ont_IRI = IRI_BASE + outputfile
        
        # Terms for which we don't explicitly add subclasses to the seed set.
        if len(termIDs) > 0:
            tmpname = outputfile + '-tmp0.owl'
            command = ['owltools', ontfile, '--extract-module', '-m', 'STAR']
            command += termIDs + ['--set-ontology-id', ont_IRI, '-o', tmpname]
            subprocess.call(command)
            temp_modules.append(tmpname)
        
        # Terms for which we explicitly add subclasses to the seed set.
        if len(termIDs_to_expand) > 0:
            tmpname = outputfile + '-tmp1.owl'
            command = ['owltools', ontfile, '--extract-module', '-d', '-m', 'STAR']
            command += termIDs_to_expand + ['--set-ontology-id', ont_IRI, '-o', tmpname]
            subprocess.call(command)
            temp_modules.append(tmpname)
        
        # Generate the final import module.
        if len(temp_modules) == 1:
            # Only one temporary module was created, so just rename it.
            os.rename(temp_modules[0], outputfile)
        elif len(temp_modules) > 1:
            # Merge the temporary modules.
            command = ['owltools'] + temp_modules + ['--merge-support-ontologies']
            command += ['--set-ontology-id', ont_IRI, '-o', outputfile]
            subprocess.call(command)
        else:
            raise RuntimeError('No terms to import were found in the terms file.')


# This is used to define unique values of the ontology ID, the default xmlns
# attribute, and the xml:base attribute for the generated OWL file.  If these
# are not set, Protege does not seem to be able to deal with the imports, at
# least not reliably.
IRI_BASE = "https://raw.githubusercontent.com/PlantPhenoOntology/PPO/master/import_modules/"

argp = ArgumentParser(description='Processes a single CSV file of \
terms/entities to extract from a source ontology.  The results are written to \
an output file in OWL format.')
argp.add_argument('-i', '--importsfile', type=str, required=True, help='A CSV \
file containing the set of ontologies to import.')
argp.add_argument('-s', '--outputsuffix', type=str, required=True, help='A \
suffix to use for naming the import module OWL files.')
args = argp.parse_args()

# Define the strings that indicate TRUE in the CSV files.  Note that variants
# of these strings with different casing will also be recognized.
true_strs = ['t', 'true', 'y', 'yes']

# Verify that the imports file exists.
if not(os.path.isfile(args.importsfile)):
    raise RuntimeError('The imports CSV file could not be found.')

mbuilder = ImportModuleBuilder()

with open(args.importsfile) as ifilein:
    ireader = csv.DictReader(ifilein)

    for row in ireader:
        termsfile_path = row['termsfile']
        # If the termsfile path is a relative path, convert it to an absolute
        # path using the location of the top-level CSV file as the base.
        if not(os.path.isabs(termsfile_path)):
            termsdir = os.path.dirname(os.path.abspath(args.importsfile))
            termsfile_path = os.path.join(termsdir, termsfile_path)

        mbuilder.buildModule(row['IRI'], termsfile_path, args.outputsuffix)

