"""Testing Consumer Sensor."""

from unittest.mock import patch, AsyncMock

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.components.recorder.const import DATA_INSTANCE

from custom_components.kronoterm.consumer_sensor import ConsumerSensor
from custom_components.kronoterm.dummy_consumer_sensor import DummyPowerConsumerSensor
from custom_components.kronoterm.const import BLACK_HOLE_SENSOR


async def setup_consumer(
    hass: HomeAssistant,
    mock_wait: AsyncMock,
) -> tuple[ConsumerSensor, DummyPowerConsumerSensor]:
    """Set up test wrapper sensor."""
    dummy_sensor = DummyPowerConsumerSensor()
    dummy_sensor.entity_id = "sensor." + BLACK_HOLE_SENSOR

    await dummy_sensor.async_update()

    # Set initial state for the target sensor
    hass.states.async_set(
        dummy_sensor.entity_id,
        dummy_sensor.state,
        dummy_sensor.extra_state_attributes,
    )

    hass.states.get.return_value = State(
        dummy_sensor.entity_id,
        dummy_sensor.state,
        {"unit_of_measurement": dummy_sensor.native_unit_of_measurement},
    )

    consumer = ConsumerSensor(hass, dummy_sensor.entity_id)

    hass.data[DATA_INSTANCE] = AsyncMock()
    hass.data[DATA_INSTANCE].async_add_executor_job = AsyncMock()
    hass.data[DATA_INSTANCE].async_add_executor_job.return_value = {
        dummy_sensor.entity_id: []
    }
    await consumer.async_added_to_hass(time=False)

    hass.states.async_set(
        consumer.entity_id,
        dummy_sensor.native_value,
        dummy_sensor.extra_state_attributes,
    )

    # await wrapper._update_state(datetime.now(), False)

    # Let Home Assistant run any scheduled tasks
    await mock_wait(hass)

    return consumer, dummy_sensor


@pytest.mark.asyncio
@patch(
    "custom_components.kronoterm.dummy_consumer_sensor.consumption",
    return_value=15,
)
@patch.object(
    HomeAssistant,
    "async_block_till_done",
    new_callable=AsyncMock,
)
async def test_consumer_state(mock_wait: AsyncMock, hass: HomeAssistant) -> None:
    """Test wrapper state after update."""
    consumer, _ = await setup_consumer(hass, mock_wait)

    assert consumer.state == 15
    assert consumer.native_value == 15
    assert consumer.available is True
    assert consumer.predictor is not None
    assert consumer.extra_state_attributes is not None
    assert "forecast" in consumer.extra_state_attributes
    assert consumer.unit_of_measurement == "W"
