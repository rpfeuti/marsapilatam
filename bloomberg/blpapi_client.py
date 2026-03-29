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

import logging
from datetime import date
from typing import Any

try:
    import blpapi
    _BLPAPI_AVAILABLE = True
except ImportError:
    blpapi = None  # type: ignore[assignment]
    _BLPAPI_AVAILABLE = False

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


def _parse_bds_event(
    event: blpapi.Event,
    field: str,
    result: list[dict[str, Any]],
) -> None:
    """Walk a PARTIAL_RESPONSE or RESPONSE event for a single bulk-data field.

    Appends one dict per array row to *result*.  Each dict maps the sub-field
    name (e.g. ``"Member Ticker and Exchange Code"``) to its scalar value.
    """
    for msg in event:
        if not msg.hasElement("securityData"):
            continue
        sec_data = msg.getElement("securityData")
        for i in range(sec_data.numValues()):
            sec_el = sec_data.getValueAsElement(i)

            if sec_el.hasElement("securityError"):
                err = sec_el.getElement("securityError")
                log.warning("BLPAPI security error in bds: %s", err)
                continue

            if not sec_el.hasElement("fieldData"):
                continue

            fd = sec_el.getElement("fieldData")
            if not fd.hasElement(field):
                continue

            arr_el = fd.getElement(field)
            if not arr_el.isArray():
                try:
                    result.append({field: arr_el.getValue()})
                except Exception:
                    pass
                continue

            for j in range(arr_el.numValues()):
                row_el = arr_el.getValueAsElement(j)
                row: dict[str, Any] = {}
                for k in range(row_el.numElements()):
                    sub = row_el.getElement(k)
                    try:
                        row[str(sub.name())] = sub.getValue()
                    except Exception:
                        pass
                result.append(row)


class BlpapiClient:
    """Synchronous Bloomberg Desktop API client (//blp/refdata).

    Manages a single Session lifetime.  Call :meth:`stop` explicitly, or use
    the instance as a context manager to ensure cleanup.

    Raises :exc:`~bloomberg.exceptions.BlpapiError` when the terminal is not
    reachable or a request returns an error status.
    """

    def __init__(self, host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> None:
        if not _BLPAPI_AVAILABLE:
            raise BlpapiError(
                "blpapi package is not installed. "
                "BlpapiClient is not available in this environment."
            )
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

    def bdh(
        self,
        securities: list[str],
        fields: list[str],
        as_of_date: date,
    ) -> dict[str, dict[str, Any]]:
        """Historical data request for a single date — equivalent to Excel BDH().

        Sends a ``HistoricalDataRequest`` with startDate == endDate == *as_of_date*
        and returns a dict in the same shape as :meth:`bdp` so callers can use
        both interchangeably::

            {ticker: {field: value}}

        Args:
            securities: Bloomberg tickers.
            fields:     Bloomberg field names (must support historical data).
            as_of_date: The exact date to fetch data for.

        Returns:
            ``{ticker: {field: value}}`` — missing securities or dates are
            omitted rather than raising an exception (logged as warnings).

        Raises:
            BlpapiError: On ``REQUEST_STATUS`` failure or timeout.
        """
        date_str = as_of_date.strftime("%Y%m%d")

        service = self._session.getService(_REFDATA_SERVICE)
        request = service.createRequest("HistoricalDataRequest")

        for sec in securities:
            request.getElement("securities").appendValue(sec)
        for fld in fields:
            request.getElement("fields").appendValue(fld)

        request.set("startDate", date_str)
        request.set("endDate",   date_str)
        request.set("periodicitySelection", "DAILY")

        log.debug("Sending BDH request — %d securities, date=%s", len(securities), date_str)
        self._session.sendRequest(request)

        result: dict[str, dict[str, Any]] = {}
        done = False
        while not done:
            event = self._session.nextEvent(timeout=_REQUEST_TIMEOUT)
            etype = event.eventType()

            if etype in (blpapi.Event.PARTIAL_RESPONSE, blpapi.Event.RESPONSE):
                for msg in event:
                    if not msg.hasElement("securityData"):
                        continue
                    sec_data = msg.getElement("securityData")
                    ticker   = sec_data.getElementAsString("security")

                    if sec_data.hasElement("securityError"):
                        log.warning("BLPAPI BDH security error for %s", ticker)
                        continue

                    if not sec_data.hasElement("fieldData"):
                        continue

                    field_data = sec_data.getElement("fieldData")
                    row_dict: dict[str, Any] = {}
                    for i in range(field_data.numValues()):
                        pt = field_data.getValueAsElement(i)
                        for fld in fields:
                            if pt.hasElement(fld):
                                try:
                                    row_dict[fld] = pt.getElementAsFloat(fld)
                                except Exception:
                                    try:
                                        row_dict[fld] = pt.getElement(fld).getValue()
                                    except Exception:
                                        pass
                    if row_dict:
                        result[ticker] = row_dict
                    else:
                        log.warning("No data returned by BDH for %s on %s", ticker, date_str)

            if etype == blpapi.Event.RESPONSE:
                done = True
            elif etype == blpapi.Event.REQUEST_STATUS:
                messages = list(event)
                detail   = str(messages[0]) if messages else "unknown"
                raise BlpapiError(f"BLPAPI historical request failed: {detail}")
            elif etype == blpapi.Event.TIMEOUT:
                raise BlpapiError(
                    f"BLPAPI historical request timed out after {_REQUEST_TIMEOUT / 1000:.0f}s"
                )

        log.debug("BDH response received — %d securities returned", len(result))
        return result

    def bds(self, security: str, field: str) -> list[dict[str, Any]]:
        """Bulk data request for one security + field — equivalent to Excel BDS().

        Returns a list of dicts, one per array row.  Each dict maps sub-field
        names to their scalar values.  Useful for array-valued fields such as
        ``INDX_MEMBERS``, ``CURVE_MEMBERS``, etc.

        Example::

            rows = client.bds("YCSW0490 Index", "INDX_MEMBERS")
            # [{"Member Ticker and Exchange Code": "USOSFR1Z BGN Curncy"}, ...]

        Args:
            security: Bloomberg ticker.
            field:    Bulk field name (must return a sequence, not a scalar).

        Returns:
            List of row dicts — empty list if the field is not applicable.

        Raises:
            BlpapiError: On ``REQUEST_STATUS`` failure or timeout.
        """
        service = self._session.getService(_REFDATA_SERVICE)
        request = service.createRequest("ReferenceDataRequest")
        request.getElement("securities").appendValue(security)
        request.getElement("fields").appendValue(field)

        log.debug("Sending BDS request — %s / %s", security, field)
        self._session.sendRequest(request)

        result: list[dict[str, Any]] = []
        done = False
        while not done:
            event = self._session.nextEvent(timeout=_REQUEST_TIMEOUT)
            etype = event.eventType()

            if etype in (blpapi.Event.PARTIAL_RESPONSE, blpapi.Event.RESPONSE):
                _parse_bds_event(event, field, result)

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

        log.debug("BDS response received — %d rows", len(result))
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
