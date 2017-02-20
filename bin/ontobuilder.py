#!/usr/bin/env jython

# Python imports.
import sys
import logging
from argparse import ArgumentParser
from ontobuilder import OntoConfig, ConfigError
from ontobuilder.basic_buildtargets import InitTarget
from ontobuilder.imports_buildtarget import ImportsBuildTarget
from ontobuilder.onto_buildtarget import OntoBuildTarget
from ontobuilder.modified_onto_buildtarget import ModifiedOntoBuildTarget
from ontobuilder.errorcheck_buildtarget import ErrorCheckBuildTarget
from ontobuilder.buildrunner import BuildRunner


# Set the format for logging output.
logging.basicConfig(format='\n%(levelname)s: %(message)s\n')

# Define and process the command-line arguments.
argp = ArgumentParser(description='Builds an OWL ontology or ontology import \
modules using information from table-based source files.')
argp.add_argument('-c', '--config_file', type=str, required=False,
    default='ontology.conf', help='The path to a configuration file for the \
ontology build process.')
argp.add_argument('-n', '--no_def_expand', action='store_true', help='If this \
flag is given, no attempt will be made to modify definition strings by adding \
the IDs of term labels referenced in the definitions.')
argp.add_argument('-m', '--merge_imports', action='store_true', help='If this \
flag is given, imported terms will be merged with the main ontology into a \
new ontology document.')
argp.add_argument('-r', '--reason', action='store_true', help='If this \
flag is given, a reasoner will be run on the ontology (ELK by default), and \
inferred axioms will be added to a new ontology document.')
argp.add_argument('task', type=str, nargs='?', default='ontology', help='The \
build task to run.  Must be either "init", "imports", "ontology", or \
"errorcheck".')
argp.add_argument('taskargs', type=str, nargs='*', help='Additional arguments \
for the specified build task.')
args = argp.parse_args()

buildrunner = BuildRunner()
buildrunner.addBuildTarget(InitTarget, 'init')
buildrunner.addBuildTarget(OntoBuildTarget, 'ontology', merge_imports=False, reason=False)
buildrunner.addBuildTarget(ModifiedOntoBuildTarget, 'ontology')

# Get the specified build target.
if args.task == 'init':
    target = InitTarget(args)
else:
    if args.task == 'ontology':
        if args.merge_imports or args.reason:
            target = ModifiedOntoBuildTarget(args, None)
        else:
            target = OntoBuildTarget(args, None)

    elif args.task == 'errorcheck':
        target = ErrorCheckBuildTarget(args, None)

    elif args.task == 'imports':
        target = ImportsBuildTarget(args, None)

    else:
        print '\nUnrecognized build task: {0}.\n'.format(args.task)
        sys.exit(1)

# Run the build target.
try:
    if target.isBuildRequired():
        target.run()
    else:
        print '\n', target.getBuildNotRequiredMsg(), '\n'
except RuntimeError as err:
    print '\n', err, '\n'
    sys.exit(1)

