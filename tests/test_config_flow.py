from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.launtel import config_flow
from custom_components.launtel.api import LauntelService


class DummyHass(SimpleNamespace):
    pass


@pytest.mark.asyncio
async def test_user_step_success(monkeypatch):
    hass = DummyHass()
    session = object()
    fake_client = SimpleNamespace()
    fake_client.async_login = AsyncMock()
    fake_client.async_get_services = AsyncMock(return_value=[
        LauntelService(title="Svc", service_id=1, avcid="avc", user_id="user", speed_label="Speed", change_in_progress=False)
    ])

    monkeypatch.setattr(config_flow, "async_get_clientsession", lambda hass: session)
    monkeypatch.setattr(config_flow, "LauntelClient", lambda *args, **kwargs: fake_client)

    flow = config_flow.LauntelConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user({"username": "user", "password": "pass"})

    assert result["type"] == "form"
    assert result["step_id"] == "select_service"
    assert flow._services


@pytest.mark.asyncio
async def test_user_step_no_services(monkeypatch):
    hass = DummyHass()
    fake_client = SimpleNamespace()
    fake_client.async_login = AsyncMock()
    fake_client.async_get_services = AsyncMock(return_value=[])

    monkeypatch.setattr(config_flow, "async_get_clientsession", lambda hass: object())
    monkeypatch.setattr(config_flow, "LauntelClient", lambda *args, **kwargs: fake_client)

    flow = config_flow.LauntelConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user({"username": "user", "password": "pass"})

    assert result["type"] == "form"
    assert result["errors"]["base"] == "no_services"


@pytest.mark.asyncio
async def test_select_service_creates_entry(monkeypatch):
    flow = config_flow.LauntelConfigFlow()
    flow.hass = DummyHass()
    flow._username = "user"
    flow._password = "pass"
    flow._services = [
        LauntelService(title="Svc", service_id=1, avcid="avc", user_id="user", speed_label="Speed", change_in_progress=False)
    ]

    result = await flow.async_step_select_service({"service_id": 1})

    assert result["type"] == "create_entry"
    assert result["title"] == "Svc"
    assert result["data"]["service_id"] == 1
