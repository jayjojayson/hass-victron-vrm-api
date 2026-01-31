"""Config flow to set up Victron VRM Energy."""
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import logging

from .const import (
    DOMAIN, 
    CONF_SITE_ID, 
    CONF_TOKEN, 
    CONF_BATTERY_INSTANCE,
    CONF_MULTI_INSTANCE,
    CONF_PV_INVERTER_INSTANCE,
    CONF_TANK_INSTANCE,
    CONF_SOLAR_CHARGER_INSTANCE,
    CONF_GRID_INSTANCE
) 

_LOGGER = logging.getLogger(__name__)

# Definieren des Schemas für die initiale Konfiguration mit Beschreibungen
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_SITE_ID, description="Victron VRM Site ID"): str,
    vol.Required(CONF_TOKEN, description="VRM API Token"): str,
    vol.Optional(CONF_BATTERY_INSTANCE, default="", description="Battery Instance IDs (e.g., '1, 2')"): str,
    vol.Optional(CONF_MULTI_INSTANCE, default="", description="MultiPlus Instance IDs (e.g., '100, 101')"): str,
    vol.Optional(CONF_PV_INVERTER_INSTANCE, default="", description="PV Inverter Instance IDs (e.g., '200')"): str,
    vol.Optional(CONF_TANK_INSTANCE, default="", description="Tank Instance IDs (e.g., '300, 301')"): str,
    vol.Optional(CONF_SOLAR_CHARGER_INSTANCE, default="", description="Solar Charger Instance IDs (e.g., '400')"): str,
    vol.Optional(CONF_GRID_INSTANCE, default="", description="Grid Meter Instance IDs (e.g., '30')"): str,
})


class VictronVrmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Victron VRM Energy."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step when adding the integration via UI."""
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = str(user_input[CONF_SITE_ID])
            
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Victron VRM Site {unique_id}", 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the reconfiguration step (Neu konfigurieren)."""
        errors: dict[str, str] = {}
        
        # Hole den aktuellen Config Entry
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None:
            # Aktualisiere den Eintrag und lade ihn neu
            return self.async_update_reload_and_abort(
                entry, 
                data=user_input
            )

        # Schema mit aktuellen Werten als Default vorbefüllen UND Beschreibungen beibehalten
        current_config = entry.data
        
        reconfigure_schema = vol.Schema({
            vol.Required(CONF_SITE_ID, default=current_config.get(CONF_SITE_ID), description="Victron VRM Site ID"): str,
            vol.Required(CONF_TOKEN, default=current_config.get(CONF_TOKEN), description="VRM API Token"): str,
            vol.Optional(CONF_BATTERY_INSTANCE, default=current_config.get(CONF_BATTERY_INSTANCE, ""), description="Battery Instance IDs (e.g., '1, 2')"): str,
            vol.Optional(CONF_MULTI_INSTANCE, default=current_config.get(CONF_MULTI_INSTANCE, ""), description="MultiPlus Instance IDs (e.g., '100, 101')"): str,
            vol.Optional(CONF_PV_INVERTER_INSTANCE, default=current_config.get(CONF_PV_INVERTER_INSTANCE, ""), description="PV Inverter Instance IDs (e.g., '200')"): str,
            vol.Optional(CONF_TANK_INSTANCE, default=current_config.get(CONF_TANK_INSTANCE, ""), description="Tank Instance IDs (e.g., '300, 301')"): str,
            vol.Optional(CONF_SOLAR_CHARGER_INSTANCE, default=current_config.get(CONF_SOLAR_CHARGER_INSTANCE, ""), description="Solar Charger Instance IDs (e.g., '400')"): str,
            vol.Optional(CONF_GRID_INSTANCE, default=current_config.get(CONF_GRID_INSTANCE, ""), description="Grid Meter Instance IDs (e.g., '30')"): str,
        })

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=reconfigure_schema,
            errors=errors,
        )
        