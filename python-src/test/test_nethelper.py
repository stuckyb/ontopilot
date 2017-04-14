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
import ontopilot.nethelper as nethelper
from ontopilot.nethelper import NotFoundError, ConnectionFailError
import unittest
#from testfixtures import LogCapture

# Java imports.


class Test_nethelper(unittest.TestCase):
    """
    Tests the methods in the nethelper module.
    """
    def setUp(self):
        pass

    def test_checkForRedirect(self):
        # Check an IRI that does not use HTTP or HTTPS.
        self.assertEqual('', nethelper.checkForRedirect('file:/local/path'))

        # Check an HTTP IRI that does not trigger a redirect.
        self.assertEqual(
            '', nethelper.checkForRedirect('http://httpbin.org/html')
        )

        # Check an HTTPS IRI that does not trigger a redirect.
        self.assertEqual(
            '', nethelper.checkForRedirect('https://httpbin.org/html')
        )

        # Check a one-hop redirect.
        self.assertEqual(
            'http://httpbin.org/get',
            nethelper.checkForRedirect('http://httpbin.org/redirect/1')
        )

        # Check a multi-hop redirect.
        self.assertEqual(
            'http://httpbin.org/get',
            nethelper.checkForRedirect('http://httpbin.org/redirect/4')
        )

        # Check a non-existant URI.
        with self.assertRaisesRegexp(NotFoundError, 'could not be found'):
            nethelper.checkForRedirect('http://httpbin.org/status/404')

        # Check a non-resolving URI.
        with self.assertRaisesRegexp(
            ConnectionFailError, 'TCP connection error: .* getaddrinfo failed.'
        ):
            nethelper.checkForRedirect('http://fake.domain.blah/')

        # Check a denied connection attempt.
        with self.assertRaisesRegexp(
            ConnectionFailError, 'TCP connection error: .* Connection refused.'
        ):
            nethelper.checkForRedirect('http://127.0.0.1:9000/')

