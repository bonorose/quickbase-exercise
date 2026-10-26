#!/usr/bin/env python3
# ******************************************************************************
# * @file    llm.py
# * @author  Simeon Marlokov
# * @brief   LLM routes
# * @date    25.10.2026
# ******************************************************************************
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from src.core.config import get_settings
from src.core.exceptions import NotFoundError
from src.dependencies.llm import LLMControllerDep
from src.schemas.common.response import ErrorResponse
from src.schemas.llm.request import LLMStreamRequest

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post(
    "/stream",
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {
            "content": {"text/event-stream": {}},
            "description": "SSE stream of `data: <StreamEvent JSON>` frames: status* -> delta* -> done | error",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse, "description": "No GEMINI_API_KEY configured"},
    },
)
async def stream(request: LLMStreamRequest, controller: LLMControllerDep):
    if get_settings().app_env == "production":
        raise NotFoundError("Not found")
    return controller.stream(request)
