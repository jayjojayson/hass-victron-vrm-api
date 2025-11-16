"""The component entry point for the Victron VRM Energy integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.config_validation import config_entry_only_config_schema

from .const import DOMAIN 

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"] 

# Definiert, dass die Integration NUR über Config Entries (UI) eingerichtet werden kann
CONFIG_SCHEMA = config_entry_only_config_schema 
# NOTE: async_reload_entry und der Update Listener sind entfernt.

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Victron VRM component."""
    # Diese Funktion wird nun von der CONFIG_SCHEMA-Definition abgesichert.
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Victron VRM from a config entry (nach erfolgreichem UI-Setup)."""
    
    hass.data.setdefault(DOMAIN, {})
    # Speichere die Konfigurationsdaten (die nur aus entry.data stammen)
    hass.data[DOMAIN][entry.entry_id] = entry.data 

    # Lade die Plattformen (sensor.py)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry (z.B. bei Deinstallation oder Reload)."""
    
    # Entlade alle Plattformen sauber
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        # Entferne die gespeicherten Daten
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
    
