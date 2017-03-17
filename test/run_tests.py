#!/usr/bin/env jython

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


import sys
import os.path
import unittest


# Make sure we can find the ontopilot modules.
ontopilot_dir = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '../bin'
    )
)
sys.path.append(ontopilot_dir)

# Implements a very simple test runner for all test modules.  This could
# probably be done even more easily using a package such as nose, but the
# advantage here is that only unittest methods are needed, so the test suites
# are very easy to run on any platform without needing to install additional
# packages.

test_modules = [
    'test_labelmap', 'test_tablereader', 'test_mshelper',
    'test_owlontologybuilder', 'test_ontology', 'test_delimstr_parser',
    'test_ontology_entities', 'test_ontoconfig', 'test_onto_buildtarget',
    'test_importmodulebuilder', 'test_imports_buildtarget',
    'test_reasoner_manager', 'test_inferred_axiom_adder', 'test_buildtarget',
    'test_modified_onto_buildtarget', 'test_buildtarget_manager',
    'test_obohelper', 'test_idresolver', 'test_observable',
    'test_update_base_imports_buildtarget', 'test_release_buildtarget'
]

successful = True
total = failed = 0

runner = unittest.TextTestRunner(verbosity=2)

for test_module in test_modules:
    suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
    res = runner.run(suite)

    total += res.testsRun
    # Get the approximate number of failed tests.  This is an approximation
    # because a single test might both trigger an exception and an assert*()
    # failure, depending on how the test is configured.
    failed += len(res.errors) + len(res.failures)

    if not res.wasSuccessful():
        successful = False


if successful:
    if total != 1:
        print '\n\n{0} tests were run.  All tests completed successfully.\n'.format(total)
    else:
        print '\n\n1 test was run.  All tests completed successfully.\n'
else:
    if total != 1:
        msgstr = '\n\nFAILED:  {0} tests were run, resulting in '.format(total)
        if failed == 1:
            msgstr += '1 test failure or unexpected exception.'
        else:
            msgstr += '{0} test failures or unexpected exceptions.'.format(failed)
        
        print msgstr + '  See output above for details.\n'
    else:
        print ('\n\nFAILED:  1 test was run.  The test was unsuccessful.  See '
            + 'output above for details.\n')

