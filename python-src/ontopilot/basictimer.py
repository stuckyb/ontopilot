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
from __future__ import unicode_literals
import time

# Java imports.


class BasicTimer:
    """
    Defines a basic timer for timing code execution (or anything else).
    """
    def __init__(self):
        self.start_time = self.end_time = 0.0
    
    def _getElapsedTimeStr(self, elapsed):
        """
        Converts an elapsed time as a floating-point number into a string
        suitable for display.  If the elapsed time is >= 1, the number is
        rounded to 2 decimal places.  Otherwise, it is rounded to 3 significant
        figures.
        
        elapsed (float): The elapsed time.
        """
        if elapsed < 1.0:
            elapsedstr = '{0:.3g}'.format(elapsed)
        else:
            elapsedstr = '{0}'.format(round(elapsed, 2))
    
        return elapsedstr

    def __str__(self):
        return self._getElapsedTimeStr(self.end_time - self.start_time)

    def start(self):
        self.start_time = time.clock()

    def stop(self):
        """
        Stops the timer and records the elapsed time.  Returns this BasicTimer
        object so that stop() can be used in expressions where the results
        should immediately be coverted to an elapsed time string.
        """
        self.end_time = time.clock()

        return self

