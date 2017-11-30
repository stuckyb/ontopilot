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
import os.path
import urlparse, urllib
import unittest
#from testfixtures import LogCapture

# Java imports.


class Test_nethelper(unittest.TestCase):
    """
    Tests the methods in the nethelper module.
    """
    def setUp(self):
        pass

    def test_httpHEAD(self):
        # Check a valid HTTP URI.
        result = nethelper.httpHEAD('http://httpbin.org/html')
        self.assertEqual(200, result.status)
        self.assertEqual('', result.read())

        # Check a valid HTTPS URI.  Testing with Jython 2.7.0 did not work for
        # all IRIs.  For example, https://httpbin.org/ fails.  I spent some
        # time running this down, and the failure was originating from a call
        # in Lib/_socket.py (line 769) to the sync() method of SslHandler,
        # which is part of the Java netty library.  I've not investigated
        # beyond that.
        result = nethelper.httpHEAD('https://github.com/')
        self.assertEqual(200, result.status)
        self.assertEqual('', result.read())

        # Check an IRI that does not use HTTP or HTTPS.
        with self.assertRaisesRegexp(
            ConnectionFailError, 'is not an HTTP or HTTPS IRI.'
        ):
            nethelper.httpHEAD('file:/local/path')

        # Check a non-existant URI.
        with self.assertRaisesRegexp(NotFoundError, 'could not be found'):
            nethelper.httpHEAD('http://httpbin.org/status/404')

        # Check a non-resolving URI.  Note that this might not fail with ISPs
        # that resolve invalid domain names to a "helpful" information page
        # hosted by the ISP.
        with self.assertRaisesRegexp(
            ConnectionFailError, 'TCP connection error: .* getaddrinfo failed.'
        ):
            nethelper.httpHEAD('http://fake.domain.blah/')

        # Check a denied connection attempt.
        with self.assertRaisesRegexp(
            ConnectionFailError, 'TCP connection error: .* Connection refused.'
        ):
            nethelper.httpHEAD('http://127.0.0.1:9000/')

    def test_checkForRedirect(self):
        # Check an IRI that does not use HTTP or HTTPS.
        self.assertEqual('', nethelper.checkForRedirect('file:/local/path'))

        # Check an HTTP IRI that does not trigger a redirect.
        self.assertEqual(
            '', nethelper.checkForRedirect('http://httpbin.org/html')
        )

        # Check an HTTPS IRI that does not trigger a redirect.  See comments
        # above for testing an HTTPS connection in test_httpHEAD().
        self.assertEqual(
            '', nethelper.checkForRedirect('https://github.com/')
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

    def test_checkForContentLength(self):
        # Check an HTTP IRI that returns a Content-Length header.
        self.assertEqual(
            3741, nethelper.checkForContentLength('http://httpbin.org/html')
        )

        # Check an HTTP IRI that does not return a Content-Length header.
        self.assertEqual(
            None, nethelper.checkForContentLength('https://github.com/')
        )

        # Build local filesystem IRIs for testing.
        fsprefix = 'file://localhost'
        file_iri = urlparse.urljoin(fsprefix, urllib.pathname2url(
            os.path.abspath('test_data/file_size_test.txt')
        ))
        nohost_file_iri = urlparse.urljoin('file:///', urllib.pathname2url(
            os.path.abspath('test_data/file_size_test.txt')
        ))
        dir_iri = urlparse.urljoin(fsprefix, urllib.pathname2url(
            os.path.abspath('test_data/')
        ))
        invalid_iri = urlparse.urljoin(fsprefix, urllib.pathname2url(
            os.path.abspath('test_data/invalid.owl')
        ))

        # Check valid local filesystem IRIs.
        self.assertEqual(
            143, nethelper.checkForContentLength(file_iri)
        )
        self.assertEqual(
            143, nethelper.checkForContentLength(nohost_file_iri)
        )

        # Check local IRIs for a non-existent object and a non-file object.
        self.assertEqual(
            None, nethelper.checkForContentLength(dir_iri)
        )
        self.assertEqual(
            None, nethelper.checkForContentLength(invalid_iri)
        )

        # Test an unsupported scheme.
        self.assertEqual(
            None, nethelper.checkForContentLength('mailto:someaddress@somewhere')
        )

