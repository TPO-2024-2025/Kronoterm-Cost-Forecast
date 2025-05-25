"""Sensors setup."""

from collections.abc import Callable
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
)

from custom_components.kronoterm.const import (
    DOMAIN,
    SELECT_PROVIDER,
    SELECTED_CONSUMER,
)
from custom_components.kronoterm.energy_price_sensor import EnergyPriceSensor
from custom_components.kronoterm.dummy_consumer_sensor import DummyPowerConsumerSensor
from custom_components.kronoterm.consumer_sensor import ConsumerSensor
from custom_components.kronoterm.energy_api import EnergyAPIFactory
from custom_components.kronoterm.cost_sensor import CostSensor


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""  # noqa: D401
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)

    await async_setup_platform(hass, config, async_add_entities)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    provider_name = config[SELECT_PROVIDER]
    provider = await EnergyAPIFactory.create(provider_name)

    dummy = DummyPowerConsumerSensor()
    async_add_entities([dummy], update_before_add=True)
    sensor_id = config.get(SELECTED_CONSUMER)

    energy_price_sensor: EnergyPriceSensor = await EnergyPriceSensor.new(
        provider_name, provider
    )

    consumer_sensor = ConsumerSensor(hass, sensor_id)

    async_add_entities([energy_price_sensor, consumer_sensor], update_before_add=True)

    async_add_entities(
        [CostSensor(hass)],
        update_before_add=True,
    )
