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


# Implements two relatively simple build targets: InitTarget and
# BuildDirTarget.
#

# Python imports.
import sys, os, shutil
from zipfile import ZipFile
import tempfile
from contextlib import contextmanager
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

    @contextmanager
    def _getManagedTmpDir(self):
        """
        Implements a context manager that creates a temporary directory and
        ensures the directory and its contents are deleted upon context exit.
        Returns the path to the temporary directory.
        """
        tmpdir = tempfile.mkdtemp()
        try:
            yield tmpdir
        finally:
            shutil.rmtree(tmpdir)

    def _run(self):
        """
        Attempts to create a new ontology project.
        """
        if self.args.taskarg == '':
            raise RuntimeError(
                'Please provide the name of the ontology file for the new '
                'project.  For example:\n$ {0} init test.owl'.format(
                    os.path.basename(sys.argv[0])
                )
            )
    
        script_path = os.path.abspath(os.path.realpath(__file__))
        if ('.jar/Lib' in script_path) or ('.jar\\Lib' in script_path):
            # We're running from a JAR file, so we need to extract the template
            # files to a temporary location.
            jar_path = script_path.rpartition('.jar')[0] + '.jar'
            zip_ref = ZipFile(jar_path)

            # Extract the template files into a temporary directory.
            with self._getManagedTmpDir() as tmpdir:
                for filepath in zip_ref.namelist():
                    if filepath.startswith('template_files/'):
                        zip_ref.extract(filepath, tmpdir)

                templatedir = os.path.join(tmpdir, 'template_files')
                projc = ProjectCreator('.', self.args.taskarg, templatedir)
                projc.createProject()
        else:
            # We're not running from a JAR file, so we can directly access the
            # template files from the installation location.
            templatedir = os.path.join(
                os.path.dirname(script_path), '../../template_files'
            )
            projc = ProjectCreator('.', self.args.taskarg, templatedir)
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

        bad_dirpath_msg = (
            'A file with the same name as the build folder, "{0}", already '
            'exists.  Use the "builddir" option in the configuration file to '
            'specify a different build folder path, or rename the conflicting '
            'file.'
        )
        bad_dirperms_msg = (
            'The project build directory, "{0}", could not be created.  '
            'Please make sure that you have permission to create new files '
            'and directories in the project location.'
        )

        self._makeDirs(builddir, bad_dirpath_msg, bad_dirperms_msg)

        return {}

