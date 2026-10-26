#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/llm.py
# * @author  Simeon Marlokov
# * @brief   LLM wiring: LLMClient (Gemini) -> LLMService -> LLMController
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends

from src.controllers.llm_controller import LLMController
from src.integrations.llm import LLMClient, get_llm_client
from src.services.llm_service import LLMService

LLMClientDep = Annotated[LLMClient | None, Depends(get_llm_client)]


def get_llm_controller(client: LLMClientDep) -> LLMController:
    return LLMController(LLMService(client))


LLMControllerDep = Annotated[LLMController, Depends(get_llm_controller)]
