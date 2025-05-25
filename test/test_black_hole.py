"""Tests for dummy power consumer sensor."""

from unittest.mock import patch

import pytest
from custom_components.kronoterm.dummy_consumer_sensor import DummyPowerConsumerSensor

from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
@patch(
    "custom_components.kronoterm.dummy_consumer_sensor.consumption",
    return_value=15,
)
async def test_async_update_success(hass: HomeAssistant) -> None:
    """Tests a fully successful async_update."""

    sensor = DummyPowerConsumerSensor()
    await sensor.async_update()

    assert sensor.native_unit_of_measurement == "W"
    assert sensor.native_value == 15
    assert sensor.available is True
    assert sensor.unique_id == "black_hole_sensor"
