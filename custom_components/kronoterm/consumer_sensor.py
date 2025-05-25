"""Wrapper that imitates target sensor, so we can control state saving."""

from datetime import timedelta, datetime
from dateutil.tz import tzutc
from functools import partial
import logging
from typing import Any, cast, override
from collections.abc import MutableMapping

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.core import HomeAssistant, State

import homeassistant.components.recorder as rec
import homeassistant.components.recorder.history as hist

from .const import CONSUMER_SENSOR_ID
from .predictor import Predictor

_LOGGER = logging.getLogger(__name__)


class ConsumerSensor(SensorEntity):
    """Wrapper that imitates target sensor."""

    predictor: Predictor

    def __init__(self, hass: HomeAssistant, target_entity_id: str | None):
        """Initialize wrapper."""
        self._hass = hass
        self._target_entity_id = target_entity_id
        self._state = 0.0
        self._original_state = 0
        self._attr_available = target_entity_id is not None

        self._attr_translation_key = CONSUMER_SENSOR_ID
        self._attr_unique_id = CONSUMER_SENSOR_ID
        self._attr_has_entity_name = True
        self.entity_id = f"sensor.{CONSUMER_SENSOR_ID}"

        # Default attributes
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_icon = None
        self._attr_extra_state_attributes: dict[Any, Any] = {}

        self.predictor = Predictor()

    async def async_added_to_hass(self, time: bool = True) -> None:
        """When entity is added to Home Assistant."""

        if self._target_entity_id is None:
            return

        history = []

        if self._target_entity_id is not None:
            history = await get_entity_history(self._hass, self._target_entity_id)

        self.predictor = Predictor.new(
            [
                (s.last_changed, float(s.state))
                for s in history
                if s.state not in ("unknown", "unavailable", "", None)
            ]
        )

        self._update_from_state(
            self._hass.states.get(self._target_entity_id), datetime.now(tzutc())
        )

        if time:
            # Initial state fetch
            async_track_time_interval(
                self._hass,
                self._update_state,
                timedelta(seconds=60),
                cancel_on_shutdown=True,
            )

    def _update_from_state(self, state: Any, now: datetime) -> None:
        self._original_state = state
        if not state:
            return

        if state.state != "unavailable":
            self._state = float(state.state)
            self._attr_available = True

            self.predictor.add_and_refit(now, self._state)
            self._attr_extra_state_attributes["forecast"] = self.predictor.forecast(now)
        else:
            self._attr_available = False

        # Update core attributes from original
        attrs = state.attributes
        self._attr_device_class = attrs.get("device_class")
        self._attr_state_class = attrs.get("state_class")
        self._attr_native_unit_of_measurement = attrs.get("unit_of_measurement")
        self._attr_icon = attrs.get("icon")

    async def _update_state(self, now: datetime, write: bool = True) -> None:
        if self._target_entity_id is None:
            return

        state = self.hass.states.get(self._target_entity_id)
        self._update_from_state(state, now)

        if write:
            self.async_write_ha_state()

    @override
    @property
    def suggested_display_precision(self) -> int | None:
        """Display <int> decimals as default."""
        return 2

    @override
    @property
    def native_value(self) -> float:
        """Native value."""
        return self._state

    @override
    @property
    def should_poll(self) -> bool:
        """Should Poll."""
        return False


async def get_entity_history(
    hass: HomeAssistant,
    entity_id: str,
) -> list[State]:
    """Get last 7 days of entity history."""
    now = datetime.now()

    recorder = rec.get_instance(hass)

    history: MutableMapping[
        str, list[State | dict[str, Any]]
    ] = await recorder.async_add_executor_job(
        partial(
            hist.get_significant_states,
            hass,
            now - timedelta(days=7),
            now,
            [entity_id],
            significant_changes_only=False,
            no_attributes=True,
        ),
    )

    return cast(list[State], history.get(entity_id, []))
