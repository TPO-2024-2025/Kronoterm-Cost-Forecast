"""Config flow setup."""

from typing import Any

import voluptuous as vol  # type: ignore
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from custom_components.kronoterm.energy_api import EnergyAPIFactory

from .const import DOMAIN, SELECT_PROVIDER, SELECTED_CONSUMER, NAME


class ProviderConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step of the flow."""
        if user_input is not None:
            return self.async_create_entry(
                title=NAME,
                data={
                    SELECT_PROVIDER: user_input[SELECT_PROVIDER],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(SELECT_PROVIDER): vol.In(
                        await EnergyAPIFactory.providers()
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


def none_is_none(value: str) -> str | None:
    """Convert 'None' string to None."""
    return None if value == "None" else value


class OptionsFlowHandler(OptionsFlow):
    """Handles options flow for the component."""

    @property
    def config_entry(self) -> ConfigEntry:  # noqa: D102
        entry = self.hass.config_entries.async_get_entry(self.handler)
        assert entry is not None
        return entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options for the custom component."""
        # Get currently selected from the entity registry
        # entity_registry = await async_get_registry(self.hass)
        # entries = async_entries_for_config_entry(
        #    entity_registry, self.config_entry.entry_id
        # )
        selected_provider = self.config_entry.data[SELECT_PROVIDER]
        selected_sensor = self.config_entry.data.get(SELECTED_CONSUMER, None)
        # https://community.home-assistant.io/t/config-flow-how-to-update-an-existing-entity/522442/8
        if user_input is not None:
            data = {
                SELECT_PROVIDER: user_input[SELECT_PROVIDER],
                SELECTED_CONSUMER: none_is_none(user_input[SELECTED_CONSUMER]),
            }
            self.hass.config_entries.async_update_entry(self.config_entry, data=data)

            return self.async_create_entry(title="Updated options", data=data)

        # Fetch all sensors from the entity registry
        entity_registry = async_get_entity_registry(self.hass)
        all_sensors = {
            entity.entity_id: entity.name or entity.entity_id
            for entity in entity_registry.entities.values()
            if entity.entity_id.startswith("sensor.")
            and entity.unit_of_measurement in UnitOfPower.__dict__.values()
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        SELECT_PROVIDER,
                        default=selected_provider,
                    ): vol.In(await EnergyAPIFactory.providers()),
                    vol.Optional(
                        SELECTED_CONSUMER,
                        default=selected_sensor or "None",
                    ): vol.In(list(all_sensors.keys()) + ["None"]),
                }
            ),
        )
