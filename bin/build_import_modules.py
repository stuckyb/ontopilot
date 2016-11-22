#!/usr/bin/env jython

import csv
import os
import logging
from argparse import ArgumentParser
from ontobuilder.tablereader import CSVTableReader
from ontobuilder import ImportModuleBuilder


# Set the format for logging output.
logging.basicConfig(format='\n%(levelname)s: %(message)s\n')

argp = ArgumentParser(description='Processes a single CSV file of \
terms/entities to extract from a source ontology.  The results are written to \
an output file in OWL format.')
argp.add_argument('-i', '--importsfile', type=str, required=True, help='A CSV \
file containing the set of ontologies to import.')
argp.add_argument('-s', '--outputsuffix', type=str, required=True, help='A \
suffix to use for naming the import module OWL files.')
argp.add_argument('-b', '--baseIRI', type=str, required=True, help='The base \
IRI to use for generating IRIs for OWL module files.')
args = argp.parse_args()

# This is used to define unique values of the ontology ID, the default xmlns
# attribute, and the xml:base attribute for the generated OWL file.  If these
# are not set, Protege does not seem to be able to deal with the imports, at
# least not reliably.
IRI_BASE = args.baseIRI

# Verify that the imports file exists.
if not(os.path.isfile(args.importsfile)):
    raise RuntimeError('The imports CSV file could not be found.')

mbuilder = ImportModuleBuilder(IRI_BASE)

with CSVTableReader(args.importsfile) as ireader:
    for table in ireader:
        table.setRequiredColumns(['Termsfile', 'IRI'])
    
        for row in table:
            termsfile_path = row['Termsfile']
            # If the termsfile path is a relative path, convert it to an
            # absolute path using the location of the top-level imports table
            # file as the base.
            if not(os.path.isabs(termsfile_path)):
                termsdir = os.path.dirname(os.path.abspath(args.importsfile))
                termsfile_path = os.path.join(termsdir, termsfile_path)
    
            if mbuilder.isBuildNeeded(row['IRI'], termsfile_path, args.outputsuffix):
                print ('Building the ' + row['name'] + ' (' + row['IRI']
                        + ') import module.')
                mbuilder.buildModule(row['IRI'], termsfile_path, args.outputsuffix)
            else:
                print ('The ' + row['name'] + ' (' + row['IRI']
                        + ') import module is already up-to-date.')

