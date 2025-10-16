import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from typer.testing import CliRunner

from custom_components.launtel import api
from launtel_cli import app


runner = CliRunner()


class DummySession:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


class DummyClient(SimpleNamespace):
    pass


@pytest.fixture(autouse=True)
def patch_run(monkeypatch):
    def _run(coro):
        return asyncio.run(coro)

    monkeypatch.setattr("launtel_cli._run", _run)


def test_services_command(monkeypatch):
    client = DummyClient()
    client.async_get_services = AsyncMock(return_value=[
        api.LauntelService(title="Svc", service_id=1, avcid="avc", user_id="user", speed_label="Speed", change_in_progress=False)
    ])
    session = DummySession()

    async def _get_client(username, password):
        return client, session

    monkeypatch.setattr("launtel_cli._get_client", _get_client)

    result = runner.invoke(app, ["services", "--username", "user", "--password", "pass"])

    assert result.exit_code == 0
    assert "service_id=1" in result.stdout
    assert session.closed is True


def test_plans_command(monkeypatch):
    client = DummyClient()
    client.async_get_services = AsyncMock(return_value=[
        api.LauntelService(title="Svc", service_id=1, avcid="avc", user_id="user", speed_label="Speed", change_in_progress=False)
    ])
    client.async_get_plan_options = AsyncMock(return_value=(
        ["Plan"], {"Plan": 10}, "Plan", "loc", {10: {"price_per_day": 2.5, "speed": "250/100", "unlimited": True}}
    ))
    session = DummySession()

    async def _get_client(username, password):
        return client, session

    monkeypatch.setattr("launtel_cli._get_client", _get_client)

    result = runner.invoke(app, [
        "plans",
        "--username",
        "user",
        "--password",
        "pass",
        "--service-id",
        "1",
    ])

    assert result.exit_code == 0
    assert "Current plan: Plan" in result.stdout


def test_change_plan_command(monkeypatch):
    client = DummyClient()
    client.async_get_services = AsyncMock(return_value=[
        api.LauntelService(title="Svc", service_id=1, avcid="avc", user_id="user", speed_label="Speed", change_in_progress=False)
    ])
    client.async_get_plan_options = AsyncMock(return_value=(
        ["Plan"], {"Plan": 10}, "Plan", "loc", {}
    ))
    client.async_change_plan = AsyncMock()
    session = DummySession()

    async def _get_client(username, password):
        return client, session

    monkeypatch.setattr("launtel_cli._get_client", _get_client)

    result = runner.invoke(app, [
        "change-plan",
        "--username",
        "user",
        "--password",
        "pass",
        "--service-id",
        "1",
        "--label",
        "Plan",
    ])

    assert result.exit_code == 0
    client.async_change_plan.assert_awaited()
