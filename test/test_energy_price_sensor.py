"""Tests for current price sensor."""

from unittest.mock import AsyncMock, patch

import pytest
from custom_components.kronoterm.energy_price_sensor import EnergyPriceSensor
from custom_components.kronoterm.energy_api import GENI

from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
@patch.object(GENI, "price", new_callable=AsyncMock)
async def test_async_update_success(mock_price: AsyncMock, hass: HomeAssistant) -> None:
    """Tests a fully successful async_update."""

    mock_price.return_value = 3.14

    providers = await GENI.providers()

    sensor = await EnergyPriceSensor.new(
        providers[0],
        GENI(providers[0]),
    )
    await sensor.async_update()

    assert sensor.native_unit_of_measurement == "EUR/kWh"
    assert sensor.native_value == 3.14
    assert sensor.available is True
    assert sensor.extra_state_attributes["provider_name"] == providers[0]
    assert len(sensor.extra_state_attributes["forecast"]) == 4 * 8
    assert all(value is not None for value in sensor.extra_state_attributes["forecast"])


@pytest.mark.asyncio
@patch.object(GENI, "price", new_callable=AsyncMock)
async def test_async_update_fail(mock_price: AsyncMock, hass: HomeAssistant) -> None:
    """Tests a failed async_update."""

    mock_price.return_value = None

    providers = await GENI.providers()

    sensor = await EnergyPriceSensor.new(
        providers[0],
        GENI(providers[0]),
    )
    await sensor.async_update()

    assert sensor.native_unit_of_measurement == "EUR/kWh"
    assert sensor.native_value is None
    assert sensor.available is False
