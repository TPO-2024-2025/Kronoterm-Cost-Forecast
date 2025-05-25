"""Cost sensor based on current price of electricity and current consumption."""

from functools import cached_property
import logging
from typing import override, Any, cast

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant

from custom_components.kronoterm.const import (
    TOTAL_COST_SENSOR,
    CONSUMER_SENSOR_ID,
    ENERGY_PRICE_SENSOR,
)

from datetime import datetime
from decimal import Decimal

_LOGGER = logging.getLogger(__name__)


class CostSensor(RestoreSensor):
    """Sensor that calculates cost from consumption and electricity price."""

    def __init__(self, hass: HomeAssistant) -> None:  # noqa: D107
        """Create a new cost sensor."""

        # core state
        self._state: str | None = None
        self._available = True

        self._cost: float | None = None
        self._price: float | None = None
        self._consumption: float | None = None

        # settings for this entity
        self._attr_translation_key = TOTAL_COST_SENSOR
        self._attr_unique_id = TOTAL_COST_SENSOR
        self._attr_has_entity_name = True
        self.entity_id = f"sensor.{TOTAL_COST_SENSOR}"

        # other entities settings
        self._current_price_entity_id: str = f"sensor.{ENERGY_PRICE_SENSOR}"
        self._consumption_entity_id: str = f"sensor.{CONSUMER_SENSOR_ID}"
        self._hass: HomeAssistant = hass

        # cumulative sum variables:
        self._cumulative_cost: float = 0.0
        self._last_update: datetime | None = None

        # forecast variables
        self._consumption_forecast: list[tuple[datetime, float | None]] | None = None
        self._price_forecast: list[tuple[datetime, float | None]] | None = None
        self._attr_extra_state_attributes: dict[Any, Any] = {}

    @cached_property
    @override
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.TOTAL

    @property
    @override
    def last_reset(self) -> datetime | None:
        """Tell HA when to reset sensor, when set to None it never resets it."""
        return None

    @property
    @override
    def suggested_display_precision(self) -> int | None:
        """Display <int> decimals as default."""
        return 2

    @property
    @override
    def native_unit_of_measurement(self) -> str | None:
        state_price = self._hass.states.get(self._current_price_entity_id)

        if state_price and state_price.state not in (None, "unknown", "unavailable"):
            try:
                unit_full = cast(
                    str, state_price.attributes.get("unit_of_measurement", "")
                )

                # extract the currency
                unit = unit_full.split("/")[0].strip()

                return unit

            except (TypeError, ValueError):
                _LOGGER.error("Error while getting unit from price sensor.")
                return None
        else:
            _LOGGER.info("Current price entity state is unavailable.")
            return None

    @property
    @override
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    @override
    def native_value(self) -> float | None:
        """Return current cost."""
        return self._cumulative_cost

    @property
    def current_price(self) -> float | None:
        """Return current price."""
        return self._price

    @property
    def current_consumption(self) -> float | None:
        """Return current consumption."""
        return self._consumption

    def _get_current_price(self) -> float | None:
        """Get and return current price from current price sensor."""

        state_price = self._hass.states.get(self._current_price_entity_id)

        if state_price and state_price.state not in (None, "unknown", "unavailable"):
            try:
                return float(state_price.state)
            except (TypeError, ValueError):
                _LOGGER.error("Error while getting current data from price sensor.")
                return None
        else:
            _LOGGER.info("Current price entity state is unavailable.")
            return None

    def _get_current_consumption(self) -> float | None:
        """Get and return current consumption from consumer sensor."""

        state_consumption = self._hass.states.get(self._consumption_entity_id)

        if state_consumption and state_consumption.state not in (
            None,
            "unknown",
            "unavailable",
        ):
            try:
                # get data - unit, consumption
                raw_consumption = float(state_consumption.state)
                unit = state_consumption.attributes.get(
                    "unit_of_measurement", ""
                ).lower()

                # check what unit consumer has
                factor = 1
                if unit == "w":
                    factor = 1
                elif unit == "kw":
                    factor = 1_000
                elif unit == "mw":
                    factor = 1_000_000
                else:
                    _LOGGER.info(
                        f"Unknown unit for consumption sensor: '{unit}', taking W as the unit anyway."
                    )
                    factor = 1

                return raw_consumption * factor

            except (TypeError, ValueError):
                _LOGGER.error(
                    "Error while getting current data from consumption sensor."
                )
                return None
        else:
            _LOGGER.info("Current consumption entity state is unavailable.")
            return None

    def _get_forecast_price(self) -> list[tuple[datetime, float | None]] | None:
        """Get and return forecast price from current price sensor."""

        state_price = self._hass.states.get(self._current_price_entity_id)

        if state_price and state_price.state not in (
            None,
            "unknown",
            "unavailable",
        ):
            try:
                # get data - forecast array of tuples
                forecast: list[tuple[datetime, float | None]] = (
                    state_price.attributes.get("forecast")
                )

                return forecast

            except (TypeError, ValueError):
                _LOGGER.warning("Error while getting forecast data from price sensor.")
                return None
        else:
            _LOGGER.info("Forecast price entity state is unavailable.")
            return None

    def _get_forecast_consumption(self) -> list[tuple[datetime, float | None]] | None:
        """Get and return forecast consumption from consumer sensor."""

        state_consumption = self._hass.states.get(self._consumption_entity_id)

        if state_consumption and state_consumption.state not in (
            None,
            "unknown",
            "unavailable",
        ):
            try:
                # get data - unit, forecast array of tuples
                unit = state_consumption.attributes.get(
                    "unit_of_measurement", ""
                ).lower()

                forecast: list[tuple[datetime, float | None]] = (
                    state_consumption.attributes.get("forecast")
                )

                # check what unit consumer has
                factor = 1
                if unit == "w":
                    factor = 1
                elif unit == "kw":
                    factor = 1_000
                elif unit == "mw":
                    factor = 1_000_000
                else:
                    _LOGGER.info(
                        f"Unknown unit for consumption sensor: '{unit}', taking W as the unit anyway."
                    )
                    factor = 1

                if factor != 1:
                    # if factor isn't 1, we multiply consumption with it to get W
                    forecast = [
                        (timestamp, value * factor if value is not None else None)
                        for timestamp, value in forecast
                    ]

                return forecast

            except (TypeError, ValueError):
                _LOGGER.warning(
                    "Error while getting forecast data from consumption sensor."
                )
                return None
        else:
            _LOGGER.info("Forecast consumption entity state is unavailable.")
            return None

    def _calculate_cost(self, now: datetime) -> float | None:
        """Calculate current cost based on current price and consumption from the last update to now."""

        # current price ... EUR / kWh
        # consumption ... W
        # cost = price * (consumption/1000) = EUR/kWh * (W/1000) = EUR/kWh * kW = EUR/h
        # then we only need time - we get this from difference in time since last update to now

        if self._price is None or self._consumption is None:
            return None

        if self._last_update is None:
            self._last_update = now
            return 0.0

        time_diff_sec = (now - self._last_update).total_seconds()
        time_diff_hours = time_diff_sec / 3600

        cost = self._price * (self._consumption / 1000) * time_diff_hours

        self._last_update = now

        return cost

    def _update_cumulative_cost(self) -> None:
        """Calculate cumulative cost since the last update."""

        if self._cost is not None:
            self._cumulative_cost += self._cost

    def _calculate_forecast_cost_cumulative(
        self,
    ) -> list[tuple[datetime, float | None]] | None:
        """Calculate forecast cost based on forecast price and consumption."""

        if self._price_forecast is None or self._consumption_forecast is None:
            return None

        forecast: list[tuple[datetime, float | None]] = []
        last_datetime = None
        total_cost = 0.0

        # price time and consumption time can differ for 15 minutes
        # in case one was updated e.g. at 14.59 and another at 15.00
        # in that case we level them and return forecast with one entry less than usually
        if (
            abs(
                (
                    self._price_forecast[0][0] - self._consumption_forecast[0][0]
                ).total_seconds()
            )
            > 60 * 15
        ):
            _LOGGER.warning(
                "Datetime in price forecast and consumption forecast differ by more than 15 minutes."
            )
            return None
        elif self._price_forecast[0][0] < self._consumption_forecast[0][0]:
            # remove the first price forecast entry
            self._price_forecast.pop(0)
        elif self._price_forecast[0][0] > self._consumption_forecast[0][0]:
            # remove the first consumption forecast entry
            self._consumption_forecast.pop(0)

        for price_entry, consumption_entry in zip(
            self._price_forecast, self._consumption_forecast
        ):
            price_time, price_value = price_entry
            consumption_time, consumption_value = consumption_entry

            if price_value is None or consumption_value is None:
                continue

            if last_datetime is None:
                last_datetime = consumption_time
                forecast.append((last_datetime, total_cost))
                continue

            # calculate cost for the last period
            time_diff_sec = (consumption_time - last_datetime).total_seconds()
            time_diff_hours = time_diff_sec / 3600
            cost = price_value * (consumption_value / 1000) * time_diff_hours

            # update the total cost
            total_cost += cost
            forecast.append((consumption_time, total_cost))

            # update loop variables
            last_datetime = consumption_time

        return forecast

    async def async_update(self) -> None:
        """Update."""
        now = datetime.now()

        # get data from other sensors:
        self._price = self._get_current_price()
        self._consumption = self._get_current_consumption()
        self._consumption_forecast = self._get_forecast_consumption()
        self._price_forecast = self._get_forecast_price()

        # calculate current cost and cumulative cost:
        self._cost = self._calculate_cost(now)
        self._update_cumulative_cost()

        # calculate forecast cost:
        self._cost_forecast_cumulative = self._calculate_forecast_cost_cumulative()
        self._attr_extra_state_attributes["cost_forecast_cumulative"] = (
            self._cost_forecast_cumulative
        )

        self._available = self._cumulative_cost is not None

    async def async_added_to_hass(self) -> None:
        """Restore previous state after Home Assistant restarts."""

        await super().async_added_to_hass()

        last_sensor_data = await self.async_get_last_sensor_data()
        if last_sensor_data is not None:
            native_value = last_sensor_data.native_value

            if isinstance(native_value, int | float | Decimal):
                self._cumulative_cost = float(native_value)
            else:
                _LOGGER.warning(
                    "Failed to restore cumulative cost because native value has incompatible type: (%s). Restarting cumulative cost.",
                    type(native_value),
                )
                self._cumulative_cost = 0.0
