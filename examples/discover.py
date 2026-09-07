"""Read Hue V2 resources using environment-provided bridge credentials."""

import asyncio
import os

from phue import Bridge


async def main() -> None:
    async with Bridge(
        os.environ["HUE_BRIDGE_IP"], os.environ["HUE_BRIDGE_USERNAME"]
    ) as bridge:
        for room in await bridge.rooms():
            print(room.metadata.name, room.id)
        for light in await bridge.lights():
            print(light.metadata.name, light.supported_effects)
        for scene in await bridge.scenes():
            print(scene.metadata.name, scene.group, scene.actions)


if __name__ == "__main__":
    asyncio.run(main())
