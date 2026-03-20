########################################################################################################
# Copyright 2023 Bloomberg Finance L.P.

# Sample code provided by Bloomberg is made available for illustration purposes only. Sample code
# is modifiable by individual users and is not reviewed for reliability, accuracy and
# is not supported as part of any Bloomberg service. Users are solely responsible for the selection
# of and use or intended use of the sample code, its applicability, accuracy and adequacy,
# and the resultant output thereof. Sample code is proprietary and confidential to Bloomberg
# and neither the recipient nor any of its representatives may distribute, publish or display such code
# to any other party, other than information disclosed to its employees on a need-to-know basis
# in connection with the purpose for which such code was provided.
# Sample code provided by Bloomberg is provided without any representations or warranties and subject
# to modification by Bloomberg in its sole discretion.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL BLOOMBERG BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
########################################################################################################

# Sample code for jwt generation for authentication purposes
#
# The code below creates a JWT using credentials provided by the enterprise
# console and then sends a message with the JWT as a message header.

# This script may not work if you are current under an http proxy. To resolve it
# remove the http proxy settings and try again.

import binascii
import time
import uuid

try:
    # Python 2
    import urllib as urlencodelib

    import urlparse as urlparselib

    # import urllib2 as urlrequestlib
except ImportError:
    # Python 3
    import urllib.parse as urlencodelib
    import urllib.parse as urlparselib

    # This only works because all the Py2 urllib2 features we're using are in the
    # Py3 urllib.requests module. If we add a feature from another Py3 module,
    # we'll have to refactor this.
    # import urllib.request as urlrequestlib

import base64

import jwt

EXPIRE_TIME = 300


def b64encode(string):
    """Encode the JWT and escape characters"""
    if not isinstance(string, type(b"")):
        string = string.encode()
    return base64.urlsafe_b64encode(string).replace("=".encode(), "".encode()).decode()


class JwtFactory(object):
    """This class creates the JWT objects using the credentials (id and secret)."""

    def __init__(self, baseurl, client_id, client_secret):
        """Get basic information for the JWT"""

        self._baseurl = baseurl
        self._client_id = client_id
        self._client_secret = client_secret

        self._last_jwt = None
        self._last_payload = None

    def generate(self, path, method, kvp=[]):
        """Create the entire JWT, encrypt, and return it"""
        payload = self._build_payload(path, self._baseurl, method, kvp)
        secret = binascii.unhexlify(self._client_secret)

        self._last_jwt = jwt.encode(payload, secret, algorithm="HS256")
        return self._last_jwt

    def _build_payload(self, path, uri, method="GET", kvp={}):
        """Set the payload of the JWT"""
        current_time = int(round(time.time()))
        generated_kvp = {
            "iss": self._client_id,  # "Issuer" Client Id from credentials.
            "exp": current_time + EXPIRE_TIME,  # "Expiration Time" Maximum expiration time can be sent to 24 hours
            "nbf": current_time - 60,  # "Not Before" Time before which JWT MUST NOT be accepted for processing
            "iat": current_time - 60,  # "Issued At" Time at which the JWT was issued
            "jti": str(uuid.uuid4()),  # "JWT ID" unique identifier for the JWT
            "region": "ny",  # Bloomberg Internal Field
            "method": method,  # POST, GET, etc. HTTP verb
            "path": path,  # Mars API endpoint path
            "host": uri,  # The base url of the endpoint
            "client_id": self._client_id,  # Client id from the credentials
        }

        payload = {}
        payload.update(kvp)  # Add key, value pairs to payload
        payload.update(generated_kvp)

        self._last_payload = payload
        return self._last_payload

    def get_last_payload(self):
        return self._last_payload

    def get_last_jwt(self):
        return self._last_jwt


class UrlFactory(object):
    """This class will create the url with the encoded JWT, allowing you to get or post
    data as normal to this url"""

    def __init__(self, baseurl, client_id, client_secret):
        """Setting up the JWTFactory to create a valid JWT"""

        self._baseurl = baseurl
        self._client_id = client_id
        self._client_secret = client_secret

        self.jwt = JwtFactory(baseurl, client_id, client_secret)

    def generate(self, path, method="GET", noJwt=False, query_params={}, jwtkvp={}):
        """Creates the url, and in the process creates the jwt from JwtFactory"""

        url = self._baseurl + path

        if noJwt:
            # Only useful for debugging. Will not authenticate against Bloomberg without JWT
            return url

        else:
            # The url is put together with urlparselib. See their documentation for more details on these steps
            parts = urlparselib.urlparse(url)
            _query_params = urlparselib.parse_qs(parts.query)
            # Take in any additional user-supplied parameters for request
            _query_params.update(query_params)
            _query_params["jwt"] = self.jwt.generate(parts.path, method, jwtkvp)  # Set JWT in header param
            query = urlencodelib.urlencode(_query_params, doseq=True)
            parts = parts._replace(query=query)
            return urlparselib.urlunparse(parts)
