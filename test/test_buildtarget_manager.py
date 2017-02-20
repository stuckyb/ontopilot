# Copyright (C) 2016 Brian J. Stucky
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
from ontobuilder.buildtarget_manager import BuildTargetManager
from test_buildtarget import Target1, Target2
import unittest

# Java imports.


class ArgVals:
    """
    A simple "struct" for defining argument values.
    """
    pass


class TestBuildTargetManager(unittest.TestCase):
    """
    Tests the BuildTargetManager class.
    """
    def setUp(self):
        pass

    def test_getMatchingTargets(self):
        btr = BuildTargetManager()
        args = ArgVals()

        # No build target mappings defined.
        targets = btr._getMatchingTargets('target1', args)
        self.assertEqual([], targets)

        # Define one build target mapping.
        btr.addBuildTarget(Target1, 'target1')

        # Test a non-matching request.
        targets = btr._getMatchingTargets('target2', args)
        self.assertEqual([], targets)

        # Test a matching request.
        targets = btr._getMatchingTargets('target1', args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target1', targets[0].name)

        # Test a partial matching request.
        targets = btr._getMatchingTargets('targ', args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target1', targets[0].name)

        # Define two unambiguous build target mappings.
        btr.addBuildTarget(Target2, 'target2')

        # Test a non-matching request.
        targets = btr._getMatchingTargets('target3', args)
        self.assertEqual([], targets)

        # Test a matching request.
        targets = btr._getMatchingTargets('target2', args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target2', targets[0].name)

        # Test a partial matching request.
        targets = btr._getMatchingTargets('targ', args)
        self.assertEqual(2, len(targets))

        # Define a build target that cannot be disambiguated, with no extra
        # argments defined.
        btr.addBuildTarget(Target2, 'target2')

        # Test a matching request.
        targets = btr._getMatchingTargets('target2', args)
        tnames = [tmapping.name for tmapping in targets]
        self.assertEqual(['target2', 'target2'], tnames)

        # Test a partial matching request.
        targets = btr._getMatchingTargets('targ', args)
        self.assertEqual(3, len(targets))

        # Define build targets with differing numbers of arguments.
        btr.addBuildTarget(Target1, 'target1', arg1=1)
        btr.addBuildTarget(Target1, 'target1', arg1=1, arg2=2, arg3=3)
        btr.addBuildTarget(Target1, 'target1', arg1=1, arg2=2)
        btr.addBuildTarget(Target1, 'target1', arg4=4)

        # Test an unambiguous case with no arguments.
        targets = btr._getMatchingTargets('target1', args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target1', targets[0].name)
        self.assertEqual(0, len(targets[0].argvals))

        # Test two cases with one argument that matches only one target mapping
        # with arguments.
        args.arg1 = 1
        targets = btr._getMatchingTargets('target1', args)
        self.assertEqual(2, len(targets))
        self.assertEqual('target1', targets[0].name)
        self.assertEqual(1, len(targets[0].argvals))
        self.assertEqual(1, targets[0].argvals['arg1'])
        args = ArgVals()
        args.arg4 = 4
        targets = btr._getMatchingTargets('target1', args)
        self.assertEqual(2, len(targets))
        self.assertEqual('target1', targets[0].name)
        self.assertEqual(1, len(targets[0].argvals))
        self.assertEqual(4, targets[0].argvals['arg4'])

        # Test a case that matches multiple target mappings with arguments.
        args = ArgVals()
        args.arg1 = 1
        args.arg2 = 2
        args.arg3 = 3
        targets = btr._getMatchingTargets('target1', args)
        self.assertEqual(4, len(targets))
        tnames = [tmapping.name for tmapping in targets]
        self.assertEqual(['target1'] * 4, tnames)
        targnums = [len(tmapping.argvals) for tmapping in targets]
        self.assertEqual([3, 2, 1, 0], targnums)

    def test_getBuildTarget(self):
        btr = BuildTargetManager()
        args = ArgVals()
        Target1.run_cnt = Target2.run_cnt = 0

        # Define the build targets.
        btr.addBuildTarget(Target1, 'target1')
        btr.addBuildTarget(Target2, 'target1', arg1=1, arg2=2)

        # Verify that the correct target is run for both target mappings.
        btr.getBuildTarget('target1', args).run()
        self.assertEqual(1, Target1.run_cnt)
        self.assertEqual(0, Target2.run_cnt)
        args.arg1 = 1
        args.arg2 = 2
        btr.getBuildTarget('target1', args).run()
        self.assertEqual(1, Target1.run_cnt)
        self.assertEqual(1, Target2.run_cnt)

        # Define an additional target mapping.
        btr.addBuildTarget(Target1, 'target2')

        # Test an unambiguous partial target name.
        btr.getBuildTarget('targ', args).run()
        self.assertEqual(1, Target1.run_cnt)
        self.assertEqual(2, Target2.run_cnt)

        # Test an ambiguous match.
        args = ArgVals()
        with self.assertRaisesRegexp(
            RuntimeError, "matched more than one build target"
        ):
            btr.getBuildTarget('target', args)

        # Test an invalid target.
        with self.assertRaisesRegexp(
            RuntimeError, "Unknown build target"
        ):
            btr.getBuildTarget('target4', args)

