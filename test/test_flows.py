"""Test for config/option flows."""

import re
from typing import Any
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch
import pytest

import homeassistant
from homeassistant.components.recorder.const import DATA_INSTANCE
from homeassistant.components.recorder.const import DOMAIN as R_DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry  # type: ignore

from custom_components.kronoterm import config_flow
from custom_components.kronoterm.const import (
    DOMAIN,
    NAME,
    SELECT_PROVIDER,
    SELECTED_CONSUMER,
    BLACK_HOLE_SENSOR,
)
from custom_components.kronoterm.energy_api import GENI


@pytest.fixture(autouse=True)
def setup_recorder(hass: HomeAssistant) -> None:
    """Set Recorder."""

    _internal_store: dict[Any, Any] = {}
    hass.data[R_DOMAIN] = MagicMock()
    hass.data[R_DOMAIN].__getitem__.side_effect = _internal_store.__getitem__
    hass.data[R_DOMAIN].__setitem__.side_effect = _internal_store.__setitem__
    hass.data[R_DOMAIN].__delitem__.side_effect = _internal_store.__delitem__
    hass.data[R_DOMAIN].db_connected = PropertyMock(return_value=False)

    hass.data[DATA_INSTANCE] = AsyncMock()
    hass.data[DATA_INSTANCE].async_add_executor_job = AsyncMock()
    hass.data[DATA_INSTANCE].async_add_executor_job.return_value = {
        f"sensor.{BLACK_HOLE_SENSOR}": []
    }


@pytest.mark.asyncio
async def test_flow_user_init(hass: HomeAssistant) -> None:
    """Test the initialization of the form in the first step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )
    expected = {
        "data_schema": mock.ANY,  # too hard to test
        "description_placeholders": None,
        "errors": None,
        "flow_id": mock.ANY,
        "handler": DOMAIN,
        "last_step": None,
        "step_id": "user",
        "type": "form",
        "preview": None,
    }
    assert expected == result


@pytest.mark.asyncio
async def test_flow_user_init_config_entry(hass: HomeAssistant) -> None:
    """Test the config entry is successfully created."""
    with patch("custom_components.kronoterm.async_setup_entry", return_value=True):
        _result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN, context={"source": "user"}
        )
        await hass.async_block_till_done()

    selected_provider = (await GENI.providers())[0]

    result = await hass.config_entries.flow.async_configure(
        _result["flow_id"],
        user_input={SELECT_PROVIDER: selected_provider},
    )
    expected = {
        "context": {"source": "user"},
        "version": 1,
        "minor_version": 1,
        "type": "create_entry",
        "flow_id": mock.ANY,
        "handler": DOMAIN,
        "title": NAME,
        "data": {SELECT_PROVIDER: selected_provider},
        "description": None,
        "description_placeholders": None,
        "options": {},
        "result": mock.ANY,
    }
    assert expected == result


@pytest.mark.asyncio
async def test_flow_user_init_fail(hass: HomeAssistant) -> None:
    """Test the config entry is successfully created."""
    with patch("custom_components.kronoterm.async_setup_entry", return_value=True):
        _result = await hass.config_entries.flow.async_init(
            config_flow.DOMAIN, context={"source": "user"}
        )
        await hass.async_block_till_done()

    selected_provider = "abrakadabra"

    with pytest.raises(
        homeassistant.data_entry_flow.InvalidData,
        match=re.escape(f"Schema validation failed @ data['{SELECT_PROVIDER}']"),
    ):
        await hass.config_entries.flow.async_configure(
            _result["flow_id"],
            user_input={SELECT_PROVIDER: selected_provider},
        )


@pytest.mark.asyncio
async def test_options_flow_init(hass: HomeAssistant) -> None:
    """Test config flow options."""

    selected_provider = (await GENI.providers())[0]

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="_",
        data={
            SELECT_PROVIDER: selected_provider,
        },
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert result["errors"] is None


@pytest.mark.asyncio
async def test_options_flow_change_provider(hass: HomeAssistant) -> None:
    """Test config flow options."""

    providers = await GENI.providers()

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="_",
        data={
            SELECT_PROVIDER: providers[0],
        },
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    # submit form with options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={SELECT_PROVIDER: providers[1], SELECTED_CONSUMER: "None"},
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Updated options"
    assert result["result"] is True
    assert {SELECT_PROVIDER: providers[1], SELECTED_CONSUMER: None} == result["data"]


@pytest.mark.asyncio
async def test_options_flow_select_consumer(hass: HomeAssistant) -> None:
    """Test selecting and diselecting a consumer in the options flow."""

    providers = await GENI.providers()

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="_",
        data={
            SELECT_PROVIDER: providers[0],
        },
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    # submit form with options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            SELECT_PROVIDER: providers[0],
            SELECTED_CONSUMER: f"sensor.{BLACK_HOLE_SENSOR}",
        },
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Updated options"
    assert result["result"] is True
    assert {
        SELECT_PROVIDER: providers[0],
        SELECTED_CONSUMER: f"sensor.{BLACK_HOLE_SENSOR}",
    } == result["data"]

    # show initial form
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    # submit form with options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            SELECT_PROVIDER: providers[0],
            SELECTED_CONSUMER: "None",
        },
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Updated options"
    assert result["result"] is True
    assert {
        SELECT_PROVIDER: providers[0],
        SELECTED_CONSUMER: None,
    } == result["data"]
