#
# Implements two relatively simple build targets: InitTarget and
# BuildDirTarget.
#

# Python imports.
import sys, os
from buildtarget import BuildTarget, BuildTargetWithConfig
from projectcreator import ProjectCreator

# Java imports.


class InitTarget(BuildTarget):
    """
    A build target that initializes a new ontology project.
    """
    def __init__(self, args):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The only supported member is 'taskargs',
            which must provide the name of the new ontology file.
        """
        BuildTarget.__init__(self)

        self.args = args

    def _isBuildRequired(self):
        """
        This always returns True, because if the user is requesting that a new
        project be created, we should try to do so.
        """
        return True

    def _run(self):
        """
        Attempts to create a new ontology project.
        """
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

        return {}


class BuildDirTarget(BuildTargetWithConfig):
    """
    A simple build target that ensures other build targets have a suitable
    build directory.
    """
    def __init__(self, args, config=None):
        """
        args: A "struct" of configuration options (typically, parsed
            command-line arguments).  The only required member is 'config_file'
            (string).
        config (optional): An OntoConfig instance.
        """
        BuildTargetWithConfig.__init__(self, args, config)

    def _isBuildRequired(self):
        """
        Return False if the build directory already exists.
        """
        builddir = self.config.getBuildDir()

        return not(os.path.isdir(builddir))

    def _run(self):
        """
        If the build directory does not exist, attempts to create it.
        """
        builddir = self.config.getBuildDir()

        if self._isBuildRequired():
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

        return {}

