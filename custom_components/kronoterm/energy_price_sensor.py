"""Sensor (data provider) for current price of electricity."""

from datetime import datetime
from functools import cached_property
import logging
from typing import override, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)

from custom_components.kronoterm.const import ENERGY_PRICE_SENSOR
from custom_components.kronoterm.energy_api import EnergyAPI


_LOGGER = logging.getLogger(__name__)


class EnergyPriceSensor(SensorEntity):
    """Sensor (data provider) for current and future price of electricity."""

    _provider_name: str
    _provider: EnergyAPI
    _unit: str
    _price: float | None

    def __init__(self, provider_name: str, provider: EnergyAPI):  # noqa: D107
        self._provider_name = provider_name
        self._provider = provider
        self._state: str | None = None
        self._available = True
        self._attr_translation_key = ENERGY_PRICE_SENSOR
        self._attr_unique_id = ENERGY_PRICE_SENSOR
        self._attr_has_entity_name = True
        self.entity_id = f"sensor.{ENERGY_PRICE_SENSOR}"

    @staticmethod
    async def new(provider_name: str, provider: EnergyAPI) -> Any:  # noqa: D102
        sensor = EnergyPriceSensor(provider_name, provider)
        sensor._unit = await sensor._provider.unit()
        return sensor

    # TODO: HA bug: is using state class 'measurement' which is impossible considering device class ('monetary') it is using; expected None or one of 'total'
    # @cached_property
    # @override
    # def device_class(self) -> SensorDeviceClass:
    #    return SensorDeviceClass.MONETARY

    @cached_property
    @override
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    @override
    def native_unit_of_measurement(self) -> str:
        return self._unit

    @property
    @override
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    @override
    def native_value(self) -> float | None:
        """Return current price."""
        return self._price

    async def async_update(self) -> None:  # noqa: D102
        current_price = await self._provider.current_price()
        self._price = current_price
        self._available = current_price is not None
        self._attr_extra_state_attributes = {
            "provider_name": self._provider_name,
            "forecast": await self._provider.prices(datetime.now()),
        }
