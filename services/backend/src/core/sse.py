#!/usr/bin/env python3
# ******************************************************************************
# * @file    sse.py
# * @author  Simeon Marlokov
# * @brief   Server-Sent Events transport: one `data: <json>` frame per event
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse
from pydantic import BaseModel


def sse_response(events: AsyncIterator[BaseModel]) -> StreamingResponse:
    async def frames() -> AsyncIterator[str]:
        async for event in events:
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        frames(),
        media_type="text/event-stream",
        # no-cache: never buffer/replay; X-Accel-Buffering: tell nginx-style proxies not to buffer
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
