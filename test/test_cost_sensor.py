"""Tests for cost sensor."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest import approx

from custom_components.kronoterm.consumer_sensor import ConsumerSensor
from custom_components.kronoterm.dummy_consumer_sensor import DummyPowerConsumerSensor
from custom_components.kronoterm.const import (
    CONSUMER_SENSOR_ID,
    ENERGY_PRICE_SENSOR,
    BLACK_HOLE_SENSOR,
)
from custom_components.kronoterm.energy_price_sensor import EnergyPriceSensor
from custom_components.kronoterm.cost_sensor import CostSensor
from custom_components.kronoterm.energy_api import GENI

from datetime import datetime

import asyncio

from homeassistant.core import HomeAssistant, State
from homeassistant.components.sensor import SensorStateClass
from homeassistant.components.recorder.const import DATA_INSTANCE

import copy
from collections.abc import Sequence

test_price = 0.13
test_consumption = 1300
test_price_forecast = [
    (datetime(2025, 5, 13, 13, 0), 0.13),
    (datetime(2025, 5, 13, 13, 15), 0.13),
    (datetime(2025, 5, 13, 13, 30), 0.13),
    (datetime(2025, 5, 13, 13, 45), None),
]
test_consumption_forecast = [
    (datetime(2025, 5, 13, 13, 0), 1300.0),
    (datetime(2025, 5, 13, 13, 15), 1400.0),
    (datetime(2025, 5, 13, 13, 30), 1500.0),
    (datetime(2025, 5, 13, 13, 45), 1600.0),
]


def calculate_forecast_expected(
    price_forecast_arr: Sequence[tuple[datetime, float | None]],
    consumption_forecast_arr: Sequence[tuple[datetime, float | None]],
) -> list[tuple[datetime, float | None]]:
    """Create forecast array based on the test data."""
    forecast_expected: list[tuple[datetime, float | None]] = []
    last_datetime = None
    total_cost = 0.0

    for price_entry, consumption_entry in zip(
        price_forecast_arr, consumption_forecast_arr
    ):
        price_time, price_value = price_entry
        consumption_time, consumption_value = consumption_entry

        if price_value is None or consumption_value is None:
            continue

        if last_datetime is None:
            last_datetime = consumption_time
            forecast_expected.append((last_datetime, total_cost))
            continue

        # calculate cost for the last period
        time_diff_sec = (consumption_time - last_datetime).total_seconds()
        time_diff_hours = time_diff_sec / 3600
        cost = price_value * (consumption_value / 1000) * time_diff_hours

        # update the total cost
        total_cost += cost
        forecast_expected.append((consumption_time, total_cost))

        # update loop variables
        last_datetime = consumption_time

    return forecast_expected


async def setup_cost_sensor(
    hass: HomeAssistant,
    mock_wait: AsyncMock,
) -> dict:
    """Set up test wrapper sensor."""

    # Setting up the Dummy Consumer Sensor
    dummy_sensor = DummyPowerConsumerSensor()
    dummy_sensor.entity_id = "sensor." + BLACK_HOLE_SENSOR

    await dummy_sensor.async_update()

    hass.states.async_set(
        dummy_sensor.entity_id,
        dummy_sensor.state,
        dummy_sensor.extra_state_attributes,
    )

    # Setting up the Consumer Sensor
    consumer = ConsumerSensor(hass, dummy_sensor.entity_id)
    consumer.entity_id = "sensor." + CONSUMER_SENSOR_ID

    hass.data[DATA_INSTANCE] = AsyncMock()
    hass.data[DATA_INSTANCE].async_add_executor_job = AsyncMock()
    hass.data[DATA_INSTANCE].async_add_executor_job.return_value = {
        dummy_sensor.entity_id: []
    }

    await consumer.async_added_to_hass(time=False)

    hass.states.async_set(
        consumer.entity_id,
        consumer.state,
        dummy_sensor.extra_state_attributes,
    )

    # Setting up the Energy Price Sensor
    providers = await GENI.providers()
    energy_price_sensor = await EnergyPriceSensor.new(
        providers[0],
        GENI(providers[0]),
    )
    energy_price_sensor.entity_id = "sensor." + ENERGY_PRICE_SENSOR
    await energy_price_sensor.async_added_to_hass()
    await energy_price_sensor.async_update()

    hass.states.async_set(
        energy_price_sensor.entity_id,
        energy_price_sensor.native_value,
        {"unit_of_measurement": energy_price_sensor.native_unit_of_measurement},
    )

    # Let Home Assistant run any scheduled tasks
    await mock_wait(hass)

    return {
        "dummy_sensor": dummy_sensor,
        "consumer": consumer,
        "energy_price_sensor": energy_price_sensor,
    }


@pytest.mark.asyncio
# for some reason ce naslednjo vrstico odstranm, dobim errorje, ceprou nikol zares ne returnam 1000 pr dummy consumerju but oh well
@patch(
    "custom_components.kronoterm.dummy_consumer_sensor.consumption", return_value=1000
)
@patch.object(HomeAssistant, "states", create=True)
@patch.object(HomeAssistant, "async_block_till_done", new_callable=AsyncMock)
async def test_cost_sensor_success(
    mock_wait: AsyncMock, mock_states: MagicMock, hass: HomeAssistant
) -> None:
    """Test CostSensor state transitions and calculations."""

    # Mocking three different things
    def mock_get_state(entity_id: str) -> State | None:
        if entity_id == "sensor." + ENERGY_PRICE_SENSOR:
            return State(
                entity_id,
                str(test_price),
                {"unit_of_measurement": "EUR/kWh", "forecast": test_price_forecast},
            )
        elif entity_id == "sensor." + BLACK_HOLE_SENSOR:
            return State(
                entity_id,
                str(test_consumption),
                {"unit_of_measurement": "W", "forecast": test_consumption_forecast},
            )
        elif entity_id == "sensor." + CONSUMER_SENSOR_ID:
            return State(
                entity_id,
                str(test_consumption),
                {"unit_of_measurement": "W", "forecast": test_consumption_forecast},
            )

        return None

    hass.states.get = MagicMock(side_effect=mock_get_state)

    # Prepare all the sensors needed for cost sensor to work
    _ = await setup_cost_sensor(hass, mock_wait)

    # Create the Cost Sensor instance
    cost_sensor = CostSensor(hass)

    # Updating the first time - cost is 0.0, everything else is available
    await cost_sensor.async_update()
    last_update_local = cost_sensor._last_update

    # create an expected output for forecast cost
    forecast_expected = calculate_forecast_expected(
        test_price_forecast, test_consumption_forecast
    )

    # Assertions
    assert cost_sensor.native_value == 0.0
    assert cost_sensor._cost == 0.0
    assert cost_sensor.available is True
    assert cost_sensor._last_update is not None
    assert last_update_local is not None
    assert cost_sensor.current_price == test_price
    assert cost_sensor.current_consumption == test_consumption
    assert cost_sensor._cost_forecast_cumulative == forecast_expected

    # Update second time - cost increases based on the last update

    # Cost is calculated as last_update - now -> we need at least 1s for normal results
    await asyncio.sleep(1)

    await cost_sensor.async_update()
    update_now_local = cost_sensor._last_update

    # all needed variables to calculate the cost
    time_diff_sec = (update_now_local - last_update_local).total_seconds()
    time_diff_hours = time_diff_sec / 3600
    expected_cost = test_price * (test_consumption / 1000) * time_diff_hours

    # Assertions
    assert cost_sensor.native_value == approx(expected_cost, rel=1e-2)
    assert cost_sensor._cost == approx(expected_cost, rel=1e-2)
    assert cost_sensor.available is True  # for some reason se mypy prtozuje lol
    assert cost_sensor._last_update == update_now_local

    # Testing all other (less important imo) lines:
    assert cost_sensor.native_unit_of_measurement == "EUR"
    # assert cost_sensor.name == TOTAL_COST_SENSOR
    assert cost_sensor.last_reset is None
    assert cost_sensor.state_class == SensorStateClass.TOTAL
    assert cost_sensor.current_price == test_price
    assert cost_sensor.current_consumption == test_consumption
    assert cost_sensor._cost_forecast_cumulative == forecast_expected


async def test_missing_values(hass: HomeAssistant) -> None:
    """Test _calculate_cost() when current price and current consumption are None."""

    # Creating the CostSensor instance
    cost_sensor = CostSensor(hass)

    # Testing if price is None
    cost_sensor._price = None
    cost_sensor._consumption = test_consumption
    now = datetime.now()
    cost = cost_sensor._calculate_cost(now)

    # Assertions
    assert cost is None

    # Testing if consumption is None
    cost_sensor._price = test_price
    cost_sensor._consumption = None
    now = datetime.now()
    cost = cost_sensor._calculate_cost(now)

    # Assertions
    assert cost is None


@pytest.mark.asyncio
@patch(
    "custom_components.kronoterm.dummy_consumer_sensor.consumption", return_value=1000
)
@patch.object(HomeAssistant, "states", create=True)
@patch.object(HomeAssistant, "async_block_till_done", new_callable=AsyncMock)
async def test_different_units(
    mock_wait: AsyncMock, mock_states: MagicMock, hass: HomeAssistant
) -> None:
    """Test different power units got from consumption sensor."""

    units = ["W", "kW", "mW", "something_else"]

    for unit in units:
        # Mocking three different things
        def mock_get_state(entity_id: str) -> State | None:
            if entity_id == "sensor." + ENERGY_PRICE_SENSOR:
                return State(
                    entity_id,
                    str(test_price),
                    {"unit_of_measurement": "EUR/kWh", "forecast": test_price_forecast},
                )
            elif entity_id == "sensor." + BLACK_HOLE_SENSOR:
                return State(
                    entity_id,
                    str(test_consumption),
                    {
                        "unit_of_measurement": unit,
                        "forecast": test_consumption_forecast,
                    },
                )
            elif entity_id == "sensor." + CONSUMER_SENSOR_ID:
                return State(
                    entity_id,
                    str(test_consumption),
                    {
                        "unit_of_measurement": unit,
                        "forecast": test_consumption_forecast,
                    },
                )

            return None

        hass.states.get = MagicMock(side_effect=mock_get_state)

        # Prepare all the sensors needed for cost sensor to work
        _ = await setup_cost_sensor(hass, mock_wait)

        # Create the Cost Sensor instance
        cost_sensor = CostSensor(hass)

        # Updating the first time - cost is 0.0, everything else is available
        await cost_sensor.async_update()

        # Testing only unit
        test_consumption_factorized = test_consumption

        if unit.lower() == "w":
            test_consumption_factorized = test_consumption
        elif unit.lower() == "kw":
            test_consumption_factorized = test_consumption * 1_000
        elif unit.lower() == "mw":
            test_consumption_factorized = test_consumption * 1_000_000
        else:
            test_consumption_factorized = test_consumption

        # Assertions
        assert cost_sensor.current_consumption == test_consumption_factorized


# price time: 13:00, consumption time: 13:15
test_price_forecast_15_less = [
    (datetime(2025, 5, 13, 13, 0), 0.13),
    (datetime(2025, 5, 13, 13, 15), 0.13),
    (datetime(2025, 5, 13, 13, 30), 0.13),
    (datetime(2025, 5, 13, 13, 45), 0.13),
]
test_consumption_forecast_normal = [
    (datetime(2025, 5, 13, 13, 15), 1400.0),
    (datetime(2025, 5, 13, 13, 30), 1500.0),
    (datetime(2025, 5, 13, 13, 45), 1600.0),
    (datetime(2025, 5, 13, 14, 00), 1700.0),
]

# price time: 13:15, consumption time: 13:00
test_price_forecast_normal = [
    (datetime(2025, 5, 13, 13, 15), 0.13),
    (datetime(2025, 5, 13, 13, 30), 0.13),
    (datetime(2025, 5, 13, 13, 45), 0.13),
    (datetime(2025, 5, 13, 14, 00), 0.13),
]
test_consumption_forecast_15_less = [
    (datetime(2025, 5, 13, 13, 00), 1400.0),
    (datetime(2025, 5, 13, 13, 15), 1500.0),
    (datetime(2025, 5, 13, 13, 30), 1600.0),
    (datetime(2025, 5, 13, 13, 45), 1700.0),
]

# price time: 13:00, consumption time: 13:30
test_price_forecast_30_diff = [
    (datetime(2025, 5, 13, 13, 0), 1400.0),
    (datetime(2025, 5, 13, 13, 15), 1500.0),
    (datetime(2025, 5, 13, 13, 30), 1600.0),
    (datetime(2025, 5, 13, 13, 45), 1700.0),
]

test_consumption_forecast_30_diff = [
    (datetime(2025, 5, 13, 13, 30), 1400.0),
    (datetime(2025, 5, 13, 13, 45), 1500.0),
    (datetime(2025, 5, 13, 14, 00), 1600.0),
    (datetime(2025, 5, 13, 14, 15), 1700.0),
]


@pytest.mark.asyncio
@patch(
    "custom_components.kronoterm.dummy_consumer_sensor.consumption", return_value=1000
)
@patch.object(HomeAssistant, "states", create=True)
@patch.object(HomeAssistant, "async_block_till_done", new_callable=AsyncMock)
async def test_different_forecast_timestamps(
    mock_wait: AsyncMock, mock_states: MagicMock, hass: HomeAssistant
) -> None:
    """Test different forecast timestamps got from Energy Price Sensor and Consumption Sensor."""

    forecasts: list[
        tuple[
            list[tuple[datetime, float]] | None,
            list[tuple[datetime, float]] | None,
        ]
    ] = [
        (test_price_forecast_15_less, test_consumption_forecast_normal),
        (test_price_forecast_normal, test_consumption_forecast_15_less),
        (test_price_forecast_30_diff, test_consumption_forecast_30_diff),
        (None, None),
    ]

    for forecast in forecasts:
        # Mocking three different things
        p_forecast: list[tuple[datetime, float]] | None = copy.deepcopy(forecast[0])
        c_forecast: list[tuple[datetime, float]] | None = copy.deepcopy(forecast[1])

        def mock_get_state(entity_id: str) -> State | None:
            if entity_id == "sensor." + ENERGY_PRICE_SENSOR:
                return State(
                    entity_id,
                    str(test_price),
                    {"unit_of_measurement": "EUR/kWh", "forecast": p_forecast},
                )
            elif entity_id == "sensor." + BLACK_HOLE_SENSOR:
                return State(
                    entity_id,
                    str(test_consumption),
                    {
                        "unit_of_measurement": "W",
                        "forecast": c_forecast,
                    },
                )
            elif entity_id == "sensor." + CONSUMER_SENSOR_ID:
                return State(
                    entity_id,
                    str(test_consumption),
                    {
                        "unit_of_measurement": "W",
                        "forecast": c_forecast,
                    },
                )

            return None

        hass.states.get = MagicMock(side_effect=mock_get_state)

        # Prepare all the sensors needed for cost sensor to work
        _ = await setup_cost_sensor(hass, mock_wait)

        # Create the Cost Sensor instance
        cost_sensor = CostSensor(hass)

        # Updating the first time - cost is 0.0, everything else is available
        await cost_sensor.async_update()
        p_forecast_again: list[tuple[datetime, float]] | None = copy.deepcopy(
            forecast[0]
        )
        c_forecast_again: list[tuple[datetime, float]] | None = copy.deepcopy(
            forecast[1]
        )

        if p_forecast_again is None or c_forecast_again is None:
            assert cost_sensor._cost_forecast_cumulative is None
            return

        # Testing calculate forecast cost cumulative
        expected_forecast = None

        if (
            abs((p_forecast_again[0][0] - c_forecast_again[0][0]).total_seconds())
            > 60 * 15
        ):
            expected_forecast = None
        elif p_forecast_again[0][0] < c_forecast_again[0][0]:
            # remove the first price forecast entry
            p_forecast_again.pop(0)
            expected_forecast = calculate_forecast_expected(
                p_forecast_again, c_forecast_again
            )
        elif p_forecast_again[0][0] > c_forecast_again[0][0]:
            # remove the first consumption forecast entry
            c_forecast_again.pop(0)
            expected_forecast = calculate_forecast_expected(
                p_forecast_again, c_forecast_again
            )

        # Assertions
        assert cost_sensor._cost_forecast_cumulative == expected_forecast
