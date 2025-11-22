"""Config flow to set up Victron VRM Energy."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import logging

from .const import (
    DOMAIN, 
    CONF_SITE_ID, 
    CONF_TOKEN, 
    CONF_BATTERY_INSTANCE,
    CONF_MULTI_INSTANCE,
    CONF_PV_INVERTER_INSTANCE
) 

_LOGGER = logging.getLogger(__name__)

# Definieren des Schemas für die initiale Konfiguration
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_SITE_ID, description="Victron VRM Site ID"): str,
    vol.Required(CONF_TOKEN, description="VRM API Token"): str,
    # Instanz-IDs sind optional (0 = deaktiviert)
    vol.Optional(CONF_BATTERY_INSTANCE, default=0, description="Optional Battery Instance ID"): vol.Coerce(int),
    vol.Optional(CONF_MULTI_INSTANCE, default=0, description="Optional MultiPlus Instance ID"): vol.Coerce(int),
    vol.Optional(CONF_PV_INVERTER_INSTANCE, default=0, description="Optional PV Inverter Instance ID"): vol.Coerce(int),
})


class VictronVrmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Victron VRM Energy."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
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
