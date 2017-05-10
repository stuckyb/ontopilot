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
import unittest
import os.path, shutil
import subprocess
from collections import namedtuple
import tempfile
from ontopilot.ontoconfig import OntoConfig
from ontopilot.onto_buildtarget import OntoBuildTarget

# Java imports.
from java.lang import System as JavaSystem


# Define a simple "struct" type for simulating command-line arguments.
ArgsType = namedtuple('args', 'no_def_expand')


class TestBuildTargetsFunctional(unittest.TestCase):
    """
    Implements functional/integration tests for each of OntoPilot's main build
    targets.  These tests do not attempt to provide complete coverage or test
    every possible edge case, but they do verify that the OntoPilot executable
    and all of the main build processes work from start to finish and produce
    the expected results.
    """
    def setUp(self):
        # Get the path to the ontopilot executable.  This depends on whether
        # we're running on *nix or Windows, and we can't use the usual methods
        # (os.name, sys.platform) to figure this out because they report "java"
        # or something similar.
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        if JavaSystem.getProperty('os.name').startswith('Windows'):
            self.execpath = os.path.realpath(
                os.path.join(scriptdir, '..', '..', 'bin', 'ontopilot.bat')
            )
        else:
            self.execpath = os.path.realpath(
                os.path.join(scriptdir, '..', '..', 'bin', 'ontopilot')
            )

        self.tmpdir = tempfile.mkdtemp()
        print self.tmpdir

    def tearDown(self):
        if self.tmpdir is not None:
            shutil.rmtree(self.tmpdir)

    def test_init(self):
        # Run the init build task.  For now, just make sure that it runs
        # without error and check for the output files and directories located
        # at the project root.
        args = [self.execpath, 'init', 'test.owl']
        retval = subprocess.call(args, cwd=self.tmpdir)
        self.assertEqual(0, retval)

        self.assertTrue(
            os.path.isfile(os.path.join(self.tmpdir, 'project.conf'))
        )
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, 'imports')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, 'ontology')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmpdir, 'src')))

