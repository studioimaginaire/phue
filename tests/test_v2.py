import json
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from phue import Bridge, HueAPIError, HueConnectionError, LightState

LIGHT = "00000000-0000-0000-0000-000000000001"
SCENE = "00000000-0000-0000-0000-000000000002"
LIGHT_DATA = {
    "id": LIGHT,
    "type": "light",
    "metadata": {"name": "Lamp"},
    "effects_v2": {"action": {"effect_values": ["no_effect", "candle", "fire"]}},
    "future_capability": {"supported": True},
}


async def test_effect_parameters_and_resource_preservation() -> None:
    writes: list[dict[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.scheme == "https"
        assert request.headers["hue-application-key"] == "key"
        assert request.url.path == f"/clip/v2/resource/light/{LIGHT}"
        if request.method == "GET":
            return httpx.Response(200, json={"errors": [], "data": [LIGHT_DATA]})
        writes.append(json.loads(request.content))
        return httpx.Response(
            200, json={"errors": [], "data": [{"rid": LIGHT, "rtype": "light"}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        async with Bridge("bridge", "key", http_client=client) as bridge:
            light = await bridge.light(LIGHT)
            assert light.supported_effects == ["no_effect", "candle", "fire"]
            assert light.model_dump()["future_capability"] == {"supported": True}
            await bridge.set_light(
                LIGHT,
                LightState(
                    effect="candle", effect_speed=0.5, xy=(0.5, 0.4), brightness=20
                ),
            )
            await bridge.set_light(LIGHT, LightState(effect="no_effect"))
            with pytest.raises(ValueError, match="not supported"):
                await bridge.set_light(LIGHT, LightState(effect="unknown"))
        assert not client.is_closed
    assert writes == [
        {
            "dimming": {"brightness": 20},
            "effects_v2": {
                "action": {
                    "effect": "candle",
                    "parameters": {"color": {"xy": {"x": 0.5, "y": 0.4}}, "speed": 0.5},
                }
            },
        },
        {"effects_v2": {"action": {"effect": "no_effect"}}},
    ]


async def test_partial_errors_and_connection_reuse() -> None:
    responses = iter(
        [
            {
                "errors": [{"description": "failed key"}],
                "data": [{"rid": LIGHT, "rtype": "light"}],
            },
            {"errors": [], "data": [LIGHT_DATA]},
        ]
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json=next(responses))
        )
    ) as client:
        async with Bridge("bridge", "key", http_client=client) as bridge:
            with pytest.raises(HueAPIError) as caught:
                await bridge.set_light(LIGHT, LightState(on=True))
            assert caught.value.data == [{"rid": LIGHT, "rtype": "light"}]
            assert "key" not in str(caught.value)
            assert (await bridge.light(LIGHT)).metadata.name == "Lamp"


async def test_scene_recall_and_group_routing() -> None:
    seen: list[tuple[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, json.loads(request.content)))
        return httpx.Response(200, json={"errors": [], "data": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        async with Bridge("bridge", "key", http_client=client) as bridge:
            await bridge.recall_scene(
                SCENE, action="dynamic_palette", duration_seconds=2
            )
            await bridge.set_group(LIGHT, LightState(brightness=30))
            with pytest.raises(ValueError, match="individual"):
                await bridge.set_group(LIGHT, LightState(effect="candle"))
    assert seen == [
        (
            f"/clip/v2/resource/scene/{SCENE}",
            {"recall": {"action": "dynamic_palette", "duration": 2000}},
        ),
        (f"/clip/v2/resource/grouped_light/{LIGHT}", {"dimming": {"brightness": 30}}),
    ]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(403),
        httpx.Response(200, json={"unexpected": True}),
        httpx.Response(200, text="not json"),
    ],
)
async def test_invalid_responses_are_safe(response: httpx.Response) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: response)
    ) as client:
        async with Bridge("bridge", "secret", http_client=client) as bridge:
            with pytest.raises(HueConnectionError) as caught:
                await bridge.lights()
            assert "secret" not in str(caught.value)


async def test_lifecycle_and_invalid_ids() -> None:
    bridge = Bridge("bridge", "key")
    with pytest.raises(RuntimeError, match="async with"):
        await bridge.lights()
    async with bridge:
        with pytest.raises(RuntimeError, match="already entered"):
            await bridge.__aenter__()
        with pytest.raises(ValueError):
            await bridge.light("../scene")
    with pytest.raises(RuntimeError):
        await bridge.rooms()
    async with bridge:
        pass


@pytest.mark.parametrize(
    "state",
    [
        {},
        {"brightness": -1},
        {"brightness": float("nan")},
        {"brightness": float("inf")},
        {"xy": (0.9, 0.9)},
        {"xy": (0.2, 0.3), "temperature_kelvin": 3000},
        {"effect_speed": 0.5},
        {"effect": "candle", "transition_seconds": 1},
    ],
)
def test_state_validation(state: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        LightState.model_validate(state)


def test_unit_conversion_and_immutability() -> None:
    state = LightState(
        on=True, brightness=50, temperature_kelvin=2500, transition_seconds=1.5
    )
    before = state.model_dump()
    assert state.to_payload() == {
        "on": {"on": True},
        "dimming": {"brightness": 50},
        "color_temperature": {"mirek": 400},
        "dynamics": {"duration": 1500},
    }
    assert state.model_dump() == before


async def test_all_resources_uses_collection_root() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/clip/v2/resource"
        return httpx.Response(200, json={"errors": [], "data": [LIGHT_DATA]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        async with Bridge("bridge", "key", http_client=client) as bridge:
            assert (await bridge.resources())[0].id == LIGHT
