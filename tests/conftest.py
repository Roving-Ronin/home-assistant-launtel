import asyncio
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


def _ensure_module(name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


# Create base package modules
ha = _ensure_module("homeassistant")
ha.helpers = types.ModuleType("homeassistant.helpers")
ha.components = types.ModuleType("homeassistant.components")
ha.core = types.ModuleType("homeassistant.core")
ha.config_entries = types.ModuleType("homeassistant.config_entries")
ha.data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")
ha.exceptions = types.ModuleType("homeassistant.exceptions")
ha.const = types.ModuleType("homeassistant.const")
ha.helpers.aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
ha.helpers.update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")
ha.helpers.entity_platform = types.ModuleType("homeassistant.helpers.entity_platform")
ha.helpers.device_registry = types.ModuleType("homeassistant.helpers.device_registry")
ha.components.sensor = types.ModuleType("homeassistant.components.sensor")
ha.components.select = types.ModuleType("homeassistant.components.select")
ha.components.button = types.ModuleType("homeassistant.components.button")

vol = types.ModuleType("voluptuous")


class _Schema:
    def __init__(self, schema):
        self.schema = schema

    def __call__(self, data):  # pragma: no cover - not used in tests
        return data


vol.Schema = _Schema
vol.Required = lambda key: key
vol.In = lambda options: options

sys.modules["voluptuous"] = vol

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.modules["homeassistant.helpers"] = ha.helpers
sys.modules["homeassistant.components"] = ha.components
sys.modules["homeassistant.core"] = ha.core
sys.modules["homeassistant.config_entries"] = ha.config_entries
sys.modules["homeassistant.data_entry_flow"] = ha.data_entry_flow
sys.modules["homeassistant.exceptions"] = ha.exceptions
sys.modules["homeassistant.const"] = ha.const
sys.modules["homeassistant.helpers.aiohttp_client"] = ha.helpers.aiohttp_client
sys.modules["homeassistant.helpers.update_coordinator"] = ha.helpers.update_coordinator
sys.modules["homeassistant.helpers.entity_platform"] = ha.helpers.entity_platform
sys.modules["homeassistant.helpers.device_registry"] = ha.helpers.device_registry
sys.modules["homeassistant.components.sensor"] = ha.components.sensor
sys.modules["homeassistant.components.select"] = ha.components.select
sys.modules["homeassistant.components.button"] = ha.components.button


class HomeAssistant:
    def __init__(self):
        self.data: dict[str, Any] = {}
        self.config_entries = types.SimpleNamespace(
            async_forward_entry_setups=lambda entry, platforms: None,
            async_unload_platforms=lambda entry, platforms: True,
        )


ha.core.HomeAssistant = HomeAssistant


class ConfigFlow:
    def __init_subclass__(cls, *, domain: str | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._domain = domain

    def async_show_form(self, *, step_id: str, data_schema=None, errors=None):
        return {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors or {}}

    def async_abort(self, *, reason: str):
        return {"type": "abort", "reason": reason}

    def async_create_entry(self, *, title: str, data: dict[str, Any]):
        return {"type": "create_entry", "title": title, "data": data}

    async def async_set_unique_id(self, unique_id: str):
        self._unique_id = unique_id

    def _abort_if_unique_id_configured(self):
        return None


ha.config_entries.ConfigFlow = ConfigFlow
ha.config_entries.ConfigEntry = object
ha.data_entry_flow.FlowResult = dict


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


class DataUpdateCoordinator:
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
        self.data = await self.update_method()

    def async_set_updated_data(self, data):
        self.data = data


ha.helpers.update_coordinator.CoordinatorEntity = CoordinatorEntity
ha.helpers.update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator


ha.helpers.aiohttp_client.async_get_clientsession = lambda hass: object()

AddEntitiesCallback = Callable[[list], None]
ha.helpers.entity_platform.AddEntitiesCallback = AddEntitiesCallback


@dataclass
class DeviceInfo:
    identifiers: set[tuple[str, str]]
    name: str
    manufacturer: str
    model: str


ha.helpers.device_registry.DeviceInfo = DeviceInfo


class SensorEntity:
    pass


ha.components.sensor.SensorEntity = SensorEntity
ha.components.sensor.SensorDeviceClass = types.SimpleNamespace(MONETARY="monetary")


class SelectEntity:
    pass


ha.components.select.SelectEntity = SelectEntity


class ButtonEntity:
    pass


ha.components.button.ButtonEntity = ButtonEntity


class HomeAssistantError(Exception):
    pass


ha.exceptions.HomeAssistantError = HomeAssistantError

ha.const.CURRENCY_DOLLAR = "$"


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: run test in asyncio event loop")


def pytest_pyfunc_call(pyfuncitem):
    if "asyncio" in pyfuncitem.keywords:
        coro = pyfuncitem.obj(**pyfuncitem.funcargs)
        asyncio.run(coro)
        return True
    return None
