# phue2 — Philips Hue V2 SDK

An asynchronous Python client for the local Hue V2 API. The first-major alpha
focuses on lights, rooms, saved scenes and native effects, with typed resources
that retain unknown fields as Hue adds capabilities.

## Install

```bash
uv add 'phue2==1.0.0a1'
```

Python 3.10 or newer is required. This is a breaking prerelease. The previous
synchronous Hue V1 library remains on the [`release/0.x`](https://github.com/zzstoatzz/phue/tree/release/0.x)
branch and remains installable with `phue2<1` (without opting into prereleases).

## Discover and control

Use your existing bridge application key. Nothing is written to a credential
file. Open one bridge context for the lifetime of your application:

```python
import asyncio
import os
from phue import Bridge, LightState

async def main():
    async with Bridge(
        os.environ["HUE_BRIDGE_IP"],
        os.environ["HUE_BRIDGE_USERNAME"],
    ) as bridge:
        lights = await bridge.lights()
        for light in lights:
            print(light.id, light.metadata.name, light.supported_effects)

        # Choose an ID from discovery; this changes a real light.
        light = lights[0]
        await bridge.set_light(light.id, LightState(on=True, brightness=30))
        print((await bridge.light(light.id)).model_dump())

asyncio.run(main())
```

TLS verification is enabled by default. For bridges with a private certificate,
pass `verify=ssl_context` with a context that trusts your bridge. For a deliberately
pinned bridge certificate, load its PEM into an `ssl.SSLContext`, enable
`ssl.VERIFY_X509_PARTIAL_CHAIN`, and disable hostname matching only if the certificate
uses the bridge identity rather than its IP address. Obtain and verify that
certificate through a trusted local setup process. `verify=False` is available
for explicit diagnostics, not required by the SDK. Never publish an application key.

An optional `http_client=httpx.AsyncClient(...)` remains caller-owned; the bridge
will not close it. Its owner configures TLS and timeouts. Otherwise the bridge
creates and closes its own pooled client. Calls outside an `async with` block are
rejected. Nested entry of the same bridge is rejected; a closed owned context can
be entered again.

## Native effects and scenes

`LightState` uses brightness percent, temperature in kelvin, CIE xy coordinates,
and transition seconds. Omitted fields remain unchanged. Normal state changes do
not imply `on=True`. An effect uses its own optional speed between zero and one;
it cannot be combined with a normal transition duration.

```python
from phue import Bridge, LightState

async def candle(bridge: Bridge, light_id: str):
    # Only effects advertised by this bulb are accepted.
    await bridge.set_light(
        light_id,
        LightState(effect="candle", effect_speed=0.5, brightness=20),
    )

async def stop_effect(bridge: Bridge, light_id: str):
    await bridge.set_light(light_id, LightState(effect="no_effect"))
```

Effect names come from bridge discovery rather than a fixed enum. This alpha
requires the newer `effects_v2` feature when applying effects. It does not fall
back to the deprecated effects representation. Per-light support is checked
before a write. Color or temperature supplied with an active effect is sent as
an effect parameter.

`await bridge.scenes()` exposes full scene actions and palettes. Recall a scene
with `await bridge.recall_scene(scene_id)`, or request its dynamic palette with
`action="dynamic_palette"` where supported by the bridge. The SDK does not emulate
flicker by repeatedly sending brightness commands.

Rooms refer to devices through `children` and to grouped-light services through
`services`. Light `owner` references identify their device. Use the room's
`grouped_light` service ID with `set_group`; a room ID is not a grouped-light ID.
Native effects target individual lights. `resources()` exposes the full inventory
for joining these relationships and reading connectivity data.

## Errors

`HueAPIError` retains the bridge's `errors` and any returned `data`, including
acknowledged resources in a partially successful response. `HueConnectionError`
covers transport, HTTP and malformed-envelope failures. Both subclass `HueError`.
An acknowledgement is not physical verification; read state after a transition.
The SDK does not retry writes automatically.

## Migrating from 0.x

- `Bridge(ip=..., username=...)` becomes asynchronous `Bridge(host, application_key)`.
- V1 numeric IDs become V2 resource IDs. The bridge-provided `id_v1` can help map
  existing lights; rediscover rooms and their grouped-light service references.
- `get_light()` becomes `lights()`; `get_light(id)` becomes `light(id)`.
- `set_light(id, "bri", 127)` becomes `set_light(id, LightState(brightness=50))`.
- Group names and scene names are resolved by the application, not guessed by the SDK.
- V1 object properties, sensors/schedules APIs, and the old CLI are not part of this
  initial alpha. Event subscriptions and entertainment streaming are not implemented.

This release intentionally covers the smart-home example's V2 workflows first.
It does not claim parity with the full V1 SDK or the entire Hue API.

## Development

```bash
uv sync
uv run pytest
uv run pre-commit run --all-files
```

## Acknowledgments and license

This project grew from [phue](https://github.com/studioimaginaire/phue) by Nathanaël
Lécaudé and earlier protocol work by rsmck. Nathan Nowack maintained the modernized
fork and the V2 rewrite. MIT license; see LICENSE. Philips Hue is a trademark of
Koninklijke Philips N.V.; this project is not affiliated with Philips or Signify.
