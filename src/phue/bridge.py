"""Asynchronous client for the local Hue V2 API."""

import ssl
from typing import Any, Literal, TypeVar
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from phue.exceptions import HueAPIError, HueConnectionError
from phue.models import Light, LightState, Resource, ResourceIdentifier, Room, Scene

Model = TypeVar("Model", bound=BaseModel)


class Envelope(BaseModel):
    errors: list[dict[str, Any]]
    data: list[dict[str, Any]]


class Bridge:
    """Use as an async context manager. A supplied client remains caller-owned.

    TLS verification is enabled by default. Pass an SSLContext that trusts your
    bridge's certificate, or an explicitly configured caller-owned AsyncClient.
    """

    def __init__(
        self,
        host: str,
        application_key: str,
        *,
        verify: bool | ssl.SSLContext = True,
        timeout: float = 10,
        http_client: httpx.AsyncClient | None = None,
    ):
        url = httpx.URL(f"https://{host}")
        if (
            not url.host
            or url.username
            or url.password
            or url.path != "/"
            or url.query
            or url.fragment
        ):
            raise ValueError(
                "host must be a bridge hostname or IP address, optionally with a port"
            )
        if not application_key:
            raise ValueError("application_key must not be empty")
        self._base_url = str(url).rstrip("/")
        self._key = application_key
        self._verify = verify
        self._timeout = timeout
        self._client = http_client
        self._owns_client = http_client is None
        self._entered = False

    async def __aenter__(self) -> "Bridge":
        if self._entered:
            raise RuntimeError("Bridge context is already entered")
        if self._owns_client:
            self._client = httpx.AsyncClient(verify=self._verify, timeout=self._timeout)
        elif self._client is None or self._client.is_closed:
            raise RuntimeError("The supplied HTTP client is closed")
        self._entered = True
        return self

    async def __aexit__(self, *_: Any) -> None:
        self._entered = False
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        kind: str,
        resource_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not self._entered or self._client is None:
            raise RuntimeError("Use Bridge inside an async with block")
        path = "/clip/v2/resource" + (f"/{kind}" if kind else "")
        if resource_id is not None:
            path += "/" + str(UUID(resource_id))
        try:
            response = await self._client.request(
                method,
                self._base_url + path,
                headers={"hue-application-key": self._key},
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HueConnectionError(
                f"Hue returned HTTP {exc.response.status_code}"
            ) from None
        except httpx.RequestError:
            raise HueConnectionError("Hue bridge request failed") from None
        try:
            envelope = Envelope.model_validate(response.json())
        except (ValueError, ValidationError):
            raise HueConnectionError(
                "Hue returned an invalid response envelope"
            ) from None
        if envelope.errors:
            errors = [dict(error) for error in envelope.errors]
            for error in errors:
                if isinstance(error.get("description"), str):
                    error["description"] = error["description"].replace(
                        self._key, "[redacted]"
                    )
            raise HueAPIError(errors, envelope.data)
        return envelope.data

    async def _list(self, kind: str, model: type[Model]) -> list[Model]:
        return [model.model_validate(item) for item in await self._request("GET", kind)]

    async def lights(self) -> list[Light]:
        return await self._list("light", Light)

    async def light(self, light_id: str) -> Light:
        items = await self._request("GET", "light", light_id)
        if len(items) != 1:
            raise HueConnectionError("Expected one light in the bridge response")
        return Light.model_validate(items[0])

    async def rooms(self) -> list[Room]:
        return await self._list("room", Room)

    async def scenes(self) -> list[Scene]:
        return await self._list("scene", Scene)

    async def resources(self) -> list[Resource]:
        """Read all resources, retaining unknown fields for relationships and capabilities."""
        return [
            Resource.model_validate(item) for item in await self._request("GET", "")
        ]

    async def set_light(
        self, light_id: str, state: LightState
    ) -> list[ResourceIdentifier]:
        """Update one light. Native effects are validated against its advertised support."""
        if state.effect is not None:
            light = await self.light(light_id)
            if state.effect not in light.supported_effects:
                raise ValueError(
                    f"Effect {state.effect!r} is not supported by this light"
                )
            if light.effects_v2 is None:
                raise ValueError("This light does not advertise effects_v2 support")
        result = await self._request("PUT", "light", light_id, state.to_payload())
        return [ResourceIdentifier.model_validate(item) for item in result]

    async def set_group(
        self, grouped_light_id: str, state: LightState
    ) -> list[ResourceIdentifier]:
        """Update a room's grouped_light service. Effects must target individual lights."""
        if state.effect is not None:
            raise ValueError(
                "Apply native effects to individual lights, not grouped_light"
            )
        result = await self._request(
            "PUT", "grouped_light", grouped_light_id, state.to_payload()
        )
        return [ResourceIdentifier.model_validate(item) for item in result]

    async def recall_scene(
        self,
        scene_id: str,
        *,
        action: Literal["active", "dynamic_palette", "static"] = "active",
        duration_seconds: float | None = None,
    ) -> list[ResourceIdentifier]:
        """Recall a saved scene, including its per-light effect actions."""
        if action not in ("active", "dynamic_palette", "static"):
            raise ValueError("Unknown scene recall action")
        recall: dict[str, Any] = {"action": action}
        if duration_seconds is not None:
            if not 0 <= duration_seconds <= 3600:
                raise ValueError("duration_seconds must be between 0 and 3600")
            recall["duration"] = round(duration_seconds * 1000)
        result = await self._request("PUT", "scene", scene_id, {"recall": recall})
        return [ResourceIdentifier.model_validate(item) for item in result]
