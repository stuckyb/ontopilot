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
import os
from ontopilot.buildtarget import BuildTarget, BuildTargetWithConfig
import unittest

# Java imports.


# Expected test results.
TARGET1_PRODUCTS = {
    'product 1': 'something'
}
COMBINED_PRODUCTS =  {
    'product 1': 'something',
    'product 2': 'something else'
}

# Define two dummy concrete build targets to test the build functionality.  One
# of these, Target1, allows manipulating the value of _isBuildRequired().
class Target1(BuildTarget):
    run_cnt = 0
    build_products = TARGET1_PRODUCTS
    def __init__(self, args=None):
        BuildTarget.__init__(self)
        self.build_required = True
    def _isBuildRequired(self):
        return self.build_required
    def _run(self):
        self.run_cnt += 1
        return self.build_products

class Target2(BuildTarget):
    run_cnt = 0
    def __init__(self, args=None):
        BuildTarget.__init__(self)
    def _isBuildRequired(self):
        return True
    def _run(self):
        self.run_cnt += 1
        return {'product 2': 'something else'}


class TestBuildTarget(unittest.TestCase):
    """
    Tests the BuildTarget base class.
    """
    def setUp(self):
        pass

    def test_isBuildRequired(self):
        # Test single targets with no dependencies, one that requires a build
        # and one that does not.
        target1 = Target1()
        target1.build_required = False
        self.assertFalse(target1.isBuildRequired())
        target2 = Target2()
        self.assertTrue(target2.isBuildRequired())

        # Test a target that does not explicitly require a build, but with a
        # dependency that does.
        target1.addDependency(target2)
        self.assertTrue(target1.isBuildRequired())

        # Test a target that does require a build, but with a dependency that
        # does not.
        target1 = Target1()
        target1.build_required = False
        target2.addDependency(target1)
        self.assertTrue(target2.isBuildRequired())

        # Test a target that does not require a build, and with a dependency
        # that also does not.
        target2 = Target1()
        target2.build_required = False
        target1.addDependency(target2)
        self.assertFalse(target1.isBuildRequired())

    def test_getSourceDirectory(self):
        """
        Note that this method does not test the JAR/temporary directory
        functionality.
        """
        target = Target1()

        testdir = os.path.dirname(os.path.realpath(__file__))

        if '.jar' not in testdir:
            root_srcdir = os.path.abspath(os.path.join(testdir, '../..'))

            with target.getSourceDirectory('') as sourcedir:
                self.assertEqual(root_srcdir, sourcedir)

            with target.getSourceDirectory('web') as sourcedir:
                self.assertEqual(root_srcdir + '/web', sourcedir)

            with target.getSourceDirectory('web/') as sourcedir:
                self.assertEqual(root_srcdir + '/web', sourcedir)

    def test_run(self):
        # Test a single target with no dependencies.
        target1 = Target1()
        result = target1.run()
        self.assertEqual(TARGET1_PRODUCTS, result)

        # Test a single target with a dependency.
        target2 = Target2()
        target1.addDependency(target2)
        result = target1.run()
        self.assertEqual(COMBINED_PRODUCTS, result)

        # Test dependencies with conflicting build products.
        target2_2 = Target2()
        target1.addDependency(target2_2)
        with self.assertRaisesRegexp(
            RuntimeError, 'Unable to merge product returned from build target'
        ):
            target1.run()

        # Test a dependency with a build product that conflicts with the
        # dependent's build products.
        target1 = Target1()
        target2 = Target1()
        target1.addDependency(target2)
        with self.assertRaisesRegexp(
            RuntimeError,
            "key that duplicates one of its dependency's product name keys"
        ):
            target1.run()

        # Test that forcing a build works as expected.
        target1 = Target1()
        target1.build_required = False
        target1.build_products = {}
        target2 = Target1()
        target2.build_required = False
        target2.build_products = {}
        target1.addDependency(target2)

        target1.run()
        self.assertEqual(0, target1.run_cnt)
        self.assertEqual(0, target2.run_cnt)

        target1.run(force_build=True)
        self.assertEqual(1, target1.run_cnt)
        self.assertEqual(1, target2.run_cnt)


# Define a dummy concrete build targets to test TestBuildTargetWithConfig.
class Target1Config(BuildTargetWithConfig):
    def __init__(self, args, cfgfile_required=True):
        BuildTargetWithConfig.__init__(self, args, cfgfile_required)
    def _isBuildRequired(self):
        return True
    def _run(self):
        return {}

class ArgVals:
    config_file = ''


class TestBuildTargetWithConfig(unittest.TestCase):
    """
    Tests the BuildTargetWithConfig base class.
    """
    def setUp(self):
        pass

    def test_init(self):
        argvals = ArgVals()

        # Test instantiating without requiring a config file and without
        # providing a config file.
        argvals.config_file = ''
        target = Target1Config(argvals, False)
        self.assertIsNone(target.config.getConfigFilePath())

        # Test instantiating without requiring a config file and providing a
        # config file.
        argvals.config_file = 'test_data/project.conf'
        target = Target1Config(argvals, False)
        self.assertIsNotNone(target.config.getConfigFilePath())

        # Test instantiating requiring a config file and without providing a
        # config file.
        argvals.config_file = ''
        with self.assertRaisesRegexp(
            RuntimeError, 'Unable to load the project configuration file.'
        ):
            Target1Config(argvals, True)

        # Test instantiating when both requiring and providing a config file.
        argvals.config_file = 'test_data/project.conf'
        target = Target1Config(argvals, True)
        self.assertIsNotNone(target.config.getConfigFilePath())

