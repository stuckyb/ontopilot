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
from ontopilot.basictimer import BasicTimer
import unittest

# Java imports.


class TestBasicTimer(unittest.TestCase):
    """
    Tests the BasicTimer class.
    """
    def setUp(self):
        pass

    def test_getElapsedTimeStr(self):
        timer = BasicTimer()

        self.assertEqual('0.123', timer._getElapsedTimeStr(0.123))
        self.assertEqual('0.123', timer._getElapsedTimeStr(0.1234))
        self.assertEqual('0.123', timer._getElapsedTimeStr(0.123456))

        self.assertEqual('1.12', timer._getElapsedTimeStr(1.12))
        self.assertEqual('1.12', timer._getElapsedTimeStr(1.123))
        self.assertEqual('1.12', timer._getElapsedTimeStr(1.123456))

        self.assertEqual('100.12', timer._getElapsedTimeStr(100.12))
        self.assertEqual('100.12', timer._getElapsedTimeStr(100.123))
        self.assertEqual('100.12', timer._getElapsedTimeStr(100.123456))

