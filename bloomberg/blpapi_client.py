"""
Bloomberg Desktop API (BLPAPI) client.

Provides a thin synchronous wrapper around the native blpapi SDK, following
the same design conventions as mars_client.py:

- One long-lived session per instance (start on __init__, stop on stop() or __exit__)
- Typed bdp() method for synchronous reference data requests (Excel BDP equivalent)
- Raises BlpapiError on session/service/request failures

Requires:
- Bloomberg Professional terminal running locally (default localhost:8194)
- blpapi Python SDK installed from the blpapi-3.25.11.1 package in this repo

Usage::

    client = BlpapiClient()
    data = client.bdp(["USDCOP Curncy", "USDBRL Curncy"], ["PX_LAST"])
    # {"USDCOP Curncy": {"PX_LAST": 4312.5}, "USDBRL Curncy": {"PX_LAST": 5.72}}
    client.stop()

    # Or as a context manager:
    with BlpapiClient() as client:
        data = client.bdp(["USDCOP Curncy"], ["PX_LAST"])
"""

from __future__ import annotations

import logging
from typing import Any

import blpapi

from bloomberg.exceptions import BlpapiError

log = logging.getLogger(__name__)

_REFDATA_SERVICE = "//blp/refdata"
_DEFAULT_HOST    = "localhost"
_DEFAULT_PORT    = 8194
_REQUEST_TIMEOUT = 10_000  # milliseconds


def _parse_refdata_event(event: blpapi.Event, result: dict[str, dict[str, Any]]) -> None:
    """Walk a PARTIAL_RESPONSE or RESPONSE event and populate *result* in-place.

    Structure walked:
        securityData[]
            security      (ticker string)
            fieldData     (name → scalar value)
            securityError (optional — skipped with a warning)
    """
    for msg in event:
        if not msg.hasElement("securityData"):
            continue
        sec_data = msg.getElement("securityData")
        for i in range(sec_data.numValues()):
            sec_el  = sec_data.getValueAsElement(i)
            ticker  = sec_el.getElementAsString("security")

            if sec_el.hasElement("securityError"):
                err = sec_el.getElement("securityError")
                log.warning("BLPAPI security error for %s: %s", ticker, err)
                continue

            if not sec_el.hasElement("fieldData"):
                continue

            fields_el = sec_el.getElement("fieldData")
            result.setdefault(ticker, {})
            for j in range(fields_el.numElements()):
                fld_el = fields_el.getElement(j)
                result[ticker][str(fld_el.name())] = fld_el.getValue()


class BlpapiClient:
    """Synchronous Bloomberg Desktop API client (//blp/refdata).

    Manages a single Session lifetime.  Call :meth:`stop` explicitly, or use
    the instance as a context manager to ensure cleanup.

    Raises :exc:`~bloomberg.exceptions.BlpapiError` when the terminal is not
    reachable or a request returns an error status.
    """

    def __init__(self, host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> None:
        opts = blpapi.SessionOptions()
        opts.setServerAddress(host, port, 0)
        self._session = blpapi.Session(opts)

        log.debug("Starting BLPAPI session — %s:%s", host, port)
        if not self._session.start():
            raise BlpapiError(
                f"Failed to start BLPAPI session ({host}:{port}) — "
                "is the Bloomberg Professional terminal running?"
            )

        log.debug("Opening service %s", _REFDATA_SERVICE)
        if not self._session.openService(_REFDATA_SERVICE):
            self._session.stop()
            raise BlpapiError(f"Failed to open Bloomberg service {_REFDATA_SERVICE}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def bdp(self, securities: list[str], fields: list[str]) -> dict[str, dict[str, Any]]:
        """Synchronous reference data request — equivalent to Excel BDP().

        Sends a single ``ReferenceDataRequest`` for all *securities* and
        *fields* and blocks until the full ``RESPONSE`` is received.

        Args:
            securities: Bloomberg tickers, e.g. ``["USDCOP Curncy", "IBM US Equity"]``.
            fields:     Bloomberg field names, e.g. ``["PX_LAST", "NAME"]``.

        Returns:
            ``{ticker: {field: value}}`` — missing securities or fields are
            omitted rather than raising an exception (logged as warnings).

        Raises:
            BlpapiError: On ``REQUEST_STATUS`` failure or timeout.
        """
        service = self._session.getService(_REFDATA_SERVICE)
        request = service.createRequest("ReferenceDataRequest")

        for sec in securities:
            request.getElement("securities").appendValue(sec)
        for fld in fields:
            request.getElement("fields").appendValue(fld)

        log.debug("Sending BDP request — %d securities, %d fields", len(securities), len(fields))
        self._session.sendRequest(request)

        result: dict[str, dict[str, Any]] = {}
        done = False
        while not done:
            event = self._session.nextEvent(timeout=_REQUEST_TIMEOUT)
            etype = event.eventType()

            if etype in (blpapi.Event.PARTIAL_RESPONSE, blpapi.Event.RESPONSE):
                _parse_refdata_event(event, result)

            if etype == blpapi.Event.RESPONSE:
                done = True
            elif etype == blpapi.Event.REQUEST_STATUS:
                messages = list(event)
                detail   = str(messages[0]) if messages else "unknown"
                raise BlpapiError(f"BLPAPI request failed: {detail}")
            elif etype == blpapi.Event.TIMEOUT:
                raise BlpapiError(
                    f"BLPAPI request timed out after {_REQUEST_TIMEOUT / 1000:.0f}s"
                )

        log.debug("BDP response received — %d securities returned", len(result))
        return result

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Stop the BLPAPI session and release resources."""
        try:
            self._session.stop()
            log.debug("BLPAPI session stopped")
        except Exception:
            pass

    def __enter__(self) -> BlpapiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()
