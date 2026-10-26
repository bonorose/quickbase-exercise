#!/usr/bin/env python3
# ******************************************************************************
# * @file    llm/response.py
# * @author  Simeon Marlokov
# * @brief   LLM stream events, sent as SSE `data:` frames (see core/sse.py).
# *          Order: status* -> delta* -> exactly one of done | error.
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class StreamStatusEvent(BaseModel):
    """Transient progress, e.g. 'model busy, switching…'. Replaced by the next event."""

    type: Literal["status"] = "status"
    message: str


class StreamDeltaEvent(BaseModel):
    type: Literal["delta"] = "delta"
    text: str


class StreamDoneEvent(BaseModel):
    type: Literal["done"] = "done"
    model: str
    text: str


class StreamErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str


StreamEvent = Annotated[
    StreamStatusEvent | StreamDeltaEvent | StreamDoneEvent | StreamErrorEvent,
    Field(discriminator="type"),
]
