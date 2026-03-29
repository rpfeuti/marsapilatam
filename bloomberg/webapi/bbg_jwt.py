"""
Bloomberg JWT authentication factory.

Generates HS256-signed JWTs for the MARS REST API.
Each token encodes the HTTP method and endpoint path so Bloomberg can verify
the token was created for that specific request.

Original Bloomberg sample code — cleaned up, fully typed, Python 3.12.

Copyright 2026, Bloomberg Finance L.P.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:  The above
copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from __future__ import annotations

import binascii
import time
import uuid

import jwt

_EXPIRE_SECONDS: int = 300
_NOT_BEFORE_SKEW: int = 60


class JwtFactory:
    """Creates signed JWT tokens for authenticating MARS API requests."""

    def __init__(self, host: str, client_id: str, client_secret: str) -> None:
        self._host = host
        self._client_id = client_id
        self._secret_bytes: bytes = binascii.unhexlify(client_secret)

    def generate(
        self,
        path: str,
        method: str,
        kvp: dict[str, object] | None = None,
    ) -> str:
        """
        Sign and return a JWT for the given endpoint and HTTP method.

        Args:
            path:   API endpoint path, e.g. ``/marswebapi/v1/securitiesPricing``.
            method: HTTP verb (``GET``, ``POST``, ``PATCH``, ``DELETE``).
            kvp:    Optional extra claims merged into the payload (e.g. ``{"uuid": 12345}``).

        Returns:
            Encoded JWT string.
        """
        now = int(time.time())
        payload: dict[str, object] = {
            # Standard JWT claims
            "iss": self._client_id,
            "exp": now + _EXPIRE_SECONDS,
            "nbf": now - _NOT_BEFORE_SKEW,
            "iat": now - _NOT_BEFORE_SKEW,
            "jti": str(uuid.uuid4()),
            # Bloomberg-specific claims
            "region": "ny",
            "method": method,
            "path": path,
            "host": self._host,
            "client_id": self._client_id,
        }
        if kvp:
            payload.update(kvp)

        return jwt.encode(payload, self._secret_bytes, algorithm="HS256")
