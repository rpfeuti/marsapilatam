"""
Extract IPv4 from Bloomberg MARS API error text (allowlist / denied IP in response body).

No external services — the API message already states which IP was rejected.
"""

from __future__ import annotations

import re

_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)


def ipv4_from_text(text: str) -> str | None:
    """Return the first IPv4 embedded in *text* (e.g. Bloomberg MARS error body)."""
    if not text:
        return None
    m = _IPV4_RE.search(text)
    return m.group(0) if m else None


def outbound_ip_for_whitelist(mars_error_text: str | None) -> str | None:
    """Parse denied IP from the MARS exception string (full HTTP error body)."""
    if not mars_error_text:
        return None
    return ipv4_from_text(mars_error_text)
