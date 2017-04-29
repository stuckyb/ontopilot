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

#
# Provides convenience methods for working with remote resources.
#

# Python imports.
from __future__ import unicode_literals
import urlparse, httplib
from ssl import SSLError
import time
import socket

# Java imports.


class ConnectionFailError(RuntimeError):
    """
    Represents exceptions caused by failed HTTP or HTTPS connection attempts.
    """
    pass


class NotFoundError(RuntimeError):
    """
    Represents errors caused by 404: Not found HTTP status codes.
    """
    pass


def httpHEAD(sourceIRI):
    """
    Makes an HTTP HEAD request to sourceIRI and returns the response.  Works
    for either HTTP or HTTPS IRIs.  The response is returned as a standard
    Python HTTPResponse object.

    sourceIRI: A fully expanded IRI as an OWL API IRI object or a string.
    """
    # The maximum number of times to retry a connection attempt.
    MAX_RETRIES = 6

    source_iri = unicode(sourceIRI)
    parts = urlparse.urlsplit(source_iri)

    # Reconstruct the portion of the IRI that comes after the scheme and
    # host string.
    location_part = urlparse.urlunsplit(('', '') + parts[2:5])

    retrycnt = 0
    response = None
    success = False
    # The Jython SSL library will occasionally produce "_socket.SSLError:
    # [Errno 1] Illegal state exception" exceptions when multiple
    # connection attempts are made without any wait time in between.  Thus,
    # we need to allow for this by wrapping all of the network logic in a
    # loop and waiting a short time on failure before retrying.
    while (retrycnt < MAX_RETRIES) and not(success):
        try:
            # Initialize the connection.  Note that this will correctly
            # handle non-standard TCP port numbers specified as part of the
            # URL string (e.g., "http://example.com:8080"), because they
            # will be included as part of the "netloc" attribute by
            # urlsplit() and then extracted by the httplib methods.
            if parts.scheme.lower() == 'http':
                conn = httplib.HTTPConnection(parts.netloc)
            elif parts.scheme.lower() == 'https':
                conn = httplib.HTTPSConnection(parts.netloc)
            else:
                raise ConnectionFailError(
                    'The IRI <{0}> is not an HTTP or HTTPS IRI.'.format(
                        source_iri
                    )
                )

            conn.request('HEAD', location_part)
            response = conn.getresponse()
            conn.close()
            success = True

            status = int(response.status)
            if status == 404:
                raise NotFoundError(
                    'The resource at <{0}> could not be found.  Please '
                    'make sure that the IRI is correct.'.format(source_iri)
                )

        except SSLError as err:
            time.sleep(0.1)
            retrycnt += 1
            if retrycnt == MAX_RETRIES:
                raise ConnectionFailError(
                    'Unable to access the resource at <{0}> due to '
                    'repeated SSL connection failures.  Please make sure '
                    'that the IRI is correct and that an Internet '
                    'connection is available, if needed.'.format(source_iri)
                )
        except (
            socket.error, socket.herror, socket.gaierror, socket.timeout
        ) as err:
            raise ConnectionFailError(
                'Unable to access the resource at <{0}> due to a TCP '
                'connection error: {1}.'.format(source_iri, unicode(err))
            )

    return response

def checkForRedirect(sourceIRI):
    """
    Given a source IRI, checks if the IRI is a redirect to an alternative
    location.  Handles multi-step redirects (e.g., the original IRI redirects
    to another IRI, which redirects to another IRI, ...).  If the source IRI is
    a redirect, returns a string containing the IRI of the final document
    location.  Otherwise, returns an empty string.

    sourceIRI: A fully expanded IRI as an OWL API IRI object or a string.
    """
    redirected = False
    status = 300
    curr_iri = unicode(sourceIRI)

    while (status < 400) and (status >= 300):
        parts = urlparse.urlsplit(curr_iri)
        if parts.scheme.lower() in ('http', 'https'):
            response = httpHEAD(curr_iri)
        else:
            status = 200
            break

        status = int(response.status)
        if (status < 400) and (status >= 300):
            redirected = True
            curr_iri = urlparse.urljoin(
                curr_iri, response.getheader('location')
            )

    if redirected:
        return curr_iri
    else:
        return ''

