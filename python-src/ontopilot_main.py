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
from __future__ import unicode_literals
import sys
import logging
from argparse import ArgumentParser
import ontopilot
from ontopilot import ConfigError
from ontopilot import InitTarget
from ontopilot import ImportsBuildTarget
from ontopilot import OntoBuildTarget, ModifiedOntoBuildTarget
from ontopilot import ReleaseBuildTarget, DocsBuildTarget
from ontopilot import ErrorCheckBuildTarget
from ontopilot import UpdateBaseImportsBuildTarget
from ontopilot import InferencePipelineBuildTarget
from ontopilot import FindEntitiesBuildTarget
from ontopilot import BuildTargetManager

# Java imports.


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
buildtm.addBuildTarget(DocsBuildTarget, task='make', taskarg='documentation')
buildtm.addBuildTarget(UpdateBaseImportsBuildTarget, task='update_base')
buildtm.addBuildTarget(UpdateBaseImportsBuildTarget, task='updatebase')
buildtm.addBuildTarget(ErrorCheckBuildTarget, task='error_check')
buildtm.addBuildTarget(ErrorCheckBuildTarget, task='errorcheck')
buildtm.addBuildTarget(InferencePipelineBuildTarget, task='inference_pipeline')
buildtm.addBuildTarget(InferencePipelineBuildTarget, task='inferencepipeline')
buildtm.addBuildTarget(InferencePipelineBuildTarget, task='ipl')
buildtm.addBuildTarget(FindEntitiesBuildTarget, task='find_entities')
buildtm.addBuildTarget(FindEntitiesBuildTarget, task='findentities')
buildtm.addBuildTarget(FindEntitiesBuildTarget, task='fe')

# Define the command-line arguments.
argp = ArgumentParser(
    prog='ontopilot',
    description='Software for ontology development and deployment.'
)
argp.add_argument(
    '-c', '--config_file', type=str, required=False, default='',
    help='The path to a configuration file for the ontology build process.'
)
argp.add_argument(
    '-q', '--quiet', action='store_true', required=False, help='If this flag '
    'is given, all usual console status messages will be suppressed except for '
    'error messages.'
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
    '-i', '--input_data', type=str, required=False, default='', help='The '
    'path to a source ontology/data set to use when running in inference '
    'pipeline mode, or a file of search terms when running in entity finding '
    'mode.  If no source path is provided, the input will be read from '
    'standard in.'
)
argp.add_argument(
    '-o', '--fileout', type=str, required=False, default='', help='The path '
    'to an output file to use when running in inference pipeline mode or '
    'entity finding mode.  If no output path is provided, results will be '
    'written to standard out.'
)
argp.add_argument(
    '-s', '--search_ont', type=str, required=False, default=[],
    action='append', help='The path to a source ontology file to search when '
    'running in entity finding mode.  This option can be repeated to specify '
    'multiple search ontologies.'
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

if args.quiet:
    ontopilot.setLogLevel(logging.ERROR)

# Get and run the appropriate build target.
try:
    target = buildtm.getBuildTarget(args, targetname_arg='task')
    if target.isBuildRequired() or args.force:
        target.run(args.force)
        sys.exit(0)
    else:
        print '\n', target.getBuildNotRequiredMsg(), '\n'
        sys.exit(0)
except (ConfigError, RuntimeError) as err:
    print '\n', unicode(err), '\n'
    sys.exit(1)

