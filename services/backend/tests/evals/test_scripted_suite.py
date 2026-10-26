import pytest

from evals.runner import SuiteRunner
from evals.scenario import load_scenarios
from src.core.config import get_settings
from src.core.rate_limit import get_rate_limiter
from src.integrations.llm import get_llm_client
from src.seed.run import seed

pytestmark = pytest.mark.api


async def test_scripted_scenarios_pass(client, owner_engine, app, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_USER_PER_MINUTE", "10000")
    monkeypatch.setenv("RATE_LIMIT_ORGANIZATION_PER_MINUTE", "10000")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_EMAIL", "10000")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_IP", "10000")
    get_settings.cache_clear()
    get_rate_limiter().reset()
    await seed(reset=True)
    runner = SuiteRunner(client, owner_engine, app)
    failures = []
    try:
        for scenario in load_scenarios():
            for variant in scenario.variants:
                if not variant.script:
                    continue
                trial = await runner.run_variant(
                    scenario.id,
                    scenario.actor.organization,
                    scenario.actor.email,
                    variant,
                    live=False,
                )
                if not trial.passed:
                    failures.append(f"{trial.scenario_id}: {trial.failures} {trial.excerpt}")
    finally:
        app.dependency_overrides.pop(get_llm_client, None)
    assert not failures, "\n".join(failures)
