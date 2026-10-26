#!/usr/bin/env python3
# ******************************************************************************
# * @file    tools/registry.py
# * @author  Simeon Marlokov
# * @brief   The only way the model reaches a tool. Unknown names and invalid
# *          arguments become ok=false instead of exceptions.
# * @date    25.10.2026
# ******************************************************************************
from pydantic import ValidationError

from src.integrations.llm.types import ToolCall, ToolSpec
from src.tools.base import Tool, ToolContext, ToolOutcome


class ToolRegistry:
    def __init__(self, tools: list[Tool]):
        self._tools = {tool.name: tool for tool in tools}

    def specs(self) -> list[ToolSpec]:
        specs: list[ToolSpec] = []
        for tool in self._tools.values():
            schema = tool.args_model.model_json_schema()
            schema["additionalProperties"] = False
            specs.append(ToolSpec(name=tool.name, description=tool.description, parameters=schema))
        return specs

    async def execute(self, call: ToolCall, ctx: ToolContext) -> ToolOutcome:
        tool = self._tools.get(call.name)
        if tool is None:
            return ToolOutcome(ok=False, error="unknown tool")
        try:
            args = tool.args_model.model_validate(call.args)
        except ValidationError as exc:
            return ToolOutcome(ok=False, error=exc.errors()[0]["msg"] if exc.errors() else "invalid arguments")
        return await tool.run(args, ctx)
