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
from ontobuilder.release_buildtarget import ReleaseBuildTarget
from ontobuilder.errorcheck_buildtarget import ErrorCheckBuildTarget
from ontobuilder.update_base_imports_buildtarget import UpdateBaseImportsBuildTarget
from ontobuilder.buildtarget_manager import BuildTargetManager


# Set the format for logging output.
logging.basicConfig(format='\n%(levelname)s: %(message)s\n')

# Define the build targets.
buildtm = BuildTargetManager()
buildtm.addBuildTarget(InitTarget, task='initialize')
buildtm.addBuildTarget(ImportsBuildTarget, task='make', taskarg='imports')
buildtm.addBuildTarget(
    OntoBuildTarget, task='make', taskarg='ontology', merge_imports=False,
    reason=False
)
buildtm.addBuildTarget(ModifiedOntoBuildTarget, task='make', taskarg='ontology')
buildtm.addBuildTarget(ReleaseBuildTarget, task='make', taskarg='release')
buildtm.addBuildTarget(UpdateBaseImportsBuildTarget, task='update_base')
buildtm.addBuildTarget(ErrorCheckBuildTarget, task='errorcheck')

# Define the command-line arguments.
argp = ArgumentParser(description='Manages an OWL ontology project.')
argp.add_argument(
    '-c', '--config_file', type=str, required=False, default='ontology.conf',
    help='The path to a configuration file for the ontology build process.'
)
argp.add_argument(
    '-m', '--merge_imports', action='store_true', help='If this flag is '
    'given, imported ontologies will be merged with the main ontology into a '
    'new ontology document.'
)
argp.add_argument(
    '-r', '--reason', action='store_true', help='If this flag is given, a '
    'reasoner will be run on the ontology (ELK by default), and inferred '
    'axioms will be added to a new ontology document.'
)
argp.add_argument(
    '-d', '--release_date', type=str, required=False, default='', help='Sets '
    'a custom date for a release build.  The date must be in the format '
    'YYYY-MM-DD.'
)
argp.add_argument(
    'task', type=str, nargs='?', default='ontology', help='The build task to '
    'run.  Must be one of {0}.'.format(
        buildtm.getBuildTargetNamesStr('task')
    )
)
argp.add_argument(
    'taskarg', type=str, nargs='?', default='', help='Additional argument for '
    'the specified build task.  For the build task "make", this should be '
    'either {0}.  For the build task "initialize", this should be the name of '
    'an OWL file for a new ontology project.'.format(
        buildtm.getBuildTargetNamesStr('taskarg', task='make')
    )
)

args = argp.parse_args()

# Get and run the appropriate build target.
try:
    target = buildtm.getBuildTarget(args, targetname_arg='task')
    if target.isBuildRequired():
        target.run()
    else:
        print '\n', target.getBuildNotRequiredMsg(), '\n'
        sys.exit(1)
except RuntimeError as err:
    print '\n', err, '\n'
    sys.exit(1)

