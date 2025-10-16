import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from custom_components.launtel.button import LauntelRefreshButton


class DummyCoordinator(SimpleNamespace):
    async def async_request_refresh(self):
        self.called = True


def _make_entry():
    return SimpleNamespace(data={"service_id": 99}, title="Service")


@pytest.mark.asyncio
async def test_refresh_button_triggers_refresh():
    coordinator = DummyCoordinator(data={"service": SimpleNamespace(title="Service")})
    coordinator.called = False
    button = LauntelRefreshButton(coordinator, _make_entry())

    await button.async_press()

    assert coordinator.called is True
