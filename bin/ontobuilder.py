#!/usr/bin/env jython

# Python imports.
import os
import sys
import logging
from argparse import ArgumentParser
from ontobuilder import OntoConfig, OntoBuildManager
from ontobuilder import ConfigError, TermDescriptionError


# Set the format for logging output.
logging.basicConfig(format='\n%(levelname)s: %(message)s\n')

# Define and process the command-line arguments.
argp = ArgumentParser(description='Builds an OWL ontology or ontology import \
modules using information from table-based source files.')
argp.add_argument('-c', '--config_file', type=str, required=False,
    default='ontology.conf', help='The path to a configuration file for the \
ontology build process.')
argp.add_argument('-b', '--build_folder', type=str, required=False,
    default='build', help='The location of the build folder.')
argp.add_argument('-n', '--no_def_expand', action='store_true', help='If this \
flag is given, no attempt will be made to modify definition strings by adding \
the IDs of term labels referenced in the definitions.')
argp.add_argument('task', type=str, nargs='?', default='ontology',
    help='The build task to run.  Must be either "imports" or "ontology".')
args = argp.parse_args()

try:
    config = OntoConfig(args.config_file)
except ConfigError as err:
    print '\n', err , '\n'
    print 'Please make sure the configuration file exists and that the path is correct.  Use the "-c" (or "--config_file") option to specify a different configuration file or path.\n'
    sys.exit(1)

# Check if the build directory exists; if not, attempt to create it.
if not(os.path.isdir(args.build_folder)):
    if os.path.exists(args.build_folder):
        print '\nA file with the same name as the build folder, {0}, already exists.  Use the "-b" (or "--build_folder") option to specify a different build folder path, or rename the conflicting file.\n'.format(args.build_folder)
        sys.exit(1)
    else:
        os.mkdir(args.build_folder)

# Run the specified build task.
if args.task == 'ontology':
    buildman = OntoBuildManager(config, args.build_folder, not(args.no_def_expand))

    if buildman.isBuildNeeded():
        try:
            buildman.build()
        except TermDescriptionError as err:
            print '\n', err , '\n'
            sys.exit(1)
    else:
        print '\nThe compiled ontology is already up to date.\n'

