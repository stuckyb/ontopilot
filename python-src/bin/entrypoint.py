#!/usr/bin/env jython

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
import sys
import logging
from argparse import ArgumentParser
from ontopilot import ConfigError
from ontopilot import InitTarget, ImportsBuildTarget, OntoBuildTarget
from ontopilot import ModifiedOntoBuildTarget, ReleaseBuildTarget
from ontopilot import ErrorCheckBuildTarget, UpdateBaseImportsBuildTarget
from ontopilot import BuildTargetManager

# Java imports.


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
    '-c', '--config_file', type=str, required=False, default='project.conf',
    help='The path to a configuration file for the ontology build process.'
)
argp.add_argument(
    '-f', '--force', action='store_true', required=False, help='If this flag '
    'is given, the build task will be run even if the build products appear '
    'to be up to date.'
)
argp.add_argument(
    '-m', '--merge_imports', action='store_true', help='If this flag is '
    'given, imported ontologies will be merged with the main ontology into a '
    'new ontology document.'
)
argp.add_argument(
    '-r', '--reason', action='store_true', help='If this flag is given, a '
    'reasoner will be run on the ontology (HermiT by default), and inferred '
    'axioms will be added to a new ontology document.'
)
argp.add_argument(
    '-d', '--release_date', type=str, required=False, default='', help='Sets '
    'a custom date for a release build.  The date must be in the format '
    'YYYY-MM-DD.'
)
argp.add_argument(
    'task', type=str, nargs='?', default='make', help='The build task to '
    'run.  Must be one of {0}.'.format(
        buildtm.getBuildTargetNamesStr('task')
    )
)
argp.add_argument(
    'taskarg', type=str, nargs='?', default='ontology', help='Additional '
    'argument for the specified build task.  For the build task "make", this '
    'should be either {0}.  For the build task "initialize", this should be '
    'the name of an OWL file for a new ontology project.'.format(
        buildtm.getBuildTargetNamesStr('taskarg', task='make')
    )
)

args = argp.parse_args()

# Get and run the appropriate build target.
try:
    target = buildtm.getBuildTarget(args, targetname_arg='task')
    if target.isBuildRequired() or args.force:
        target.run(args.force)
    else:
        print '\n', target.getBuildNotRequiredMsg(), '\n'
        sys.exit(1)
except (ConfigError, RuntimeError) as err:
    print '\n', ConfigError, '\n'
    sys.exit(1)

