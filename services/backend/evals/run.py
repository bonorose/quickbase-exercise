"""CLI: python -m evals.run [--scenario id] [--trials N] [--live]."""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from evals.records import ScenarioReport, SuiteReport
from evals.scenario import ScenarioFile, load_scenarios

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run adversarial evaluations against the agent.")
    parser.add_argument("--scenario", help="Scenario id, or id/variant")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--live", action="store_true", help="Call Gemini. Requires GEMINI_API_KEY.")
    return parser.parse_args()


def _selected(scenarios: list[ScenarioFile], scenario_id: str | None, *, live: bool):
    chosen = []
    for scenario in scenarios:
        if scenario_id and scenario.id != scenario_id and not scenario_id.startswith(f"{scenario.id}/"):
            continue
        for variant in scenario.variants:
            label = f"{scenario.id}/{variant.id}"
            if scenario_id and scenario_id not in {scenario.id, label}:
                continue
            if live and not variant.live:
                continue
            if not live and not variant.script:
                continue
            chosen.append((scenario, variant))
    return chosen


async def _run(args: argparse.Namespace) -> SuiteReport:
    from evals.runner import SuiteRunner, relax_rate_limits
    from src.main import app
    from src.seed.run import seed

    relax_rate_limits()
    await seed(reset=True)
    import httpx
    from sqlalchemy.ext.asyncio import create_async_engine

    from src.core.config import get_settings

    engine = create_async_engine(get_settings().migration_database_url)
    scenarios = _selected(load_scenarios(), args.scenario, live=args.live)
    reports: list[ScenarioReport] = []
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            runner = SuiteRunner(client, engine, app)
            for scenario, variant in scenarios:
                failures: list[str] = []
                excerpt = ""
                passed = 0
                quota = False
                for _ in range(args.trials):
                    trial = await runner.run_variant(
                        scenario.id, scenario.actor.organization, scenario.actor.email, variant, live=args.live
                    )
                    excerpt = trial.excerpt
                    quota = quota or trial.quota_exhausted
                    if trial.passed and not trial.quota_exhausted:
                        passed += 1
                    elif trial.quota_exhausted:
                        pass
                    else:
                        failures.extend(trial.failures)
                reports.append(
                    ScenarioReport(f"{scenario.id}/{variant.id}", args.trials, passed, failures, excerpt, quota)
                )
    finally:
        await engine.dispose()
    if any(item.failures for item in reports):
        status = "failed"
    elif any(item.quota_exhausted for item in reports):
        status = "quota_exhausted"
    else:
        status = "passed"
    return SuiteReport(status, args.trials, args.live, reports)


def _prepare_database() -> None:
    from testcontainers.postgres import PostgresContainer

    os.environ.setdefault("JWT_SECRET_KEY", "eval-secret-eval-secret-eval-secret")
    os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
    os.environ.setdefault("APP_ENV", "local")
    os.environ.setdefault("SEED_USER_PASSWORD", "admin123")
    os.environ.setdefault("POSTGRES_APP_USER", "qai_app")
    os.environ.setdefault("POSTGRES_APP_PASSWORD", "qai-app-password")
    os.environ["LLM_PROVIDER"] = "gemini" if "--live" in sys.argv else "fake"
    with PostgresContainer(
        "postgres:17-alpine", username="quickbase", password="quickbase", dbname="quickbase"
    ) as postgres:
        os.environ["POSTGRES_USER"] = postgres.username
        os.environ["POSTGRES_PASSWORD"] = postgres.password
        os.environ["POSTGRES_DB"] = postgres.dbname
        os.environ["POSTGRES_HOST"] = postgres.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
        from src.core.config import get_settings
        from src.db.session import get_engine, get_session_factory

        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND_ROOT, check=True, env=os.environ.copy()
        )
        args = _parse()
        report = asyncio.run(_run(args))
        out = BACKEND_ROOT / "evals" / "out"
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(report.markdown(), encoding="utf-8")
        (out / "report.json").write_text(
            json.dumps(
                {
                    "status": report.status,
                    "trials": report.trials,
                    "live": report.live,
                    "scenarios": [item.__dict__ for item in report.scenarios],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(report.markdown())
        if report.status == "quota_exhausted":
            print("::notice::Evaluation quota exhausted; result is neutral")
            raise SystemExit(0)
        if report.status != "passed":
            raise SystemExit(1)


def main() -> None:
    if "--live" in sys.argv and not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is required for --live", file=sys.stderr)
        raise SystemExit(2)
    _prepare_database()


if __name__ == "__main__":
    main()
