#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/chat.py
# * @author  Simeon Marlokov
# * @brief   Chat wiring: organization session, LLM client, agent limits.
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends

from src.controllers.chat_controller import ChatController
from src.core.config import get_settings
from src.dependencies.database import SessionDep
from src.dependencies.llm import LLMClientDep
from src.dependencies.organizations import OrganizationDep
from src.repositories.chat_message_repository import ChatMessageRepository
from src.repositories.chat_session_repository import ChatSessionRepository
from src.services.chat_service import ChatService


def get_chat_controller(session: SessionDep, organization: OrganizationDep, client: LLMClientDep) -> ChatController:
    settings = get_settings()
    service = ChatService(
        ChatSessionRepository(session, organization),
        ChatMessageRepository(session, organization),
        client,
        max_iterations=settings.agent_max_tool_iterations,
        history_limit=settings.agent_history_max_messages,
    )
    return ChatController(service)


ChatControllerDep = Annotated[ChatController, Depends(get_chat_controller)]
