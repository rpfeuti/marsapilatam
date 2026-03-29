"""
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


class MarsApiError(Exception):
    """Base class for all MARS API errors."""


class IpNotWhitelistedError(MarsApiError):
    """Raised when the caller's IP address is not whitelisted by Bloomberg."""


class SessionError(MarsApiError):
    """Raised when a session cannot be started or is invalid."""


class PricingError(MarsApiError):
    """Raised when a pricing or solve request returns an error result."""


class CurveError(MarsApiError):
    """Raised when a curve data download fails."""


class StructuringError(MarsApiError):
    """Raised when a deal structuring request fails."""


class BlpapiError(Exception):
    """Raised when the Bloomberg Desktop API (BLPAPI) session or request fails.

    Kept separate from MarsApiError because BLPAPI uses a different transport
    (native C++ SDK / localhost:8194) rather than the MARS REST API.
    """
