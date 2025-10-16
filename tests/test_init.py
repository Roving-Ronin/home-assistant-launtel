from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.launtel.api import LauntelService

launtel_init = import_module("custom_components.launtel.__init__")


class DummyCoordinator:
    def __init__(self, hass, logger, name, update_method, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_method = update_method
        self.update_interval = update_interval
        self.data = {}
        self.last_update_success = True

    async def async_config_entry_first_refresh(self):
        self.data = await self.update_method()

    async def async_request_refresh(self):
        await self.update_method()

    def async_set_updated_data(self, data):
        self.data = data


class FakeConfigEntries:
    def __init__(self):
        self.forwarded = []
        self.unloaded = []

    async def async_forward_entry_setups(self, entry, platforms):
        self.forwarded.append((entry, tuple(platforms)))

    async def async_unload_platforms(self, entry, platforms):
        self.unloaded.append((entry, tuple(platforms)))
        return True


class FakeEntry:
    def __init__(self):
        self.entry_id = "entry1"
        self.title = "My Service"
        self.data = {
            "username": "user",
            "password": "pass",
            "service_id": 123,
            "avcid": "avc1",
            "user_id": "user123",
        }


@pytest.mark.asyncio
async def test_async_setup_entry(monkeypatch):
    hass = SimpleNamespace()
    hass.data = {}
    hass.config_entries = FakeConfigEntries()

    fake_client = MagicMock()
    fake_client.async_get_services = AsyncMock(return_value=[
        LauntelService(title="My Service", service_id=123, avcid="avc1", user_id="user123", speed_label="Speed", change_in_progress=False)
    ])
    fake_client.async_get_balance = AsyncMock(return_value=50.5)
    fake_client.async_get_estimated_days_remaining = AsyncMock(return_value=10)
    fake_client.async_get_plan_options = AsyncMock(return_value=(
        ["Option A"], {"Option A": 99}, "Option A", "loc", {99: {"label": "Option A", "price_per_day": 2.5, "unlimited": True, "speed": "250/100", "first_col": "col"}}
    ))

    session = object()

    monkeypatch.setattr(launtel_init, "async_get_clientsession", lambda hass: session)
    monkeypatch.setattr(launtel_init, "LauntelClient", lambda *args, **kwargs: fake_client)
    monkeypatch.setattr(launtel_init, "DataUpdateCoordinator", DummyCoordinator)

    entry = FakeEntry()

    result = await launtel_init.async_setup_entry(hass, entry)

    assert result is True
    assert hass.data[launtel_init.DOMAIN][entry.entry_id]["client"] is fake_client
    coordinator = hass.data[launtel_init.DOMAIN][entry.entry_id]["coordinator"]
    assert coordinator.data["current_label"] == "Option A"
    assert hass.config_entries.forwarded[0][1] == tuple(launtel_init.PLATFORMS)


@pytest.mark.asyncio
async def test_async_unload_entry():
    hass = SimpleNamespace()
    hass.data = {launtel_init.DOMAIN: {"entry1": {}}}
    hass.config_entries = FakeConfigEntries()
    entry = FakeEntry()

    result = await launtel_init.async_unload_entry(hass, entry)

    assert result is True
    assert entry.entry_id not in hass.data.get(launtel_init.DOMAIN, {})
    assert hass.config_entries.unloaded[0][1] == tuple(launtel_init.PLATFORMS)
