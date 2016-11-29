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


# Make sure we can find the ontobuilder modules.
ontobuilder_dir = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '../bin'
    )
)
sys.path.append(ontobuilder_dir)

# Implements a very simple test runner for all test modules.  This could
# probably be done even more easily using a package such as nose, but the
# advantage here is that only unittest methods are needed, so the test suites
# are very easy to run on any platform without needing to install additional
# packages.

test_modules = ['test_labelmap', 'test_tablereader']

successful = True
total = 0

runner = unittest.TextTestRunner(verbosity=2)

for test_module in test_modules:
    suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
    res = runner.run(suite)

    total += res.testsRun

    if not res.wasSuccessful():
        successful = False


if successful:
    print '\n\n' + str(total) + ' tests were run.  All tests completed successfully.\n'
else:
    print ('\n\nFAILED:  ' + str(total) + 
            ' tests were run.  One or more tests were unsuccessful.  See output above for details.\n')

