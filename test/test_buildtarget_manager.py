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
from ontopilot.buildtarget_manager import BuildTargetManager, TargetMap
from test_buildtarget import Target1, Target2
import unittest

# Java imports.


# Define additional build targets.
class Target3 (Target2):
    pass
class Target4 (Target2):
    pass


class ArgVals:
    """
    A simple "struct" for defining argument values.
    """
    def __init__(self, **argvals):
        for argname in argvals:
            setattr(self, argname, argvals[argname])


class TestBuildTargetManager(unittest.TestCase):
    """
    Tests the BuildTargetManager class.
    """
    def setUp(self):
        pass

    def test_generateNamesStr(self):
        btr = BuildTargetManager()

        self.assertEqual('', btr._generateNamesStr([]))
        self.assertEqual('"name1"', btr._generateNamesStr(['name1']))
        self.assertEqual(
            '"name1" or "name2"', btr._generateNamesStr(['name1', 'name2'])
        )
        self.assertEqual(
            '"name1", "name2", or "name3"',
            btr._generateNamesStr(['name1', 'name2', 'name3'])
        )

    def test_getSynonymousNamesStr(self):
        btr = BuildTargetManager()

        self.assertEqual('', btr._getSynonymousNamesStr([]))
        self.assertEqual('"name1"', btr._getSynonymousNamesStr(['name1']))
        self.assertEqual(
            '"name1" (also "name2")',
            btr._getSynonymousNamesStr(['name1', 'name2'])
        )
        self.assertEqual(
            '"name1" (also "name2" or "name3")',
            btr._getSynonymousNamesStr(['name1', 'name2', 'name3'])
        )
        self.assertEqual(
            '"name1" (also "name2", "name3", or "name4")',
            btr._getSynonymousNamesStr(['name1', 'name2', 'name3', 'name4'])
        )

    def test_getBuildTargetNamesStr(self):
        """
        This unit test also indirectly tests _getBuildTargetNames().
        """
        btr = BuildTargetManager()

        # 0 build targets.
        self.assertEqual('', btr.getBuildTargetNamesStr('task'))

        # 1 build target.  Add a duplicate to make sure the method only returns
        # unique task names.
        btr.addBuildTarget(Target1, task='target1')
        btr.addBuildTarget(Target1, task='target1')
        self.assertEqual('"target1"', btr.getBuildTargetNamesStr('task'))

        # 1 build target with two synonymous names.
        btr.addBuildTarget(Target1, task='target2')
        self.assertEqual(
            '"target1" (also "target2")', btr.getBuildTargetNamesStr('task')
        )

        # 1 build target with three synonymous names.
        btr.addBuildTarget(Target1, task='target3')
        self.assertEqual(
            '"target1" (also "target2" or "target3")',
            btr.getBuildTargetNamesStr('task')
        )

        # Now test cases where we have multiple build targets.
        btr = BuildTargetManager()

        # Two build targets.
        btr.addBuildTarget(Target1, task='target1')
        btr.addBuildTarget(Target2, task='target2')
        self.assertEqual(
            '"target1" or "target2"', btr.getBuildTargetNamesStr('task')
        )

        # Three build targets.
        btr.addBuildTarget(Target3, task='target3')
        self.assertEqual(
            '"target1", "target2", or "target3"',
            btr.getBuildTargetNamesStr('task')
        )

        # Now test a case where we have an argument value constraint.
        btr = BuildTargetManager()
        btr.addBuildTarget(Target1, task='target1', taskarg='val')
        btr.addBuildTarget(Target2, task='target1', taskarg='val1')
        btr.addBuildTarget(Target3, task='target1')
        btr.addBuildTarget(Target4, task='target2', taskarg='val2')
        # Check the result without the constraint.
        self.assertEqual(
            '"val", "val1", or "val2"', btr.getBuildTargetNamesStr('taskarg')
        )
        # Check the result with the constraint.
        self.assertEqual(
            '"val" or "val1"',
            btr.getBuildTargetNamesStr('taskarg', task='target1')
        )

    def test_getMatchingTargets(self):
        btr = BuildTargetManager()
        args = ArgVals()

        # No build target mappings defined.
        targets = btr._getMatchingTargets(args)
        self.assertEqual([], targets)

        # Define one build target mapping.
        btr.addBuildTarget(Target1, task='target1')

        # Test a non-matching request.
        args.task = 'target2'
        targets = btr._getMatchingTargets(args)
        self.assertEqual([], targets)

        # Test a matching request.
        args.task = 'target1'
        targets = btr._getMatchingTargets(args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target1', targets[0].argvals['task'])

        # Test an empty string.  This should obviously not match any targets.
        args.task = ''
        targets = btr._getMatchingTargets(args)
        self.assertEqual(0, len(targets))

        # Test a partial matching request.
        args.task = 'targ'
        targets = btr._getMatchingTargets(args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target1', targets[0].argvals['task'])

        # Define a second unambiguous build target mapping.
        btr.addBuildTarget(Target2, task='target2')

        # Test a non-matching request.
        args.task = 'target3'
        targets = btr._getMatchingTargets(args)
        self.assertEqual([], targets)

        # Test a matching request.
        args.task = 'target2'
        targets = btr._getMatchingTargets(args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target2', targets[0].argvals['task'])

        # Test a partial matching request.
        args.task = 'targ'
        targets = btr._getMatchingTargets(args)
        self.assertEqual(2, len(targets))

        # Define a build target that cannot be disambiguated, with no "extra"
        # argments defined.
        btr.addBuildTarget(Target2, task='target2')

        # Test a matching request.
        args.task = 'target2'
        targets = btr._getMatchingTargets(args)
        tnames = [tmapping.argvals['task'] for tmapping in targets]
        self.assertEqual(['target2', 'target2'], tnames)

        # Test a partial matching request.
        args.task = 'targ'
        targets = btr._getMatchingTargets(args)
        self.assertEqual(3, len(targets))

        # Define build targets with differing numbers of arguments.
        btr.addBuildTarget(Target1, task='target1', arg1=1)
        btr.addBuildTarget(Target1, task='target1', arg1=1, arg2=2, arg3=3)
        btr.addBuildTarget(Target1, task='target1', arg1=1, arg2=2)
        btr.addBuildTarget(Target1, task='target1', arg4=4)

        # Test an unambiguous case with no arguments.
        args.task = 'target1'
        targets = btr._getMatchingTargets(args)
        self.assertEqual(1, len(targets))
        self.assertEqual('target1', targets[0].argvals['task'])
        self.assertEqual(1, len(targets[0].argvals))

        # Test two cases with arguments that match only one target mapping with
        # "extra" arguments.
        args.arg1 = 1
        targets = btr._getMatchingTargets(args)
        self.assertEqual(2, len(targets))
        self.assertEqual('target1', targets[0].argvals['task'])
        self.assertEqual(2, len(targets[0].argvals))
        self.assertEqual(1, targets[0].argvals['arg1'])
        args = ArgVals(task='target1', arg4=4)
        targets = btr._getMatchingTargets(args)
        self.assertEqual(2, len(targets))
        self.assertEqual('target1', targets[0].argvals['task'])
        self.assertEqual(2, len(targets[0].argvals))
        self.assertEqual(4, targets[0].argvals['arg4'])

        # Test a case that matches multiple target mappings with arguments.
        args = ArgVals(task='target1', arg1=1, arg2=2, arg3=3)
        targets = btr._getMatchingTargets(args)
        self.assertEqual(4, len(targets))
        tnames = [tmapping.argvals['task'] for tmapping in targets]
        self.assertEqual(['target1'] * 4, tnames)
        targnums = [len(tmapping.argvals) for tmapping in targets]
        self.assertEqual([4, 3, 2, 1], targnums)

    def test_getAmbiguousTargetErrorMsg(self):
        btr = BuildTargetManager()
        matches = [
            TargetMap(tclass=Target1, argvals={'task': 'target1'}),
            TargetMap(tclass=Target1, argvals={'task': 'target2'})
        ]

        # Check the case with no task name argument.
        args = ArgVals(task='target1')
        msg = btr._getAmbiguousTargetErrorMsg(args, matches, '')
        self.assertTrue(
            msg.startswith(
                'The command-line arguments could not be unambiguously'
            )
        )

        # Check the case where the task name is ambiguous.
        msg = btr._getAmbiguousTargetErrorMsg(args, matches, 'task')
        self.assertTrue(
            'matched more than one build task name' in msg
        )

        # Check the case where the task name is unambiguous but the remaining
        # arguments lead to an ambiguous match.
        matches = [
            TargetMap(
                tclass=Target1, argvals={'task': 'target1', 'arg1': 'val1'}
            ),
            TargetMap(
                tclass=Target1, argvals={'task': 'target1', 'arg1': 'val2'}
            )
        ]
        msg = btr._getAmbiguousTargetErrorMsg(args, matches, 'task')
        self.assertTrue(
            msg.startswith(
                'The arguments for the build task "target1" could not be '
                'unambiguously matched to a single build operation.'
            )
        )

    def test_getBuildTarget(self):
        btr = BuildTargetManager()
        args = ArgVals()
        Target1.run_cnt = Target2.run_cnt = 0

        # Define the build targets.
        btr.addBuildTarget(Target1, task='target1')
        btr.addBuildTarget(Target2, task='target1', arg1=1, arg2=2)

        # Verify that the correct target is returned for both target mappings.
        args.task='target1'
        btarget = btr.getBuildTarget(args)
        self.assertTrue(isinstance(btarget, Target1))
        args.arg1 = 1
        args.arg2 = 2
        btarget = btr.getBuildTarget(args)
        self.assertTrue(isinstance(btarget, Target2))

        # Define an additional target mapping.
        btr.addBuildTarget(Target1, task='target2')

        # Test an unambiguous partial target name.
        args.task = 'targ'
        btarget = btr.getBuildTarget(args)
        self.assertTrue(isinstance(btarget, Target2))

        # Test an ambiguous match.
        args = ArgVals(task='target')
        with self.assertRaisesRegexp(
            RuntimeError, "matched more than one build task name"
        ):
            btr.getBuildTarget(args, targetname_arg='task')

        # Test an invalid target.
        args.task = 'target4'
        with self.assertRaisesRegexp(
            RuntimeError, "Unknown build target"
        ):
            btr.getBuildTarget(args, targetname_arg='task')

