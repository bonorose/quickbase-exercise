#!/usr/bin/env python3
# ******************************************************************************
# * @file    llm_controller.py
# * @author  Simeon Marlokov
# * @brief   LLM controller: provider events -> stream event schemas -> SSE
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse
from loguru import logger

from src.core.sse import sse_response
from src.integrations.llm import Completed, LLMError, LLMEvent, Notice, TextDelta
from src.schemas.llm.request import LLMStreamRequest
from src.schemas.llm.response import (
    StreamDeltaEvent,
    StreamDoneEvent,
    StreamErrorEvent,
    StreamEvent,
    StreamStatusEvent,
)
from src.services.llm_service import LLMService


class LLMController:
    def __init__(self, service: LLMService):
        self.service = service

    def stream(self, request: LLMStreamRequest) -> StreamingResponse:
        return sse_response(self._to_stream_events(self.service.stream_completion(request.prompt)))

    @staticmethod
    async def _to_stream_events(events: AsyncIterator[LLMEvent]) -> AsyncIterator[StreamEvent]:
        # Once streaming has started the status code is already 200, so failures become an error event
        try:
            async for event in events:
                match event:
                    case Notice(message=message):
                        yield StreamStatusEvent(message=message)
                    case TextDelta(text=text):
                        yield StreamDeltaEvent(text=text)
                    case Completed(text=text, model=model):
                        yield StreamDoneEvent(text=text, model=model)
        except LLMError as exc:
            logger.warning(f"LLM stream failed: {exc}")
            yield StreamErrorEvent(message=str(exc))
        except Exception:
            logger.exception("Unexpected error while streaming")
            yield StreamErrorEvent(message="Unexpected error while generating the response.")
