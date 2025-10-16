from types import SimpleNamespace

from custom_components.launtel.sensor import (
    LauntelBalanceSensor,
    LauntelCurrentPlanSensor,
    LauntelEstimatedDaysRemainingSensor,
)


class DummyCoordinator(SimpleNamespace):
    def __init__(self, data):
        super().__init__(data=data, last_update_success=True)


class DummyEntry(SimpleNamespace):
    pass


def _make_entry():
    return DummyEntry(data={"service_id": 123}, title="Service Title")


def test_current_plan_sensor_properties():
    coordinator = DummyCoordinator(
        {
            "service": SimpleNamespace(title="Service Title"),
            "change_in_progress": False,
            "current_label": "Plan A",
            "label_to_psid": {"Plan A": 1},
            "plans_mapping": {1: {"label": "Plan A", "price_per_day": 2.5, "unlimited": True, "speed": "250/100"}},
            "options": ["Plan A"],
            "service_speed_label": "Speed",
        }
    )
    entry = _make_entry()
    sensor = LauntelCurrentPlanSensor(coordinator, entry)

    assert sensor.native_value == "Plan A"
    attrs = sensor.extra_state_attributes
    assert attrs["current_price_per_day"] == 2.5
    assert attrs["plans"]["1"]["label"] == "Plan A"

    coordinator.data["change_in_progress"] = True
    assert sensor.native_value == "Change in progress"


def test_balance_sensor_attributes():
    coordinator = DummyCoordinator(
        {
            "service": SimpleNamespace(title="Service Title"),
            "account_balance": -12.34,
        }
    )
    entry = _make_entry()
    sensor = LauntelBalanceSensor(coordinator, entry)

    assert sensor.native_value == -12.34
    attrs = sensor.extra_state_attributes
    assert attrs["balance_status"] == "debt"
    assert attrs["formatted_balance"] == "$12.34"


def test_days_remaining_sensor_attributes():
    coordinator = DummyCoordinator(
        {
            "service": SimpleNamespace(title="Service Title"),
            "estimated_days_remaining": 5,
        }
    )
    entry = _make_entry()
    sensor = LauntelEstimatedDaysRemainingSensor(coordinator, entry)

    assert sensor.native_value == 5
    attrs = sensor.extra_state_attributes
    assert attrs["status"] == "low"
    assert attrs["weeks_remaining"] == 0.7
