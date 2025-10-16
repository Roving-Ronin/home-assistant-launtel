import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.exceptions import HomeAssistantError

from custom_components.launtel.select import LauntelPlanSelect


class DummyCoordinator(SimpleNamespace):
    def __init__(self, data):
        super().__init__(data=data)

    async def async_request_refresh(self):
        self.data.setdefault("refresh_called", 0)
        self.data["refresh_called"] += 1

    def async_set_updated_data(self, data):
        self.data = data


def _make_entry():
    return SimpleNamespace(data={"service_id": 1}, title="Service")


def _make_client():
    client = SimpleNamespace()
    client.async_change_plan = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_select_option_success():
    coordinator = DummyCoordinator(
        {
            "service": SimpleNamespace(title="Service"),
            "change_in_progress": False,
            "options": ["Plan A"],
            "label_to_psid": {"Plan A": 10},
            "user_id": "uid",
            "service_id": 5,
            "avcid": "avc",
            "locid": "loc",
        }
    )
    select = LauntelPlanSelect(coordinator, _make_client(), _make_entry())

    await select.async_select_option("Plan A")

    assert select.coordinator.data["change_in_progress"] is True
    select._client.async_change_plan.assert_awaited_once_with("uid", 10, 5, "avc", "loc")


@pytest.mark.asyncio
async def test_select_option_requires_availability():
    coordinator = DummyCoordinator(
        {
            "service": SimpleNamespace(title="Service"),
            "change_in_progress": True,
        }
    )
    select = LauntelPlanSelect(coordinator, _make_client(), _make_entry())

    with pytest.raises(HomeAssistantError):
        await select.async_select_option("Plan A")


@pytest.mark.asyncio
async def test_select_option_fetches_locid():
    coordinator = DummyCoordinator(
        {
            "service": SimpleNamespace(title="Service"),
            "change_in_progress": False,
            "options": ["Plan A"],
            "label_to_psid": {"Plan A": 10},
            "user_id": "uid",
            "service_id": 5,
            "avcid": "avc",
            "locid": None,
        }
    )
    client = _make_client()
    select = LauntelPlanSelect(coordinator, client, _make_entry())

    async def _refresh():
        coordinator.data.setdefault("refresh_called", 0)
        coordinator.data["refresh_called"] += 1
        coordinator.data["locid"] = "loc"

    coordinator.async_request_refresh = AsyncMock(side_effect=_refresh)

    await select.async_select_option("Plan A")

    client.async_change_plan.assert_awaited_once_with("uid", 10, 5, "avc", "loc")
    assert coordinator.async_request_refresh.await_count >= 1
