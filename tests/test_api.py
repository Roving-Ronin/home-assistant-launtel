import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.launtel.api import LauntelClient, LauntelService


class DummyResponse:
    def __init__(self, *, status: int = 200, text: str = "", raise_for_status: bool = False):
        self.status = status
        self._text = text
        self.raise_for_status = Mock()
        if raise_for_status:
            self.raise_for_status.side_effect = RuntimeError("boom")

    async def text(self):
        return self._text


@pytest.mark.asyncio
async def test_async_login_success(monkeypatch):
    session = AsyncMock()
    resp = DummyResponse(status=200, text="logged in")
    session.post.return_value = resp
    client = LauntelClient(session, "user", "pass")

    await client.async_login()

    session.post.assert_awaited_once()
    assert client._logged_in


@pytest.mark.asyncio
async def test_async_login_failure(monkeypatch):
    session = AsyncMock()
    resp = DummyResponse(status=200, text='<input name="username">')
    session.post.return_value = resp
    client = LauntelClient(session, "user", "pass")

    with pytest.raises(RuntimeError):
        await client.async_login()

    session.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_get_services_parses_cards(monkeypatch):
    session = AsyncMock()
    services_html = """
    <div class="service-card" id="svc-123">
      <span class="service-title-txt">My Fibre</span>
      <a href="/charts?foo=1&userid=abc123"><i class="fa-bar-chart"></i></a>
      <button onclick="pauseService(456)"></button>
      <dt>Technology / Speed Tier</dt>
      <dd>Fibre 250 / 100 Mbps</dd>
      <dt>Status</dt>
      <dd><span>Change in progress</span></dd>
    </div>
    """
    session.get.return_value = DummyResponse(text=services_html)

    client = LauntelClient(session, "user", "pass")
    client._logged_in = True

    services = await client.async_get_services()

    assert services == [
        LauntelService(
            title="My Fibre",
            service_id=456,
            avcid="svc-123",
            user_id="abc123",
            speed_label="Fibre 250 / 100 Mbps",
            change_in_progress=True,
        )
    ]


@pytest.mark.asyncio
async def test_async_get_plan_options(monkeypatch):
    session = AsyncMock()
    html = """
    <input name="psid" value="1001">
    <span class="list-group-item" data-value="1001" data-plancharge="2.5">
      <div class="row"><div class="col-8">Fibre (250/100) Unlimited</div></div>
    </span>
    <span class="list-group-item" data-value="1002" data-plancharge="1.5">Basic 25/5</span>
    <input name="locid" value="loc-55">
    """
    session.get.return_value = DummyResponse(text=html)

    client = LauntelClient(session, "user", "pass")
    client._logged_in = True

    options, label_to_psid, current_label, locid, plans_mapping = await client.async_get_plan_options("svc-123")

    assert options == ["Fibre (250/100) Unlimited", "Basic 25/5"]
    assert label_to_psid["Fibre (250/100) Unlimited"] == 1001
    assert current_label == "Fibre (250/100) Unlimited"
    assert locid == "loc-55"
    assert plans_mapping[1001]["price_per_day"] == 2.5
    assert plans_mapping[1001]["unlimited"] is True
    assert plans_mapping[1001]["speed"] == "250/100"


@pytest.mark.asyncio
async def test_async_change_plan(monkeypatch):
    session = AsyncMock()
    get_resp = DummyResponse(text="ok")
    post_resp = DummyResponse(text="done")
    session.get.return_value = get_resp
    session.post.return_value = post_resp

    client = LauntelClient(session, "user", "pass")
    client._logged_in = True

    await client.async_change_plan("uid", 10, 5, "avc", "loc")

    session.get.assert_awaited()
    session.post.assert_awaited()


@pytest.mark.asyncio
async def test_async_get_balance(monkeypatch):
    session = AsyncMock()
    html = """
    <dt>Current Balance</dt>
    <dd><span>+$112.65</span></dd>
    """
    session.get.return_value = DummyResponse(text=html)

    client = LauntelClient(session, "user", "pass")
    client._logged_in = True

    balance = await client.async_get_balance()

    assert balance == 112.65


@pytest.mark.asyncio
async def test_async_get_estimated_days_remaining(monkeypatch):
    session = AsyncMock()
    html = """
    <dt>Estimated Days Remaining</dt>
    <dd><span class="text-success">27</span></dd>
    """
    session.get.return_value = DummyResponse(text=html)

    client = LauntelClient(session, "user", "pass")
    client._logged_in = True

    days = await client.async_get_estimated_days_remaining()

    assert days == 27
