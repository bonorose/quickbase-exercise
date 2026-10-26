#!/usr/bin/env python3
# ******************************************************************************
# * @file    chat.py
# * @author  Simeon Marlokov
# * @brief   Chat routes (C-05, C-06, C-07, C-08)
# * @date    25.10.2026
# ******************************************************************************
import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from src.dependencies.chat import ChatControllerDep
from src.schemas.chat.request import CreateSessionRequest, SendMessageRequest, SessionListQuery
from src.schemas.chat.response import ChatSessionDetailResponse, ChatSessionListResponse, ChatSessionResponse
from src.schemas.common.response import ErrorResponse

router = APIRouter(prefix="/chat/sessions", tags=["chat"])


@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest, controller: ChatControllerDep):
    return await controller.create_session(request)


@router.get("", response_model=ChatSessionListResponse)
async def list_sessions(controller: ChatControllerDep, query: Annotated[SessionListQuery, Query()]):
    return await controller.list_sessions(query)


@router.get(
    "/{session_id}",
    response_model=ChatSessionDetailResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
async def get_session(session_id: uuid.UUID, controller: ChatControllerDep):
    return await controller.get_session(session_id)


@router.post(
    "/{session_id}/messages",
    response_class=StreamingResponse,
    responses={
        status.HTTP_200_OK: {"content": {"text/event-stream": {}}, "description": "C-20 event stream"},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
async def send_message(session_id: uuid.UUID, request: SendMessageRequest, controller: ChatControllerDep):
    return await controller.send_message(session_id, request)
