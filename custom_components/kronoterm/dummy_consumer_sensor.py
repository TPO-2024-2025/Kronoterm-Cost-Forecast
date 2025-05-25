"""Dummy sensor that simulates heat pump consumption by reporting power usage in Watts based on current minutes."""

from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import Any, override
import numpy as np

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower

from custom_components.kronoterm.const import BLACK_HOLE_SENSOR


class DummyPowerConsumerSensor(SensorEntity):
    """Black hole that consumes power."""

    def __init__(self) -> None:  # noqa: D107
        self._attr_translation_key = BLACK_HOLE_SENSOR
        self._attr_unique_id = BLACK_HOLE_SENSOR
        self._attr_has_entity_name = True
        self.entity_id = f"sensor.{BLACK_HOLE_SENSOR}"
        self._attr_available = True

    @staticmethod
    async def new() -> Any:  # noqa: D102
        sensor = DummyPowerConsumerSensor()
        return sensor

    @cached_property
    @override
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    @override
    def suggested_display_precision(self) -> int | None:
        """Display <int> decimals as default."""
        return 2

    @property
    @override
    def native_unit_of_measurement(self) -> str:
        return UnitOfPower.WATT

    @property
    @override
    def device_class(self) -> SensorDeviceClass:
        return SensorDeviceClass.POWER

    async def async_update(self) -> None:
        """
        Simulate power consumption based on the current minute.

        Updates every SCAN_INTERVAL=30s.
        """
        self._attr_native_value = consumption()
        self._attr_available = True


def consumption() -> float:  # noqa: D103
    dt = datetime.now()

    # Fine fluctuations (periodic per day)
    def fine_fluctuations(minute_of_day: float) -> float:
        return float(
            2 * np.sin(2 * np.pi * minute_of_day / 7.5)
            + 1.5 * np.sin(2 * np.pi * minute_of_day / 3.3)
            + 0.8 * np.sin(2 * np.pi * minute_of_day / 1.8)
        )

    # Smooth peak (Gaussian-shaped with wraparound)
    def smooth_peak(
        hour: float, center: float, amplitude: float, width_hours: float
    ) -> float:
        delta = (hour - center + 12) % 24 - 12  # Wrap hour within -12 to 12
        return float(amplitude * np.exp(-(delta**2) / (2 * width_hours**2)))

    hour = dt.hour + dt.minute / 60.0
    minute_of_day = dt.hour * 60 + dt.minute

    base_load = 300
    night_peak = smooth_peak(hour, center=2, amplitude=12000, width_hours=2.5)
    morning_peak = smooth_peak(hour, center=6, amplitude=5400, width_hours=2.0)
    evening_peak = smooth_peak(hour, center=18, amplitude=7200, width_hours=3.0)
    modulation = float(150 * np.cos(2 * np.pi * hour / 24))
    fine = fine_fluctuations(minute_of_day)

    return float(
        base_load + night_peak + morning_peak + evening_peak + modulation + fine
    )
