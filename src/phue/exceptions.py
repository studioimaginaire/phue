"""Errors from Hue V2 transport and API responses."""

from typing import Any


class HueError(Exception):
    """Base error for Hue communication."""


class HueAPIError(HueError):
    """The bridge rejected a request; data retains any partial successes."""

    def __init__(self, errors: list[dict[str, Any]], data: list[dict[str, Any]]):
        self.errors = errors
        self.data = data
        super().__init__(
            "; ".join(
                str(error.get("description", "Hue API error")) for error in errors
            )
        )


class HueConnectionError(HueError):
    """The bridge could not be reached or returned an invalid HTTP response."""
