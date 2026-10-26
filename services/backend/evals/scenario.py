"""YAML scenario schema."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class Actor(BaseModel):
    organization: str
    email: str


class ScriptCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ScriptTurnModel(BaseModel):
    text: str = ""
    tool_calls: list[ScriptCall] = Field(default_factory=list)


class StepModel(BaseModel):
    say: str | None = None
    decide: str | None = None
    save: bool = False
    expire: bool = False
    diverge: bool = False
    user: str | None = None
    extra_body: dict[str, Any] | None = None
    from_step: int | None = None


class VariantModel(BaseModel):
    id: str
    live: bool = False
    script: dict[str, ScriptTurnModel] = Field(default_factory=dict)
    steps: list[StepModel]
    gates: list[Any]


class ScenarioFile(BaseModel):
    id: str
    category: str
    actor: Actor
    variants: list[VariantModel]


def load_scenarios(root: Path | None = None) -> list[ScenarioFile]:
    directory = root or Path(__file__).resolve().parent / "scenarios"
    files = sorted(directory.glob("*.yaml"))
    return [ScenarioFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))) for path in files]


def parse_gate(item: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(item, str):
        return item, {}
    if isinstance(item, dict) and len(item) == 1:
        name, value = next(iter(item.items()))
        if isinstance(value, dict):
            return str(name), value
        return str(name), {"value": value}
    raise ValueError(f"Unrecognized gate {item!r}")
