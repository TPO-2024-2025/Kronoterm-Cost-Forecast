"""Test component setup."""

from unittest.mock import PropertyMock, Mock

from homeassistant.setup import async_setup_component
from homeassistant import core
from homeassistant.components.recorder.const import DOMAIN as R_DOMAIN

from custom_components.kronoterm.const import DOMAIN


async def test_async_setup(hass: core.HomeAssistant) -> None:
    """Test the component gets setup."""
    # Setup Recorder Mock
    hass.data[R_DOMAIN] = Mock()
    hass.data[R_DOMAIN].db_connected = PropertyMock(return_value=False)

    assert await async_setup_component(hass, DOMAIN, {}) is True
