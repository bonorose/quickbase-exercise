#!/usr/bin/env python3
# ******************************************************************************
# * @file    tools/base.py
# * @author  Simeon Marlokov
# * @brief   Tool contract. Context is built by the agent, never from model output.
# * @date    25.10.2026
# ******************************************************************************
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.organization import OrganizationContext


class ToolArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


@dataclass
class ToolContext:
    organization: OrganizationContext
    session_id: uuid.UUID
    db: AsyncSession
    turn_tainted: bool = False


@dataclass(frozen=True)
class ToolOutcome:
    ok: bool
    result: dict | None = None
    error: str | None = None
    summary: dict | None = None
    pending_revision: dict | None = None
    # The result carries untrusted ticket text. Persisted so later turns stay tainted.
    untrusted: bool = False


class Tool(ABC):
    name: str
    description: str
    args_model: type[ToolArgs]
    kind: Literal["read", "mutate"]

    @abstractmethod
    async def run(self, args: ToolArgs, ctx: ToolContext) -> ToolOutcome: ...
