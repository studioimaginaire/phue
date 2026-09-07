"""Typed Hue V2 resources; unknown fields are retained for forward compatibility."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HueModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class ResourceIdentifier(HueModel):
    rid: str
    rtype: str


class Metadata(HueModel):
    name: str = ""


class Resource(HueModel):
    id: str
    type: str
    id_v1: str | None = None


class Light(Resource):
    metadata: Metadata
    on: dict[str, Any] = Field(default_factory=dict)
    dimming: dict[str, Any] = Field(default_factory=dict)
    color: dict[str, Any] | None = None
    color_temperature: dict[str, Any] | None = None
    effects_v2: dict[str, Any] | None = None
    effects: dict[str, Any] | None = None
    dynamics: dict[str, Any] | None = None
    owner: ResourceIdentifier | None = None

    @property
    def supported_effects(self) -> list[str]:
        if self.effects_v2 is not None:
            return list(self.effects_v2.get("action", {}).get("effect_values", []))
        if self.effects is not None:
            return list(self.effects.get("effect_values", []))
        return []


class Room(Resource):
    metadata: Metadata
    children: list[ResourceIdentifier] = Field(default_factory=list[ResourceIdentifier])
    services: list[ResourceIdentifier] = Field(default_factory=list[ResourceIdentifier])


class Scene(Resource):
    metadata: Metadata
    group: ResourceIdentifier
    actions: list[dict[str, Any]] = Field(default_factory=list[dict[str, Any]])
    palette: dict[str, Any] | None = None
    speed: float | None = None
    auto_dynamic: bool | None = None
    status: dict[str, Any] | None = None


class LightState(BaseModel):
    """Partial light update with human-facing units; omitted fields are untouched."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    on: bool | None = None
    brightness: float | None = Field(default=None, ge=0, le=100)
    temperature_kelvin: int | None = Field(default=None, ge=2000, le=6500)
    xy: tuple[float, float] | None = None
    effect: str | None = None
    effect_speed: float | None = Field(default=None, ge=0, le=1)
    transition_seconds: float | None = Field(default=None, ge=0, le=3600)

    @model_validator(mode="after")
    def validate_update(self) -> "LightState":
        if self.xy is not None:
            if any(not 0 <= n <= 1 for n in self.xy) or sum(self.xy) > 1:
                raise ValueError("xy must be within the CIE chromaticity triangle")
            if self.temperature_kelvin is not None:
                raise ValueError("Choose xy or temperature_kelvin")
        if self.effect_speed is not None and self.effect in (None, "no_effect"):
            raise ValueError("effect_speed requires an active effect")
        if self.effect is not None and not self.effect.strip():
            raise ValueError("effect must not be empty")
        if (
            self.effect not in (None, "no_effect")
            and self.transition_seconds is not None
        ):
            raise ValueError("Native effects use effect_speed, not transition_seconds")
        if not self.model_dump(exclude_none=True, exclude={"transition_seconds"}):
            raise ValueError("Provide at least one property to change")
        return self

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.on is not None:
            payload["on"] = {"on": self.on}
        if self.brightness is not None:
            payload["dimming"] = {"brightness": self.brightness}
        color: dict[str, Any] = {}
        if self.xy is not None:
            color["color"] = {"xy": {"x": self.xy[0], "y": self.xy[1]}}
        if self.temperature_kelvin is not None:
            color["color_temperature"] = {
                "mirek": round(1_000_000 / self.temperature_kelvin)
            }
        if self.effect is not None:
            action: dict[str, Any] = {"effect": self.effect}
            if self.effect != "no_effect":
                parameters = dict(color)
                if self.effect_speed is not None:
                    parameters["speed"] = self.effect_speed
                if parameters:
                    action["parameters"] = parameters
            else:
                payload.update(color)
            payload["effects_v2"] = {"action": action}
        else:
            payload.update(color)
        if self.transition_seconds is not None:
            payload["dynamics"] = {"duration": round(self.transition_seconds * 1000)}
        return payload
