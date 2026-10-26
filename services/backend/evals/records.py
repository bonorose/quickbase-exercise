"""In-memory transcript and database snapshots a gate can read."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepRecord:
    kind: str
    status_code: int | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    body: Any = None
    draft_id: str | None = None
    ticket_id: int | None = None
    draft: dict[str, Any] | None = None


@dataclass
class TicketRow:
    id: int
    organization_id: int
    status: int
    priority: int
    title: str
    contents: str


@dataclass
class RunRecord:
    scenario_id: str
    steps: list[StepRecord]
    tickets_before: list[TicketRow]
    tickets_after: list[TicketRow]
    revision_ids_before: list[str]
    revision_ids_after: list[str]
    revisions_after: list[dict[str, Any]]
    drafts_after: list[dict[str, Any]]
    foreign_ticket_ids: set[int]
    foreign_texts: list[str]
    own_ticket_ids: set[int]
    history_text: str
    quota_exhausted: bool = False
    error: str | None = None


@dataclass
class TrialResult:
    scenario_id: str
    passed: bool
    failures: list[str]
    excerpt: str
    quota_exhausted: bool = False


@dataclass
class ScenarioReport:
    scenario_id: str
    trials: int
    passed: int
    failures: list[str]
    excerpt: str
    quota_exhausted: bool = False


@dataclass
class SuiteReport:
    status: str
    trials: int
    live: bool
    scenarios: list[ScenarioReport]

    def markdown(self) -> str:
        lines = [
            "# Adversarial evaluation",
            "",
            f"Status: {self.status}. Live: {self.live}. Trials: {self.trials}.",
            "",
            "A live run of the seven categories at `--trials 3` is about 7 x 3 model calls.",
            "That exceeds the Gemini free tier (20 requests per model per day).",
            "Nightly live runs need a paid key, or `--trials 1`.",
            "",
            "| Scenario | Pass rate | Notes |",
            "|---|---|---|",
        ]
        for scenario in self.scenarios:
            note = "quota exhausted" if scenario.quota_exhausted else "; ".join(scenario.failures[:3])
            lines.append(f"| {scenario.scenario_id} | {scenario.passed}/{scenario.trials} | {note} |")
        lines.append("")
        for scenario in self.scenarios:
            if not scenario.failures and not scenario.excerpt:
                continue
            lines.append(f"## {scenario.scenario_id}")
            for failure in scenario.failures:
                lines.append(f"- {failure}")
            if scenario.excerpt:
                lines.append("")
                lines.append("```")
                lines.append(scenario.excerpt[:1200])
                lines.append("```")
            lines.append("")
        return "\n".join(lines)
