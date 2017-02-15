
#
# Provides high-level management of the imports and ontology build process by
# implementing discrete build targets.  Each target is a class that follows a
# simple interface, and targets can be linked together in dependency
# relationships.
#

# Python imports.
import sys, os
import glob
from tablereaderfactory import TableReaderFactory
from owlontologybuilder import OWLOntologyBuilder, TermDescriptionError
from ontobuilder import TRUE_STRS
from imports_buildmanager import ImportsBuildManager
from inferred_axiom_adder import InferredAxiomAdder
from projectcreator import ProjectCreator
from imports_buildmanager import ImportsBuildManager

# Java imports.
from org.semanticweb.owlapi.model import IRI


# Required columns in terms files.
REQUIRED_COLS = ('Type', 'ID')

# Optional columns in terms files.
OPTIONAL_COLS = (
    'Comments', 'Parent', 'Subclass of', 'Equivalent to', 'Disjoint with',
    'Inverse', 'Characteristics', 'Ignore'
)
        

class BuildTarget:
    def __init__(self):
        self.dependencies = []

    def addDependency(self, target):
        """
        Adds a dependency for this build target.
        """
        self.dependencies.append(target)

    def run(self):
        """
        Runs this build task.  All dependencies are processed first.  If the
        build task fails, an appropriate exception should be thrown, and
        exceptions should be allowed to "bubble up" through the dependency
        chain so they can be properly handled by external client code.  This
        method will almost always need to be extended by subclasses.
        """
        for dependency in self.dependencies:
            dependency.run()


class InitTarget(BuildTarget):
    """
    A build target that initializes a new ontology project.
    """
    def __init__(self, args):
        """
        args: Parsed command-line arguments
        """
        BuildTarget.__init__(self)

        self.args = args

    def run(self):
        """
        Checks whether the build directory exists, and if not, attempts to
        create it.
        """
        # Run any dependencies by calling the superclass implementation.
        BuildTarget.run(self)

        if len(self.args.taskargs) == 0:
            raise RuntimeError(
                'Please provide the name of the ontology file for the new \
project.  For example:\n$ {0} init test.owl'.format(os.path.basename(sys.argv[0]))
            )
        elif len(self.args.taskargs) > 1:
            raise RuntimeError(
                'Too many arguments for the "init" task.  Please provide only \
the name of the ontology file for the new project.  For example:\n$ {0} init \
test.owl'.format(os.path.basename(sys.argv[0]))
            )
    
        # Get the path to the project template files directory.
        templatedir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '../../template_files'
        )
    
        projc = ProjectCreator('.', self.args.taskargs[0], templatedir)
        projc.createProject()


class BuildDirTarget(BuildTarget):
    """
    A simple build target that ensures other build targets have a suitable
    build directory.
    """
    def __init__(self, config):
        """
        config: An OntoConfig instance.
        """
        BuildTarget.__init__(self)

        self.config = config

    def run(self):
        """
        Checks whether the build directory exists, and if not, attempts to
        create it.
        """
        # Run any dependencies by calling the superclass implementation.
        BuildTarget.run(self)

        builddir = self.config.getBuildDir()

        if not(os.path.isdir(builddir)):
            if os.path.exists(builddir):
                raise RuntimeError('A file with the same name as the build \
folder, {0}, already exists.  Use the "builddir" option in the configuration \
file to specify a different build folder path, or rename the conflicting \
file.'.format(builddir))
            else:
                try:
                    os.mkdir(builddir)
                except OSError:
                    raise RuntimeError('The project build directory, "{0}", \
could not be created.  Please make sure that you have permission to create \
new files and directories in the project location.'.format(builddir))


class ImportsTarget(BuildTarget):
    """
    A build target for compiling the imports modules.
    """
    def __init__(self, config):
        """
        config: An OntoConfig instance.
        """
        BuildTarget.__init__(self)

        self.config = config
        self.addDependency(BuildDirTarget(self.config))

    def run(self):
        """
        Compiles the imports modules.
        """
        # Run any dependencies by calling the superclass implementation.
        BuildTarget.run(self)

        buildman = ImportsBuildManager(self.config)
    
        try:
            buildman.build()
        except (ColumnNameError, ImportModSpecError, RuntimeError) as err:
            print '\n', err , '\n'
            sys.exit(1)

