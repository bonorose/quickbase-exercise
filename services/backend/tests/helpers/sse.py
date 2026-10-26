import json

import httpx


async def read_events(response: httpx.Response) -> list[dict]:
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line.removeprefix("data: ")))
    return events
