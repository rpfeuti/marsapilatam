"""
Abstract base for all MARS instrument models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

MarsParam = dict[str, Any]


class MarsInstrument(BaseModel, ABC):
    """
    Common base for all Bloomberg MARS instrument models.

    Subclasses implement :meth:`to_mars_params` which returns the list(s) of
    ``{"name": ..., "value": {...}}`` dicts that MARS expects inside a
    ``structureRequest``.
    """

    @abstractmethod
    def to_mars_params(self) -> list | tuple:
        """Return the MARS API param structure for this instrument."""

    # ------------------------------------------------------------------
    # Helpers for building typed param dicts
    # ------------------------------------------------------------------

    @staticmethod
    def _str_param(name: str, value: str) -> MarsParam:
        return {"name": name, "value": {"stringVal": value}}

    @staticmethod
    def _double_param(name: str, value: float) -> MarsParam:
        return {"name": name, "value": {"doubleVal": float(value)}}

    @staticmethod
    def _date_param(name: str, value: str) -> MarsParam:
        return {"name": name, "value": {"dateVal": value}}

    @staticmethod
    def _selection_param(name: str, value: str) -> MarsParam:
        return {"name": name, "value": {"selectionVal": {"value": value}}}
