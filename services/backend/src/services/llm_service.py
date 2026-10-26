#!/usr/bin/env python3
# ******************************************************************************
# * @file    llm_service.py
# * @author  Simeon Marlokov
# * @brief   LLM business logic: availability check and completion streaming
# * @date    25.10.2026
# ******************************************************************************
from collections.abc import AsyncIterator

from src.core.exceptions import ServiceUnavailableError
from src.integrations.llm import LLMClient, LLMEvent, LLMMessage


class LLMService:
    def __init__(self, client: LLMClient | None):
        self.client = client

    def stream_completion(self, prompt: str) -> AsyncIterator[LLMEvent]:
        """Not a generator on purpose: the availability check runs before the response starts,
        so a missing key is a real HTTP 503 rather than an error inside a 200 stream."""
        if self.client is None:
            raise ServiceUnavailableError("The LLM is not configured. Set GEMINI_API_KEY in .env.")
        return self.client.stream([LLMMessage(role="user", text=prompt)])
