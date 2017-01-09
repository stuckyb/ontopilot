#!/usr/bin/env jython

# Python imports.
import os
import sys
import logging
from argparse import ArgumentParser
from ontobuilder.tablereader import TableReaderFactory
from ontobuilder import OWLOntologyBuilder
from ontobuilder.owlontologybuilder import TermDescriptionError


# Set the format for logging output.
logging.basicConfig(format='\n%(levelname)s: %(message)s\n')

# Define and process the command-line arguments.
argp = ArgumentParser(description='Compiles an OWL ontology from a base \
ontology file and one or more term description tables from source files.')
argp.add_argument('-b', '--base_ontology', type=str, required=True, help='An \
OWL ontology file to use as a base for compiling the final ontology.')
argp.add_argument('-n', '--no_def_expand', action='store_true', help='If this \
flag is given, no attempt will be made to modify definition strings by adding \
the IDs of term labels referenced in the definitions.')
argp.add_argument('-i', '--id', type=str, required=False, default='',
    help='An IRI to use as the ID for the compiled ontology.')
argp.add_argument('-o', '--output', type=str, required=True, help='A path to \
use for the compiled ontology file.')
argp.add_argument('termsfiles', type=str, nargs='*', help='One or more files \
that contain tables defining the new ontology terms.')
args = argp.parse_args()

# Verify that the base ontology file exists.
if not(os.path.isfile(args.base_ontology)):
    raise RuntimeError(
        'The source ontology could not be found: ' + args.base_ontology + '.'
    )

# Verify that the terms files exist.
for termsfile in args.termsfiles:
    if not(os.path.isfile(termsfile)):
        raise RuntimeError(
            'The input file could not be found: ' + termsfile + '.'
        )

ontbuilder = OWLOntologyBuilder(args.base_ontology)

# Required columns.
REQUIRED_COLS = ('Type', 'ID')
# Optional columns.
OPTIONAL_COLS = ('Comments', 'Parent', 'Subclass of', 'Equivalent to')

# Process each source file.  In this step, entities and label annotations are
# defined, but processing of all other axioms (e.g., text definitions,
# comments, equivalency axioms, subclass of axioms, etc.) is deferred until
# after all input files have been read.  This allows forward referencing of
# labels and term IRIs and means that entity descriptions and source files can
# be processed in any arbitrary order.
for termsfile in args.termsfiles:
    with TableReaderFactory(termsfile) as reader:
        print 'Parsing ' + termsfile + '...'
        for table in reader:
            table.setRequiredColumns(REQUIRED_COLS)
            table.setOptionalColumns(OPTIONAL_COLS)

            for t_row in table:
                if not(t_row['Ignore'].upper().startswith('Y')):
                    typestr = t_row['Type'].lower()
    
                    try:
                        if typestr == 'class':
                            ontbuilder.addClass(t_row)
                        elif typestr == 'dataproperty':
                            ontbuilder.addDataProperty(t_row)
                        elif typestr == 'objectproperty':
                            ontbuilder.addObjectProperty(t_row)
                        elif typestr == 'annotationproperty':
                            ontbuilder.addAnnotationProperty(t_row)
                        elif typestr == '':
                            raise TermDescriptionError(
                                'The entity type (e.g., "class", "data property") was not specified.',
                                t_row
                            )
                        else:
                            raise TermDescriptionError(
                                'The entity type "' + t_row['Type']
                                + '" is not supported.', t_row
                            )
                    except TermDescriptionError as err:
                        print '\n', err , '\n'
                        sys.exit(1)

# Define all deferred axioms from the source entity descriptions.
print 'Defining all remaining entity axioms...'
try:
    ontbuilder.processDeferredEntityAxioms(not(args.no_def_expand))
except TermDescriptionError as err:
    print '\n', err , '\n'
    sys.exit(1)

# Set the ontology ID, if a new ID was provided.
newid = args.id.strip()
if newid != '':
    ontbuilder.getOntology().setOntologyID(newid)

# Write the ontology to the output file.
print 'Writing compiled ontology to ' + args.output + '...'
ontbuilder.getOntology().saveOntology(args.output)

