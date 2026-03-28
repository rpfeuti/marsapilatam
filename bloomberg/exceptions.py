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
