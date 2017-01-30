#!/usr/bin/env jython

# Python imports.
import os
import sys
import logging
from argparse import ArgumentParser
from ontobuilder import OntoConfig, ConfigError
from ontobuilder import OntoBuildManager, TermDescriptionError
from ontobuilder import ImportsBuildManager
from ontobuilder import ColumnNameError, ImportModSpecError
from ontobuilder import ProjectCreator


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
argp.add_argument('task', type=str, nargs='?', default='ontology', help='The \
build task to run.  Must be either "init", "imports", or "ontology".')
argp.add_argument('taskargs', type=str, nargs='*', help='Additional arguments \
for the specified build task.')
args = argp.parse_args()

# Run the specified build task.
if args.task == 'init':
    if len(args.taskargs) == 0:
        print '\nPlease provide the name of the ontology file for the new project.  For example:\n$ {0} init test.owl\n\n'.format(os.path.basename(sys.argv[0]))
        sys.exit(1)
    elif len(args.taskargs) > 1:
        print '\nToo many arguments for the "init" task.  Please provide only the name of the ontology file for the new project.  For example:\n$ {0} init test.owl\n\n'.format(os.path.basename(sys.argv[0]))
        sys.exit(1)

    # Get the path to the project template files directory.
    templatedir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '../template_files'
    )

    projc = ProjectCreator('.', args.taskargs[0], templatedir)
    try:
        projc.createProject()
    except RuntimeError as err:
        print '\n', err , '\n'
        sys.exit(1)
else:
    # All other build tasks require a configuration file, so attempt to
    # instantiate an OntoConfig object.
    try:
        config = OntoConfig(args.config_file)
    except ConfigError as err:
        print '\n', err , '\n'
        print 'Please make sure the configuration file exists and that the path is correct.  Use the "-c" (or "--config_file") option to specify a different configuration file or path.\n'
        sys.exit(1)

    # Check if the build directory exists; if not, attempt to create it.
    builddir = config.getBuildDir()
    if not(os.path.isdir(builddir)):
        if os.path.exists(builddir):
            print '\nA file with the same name as the build folder, {0}, already exists.  Use the "builddir" option in the configuration file to specify a different build folder path, or rename the conflicting file.\n'.format(builddir)
            sys.exit(1)
        else:
            os.mkdir(builddir)

    if args.task == 'ontology':
        buildman = OntoBuildManager(config, not(args.no_def_expand))
    
        if buildman.isBuildNeeded():
            try:
                buildman.build()
            except (TermDescriptionError, RuntimeError) as err:
                print '\n', err , '\n'
                sys.exit(1)
        else:
            print '\nThe compiled ontology is already up to date.\n'
    elif args.task == 'imports':
        buildman = ImportsBuildManager(config)
    
        try:
            buildman.build()
        except (ColumnNameError, ImportModSpecError, RuntimeError) as err:
            print '\n', err , '\n'
            sys.exit(1)
    else:
        print '\nUnrecognized build task: {0}.\n'.format(args.task)
        sys.exit(1)

