"""The component entry point for the Victron VRM Energy integration."""
import logging
from pathlib import Path

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

_LOVELACE_CARD_URL = "/victron_vrm_api/victron-vrm-api.js"
_WWW_PATH = str(Path(__file__).parent / "www")

# NOTE: async_reload_entry und der Update Listener sind entfernt.

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Victron VRM component."""

    # www-Verzeichnis als statischen HTTP-Pfad registrieren
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths(
            [StaticPathConfig(_LOVELACE_CARD_URL.rsplit("/", 1)[0], _WWW_PATH, False)]
        )
    except (ImportError, AttributeError):
        hass.http.register_static_path(
            _LOVELACE_CARD_URL.rsplit("/", 1)[0], _WWW_PATH, cache_headers=False
        )

    # Lovelace-Ressource registrieren, sobald HA vollständig gestartet ist
    from homeassistant.helpers.start import async_at_start

    @callback
    def _schedule_resource_registration(hass: HomeAssistant) -> None:
        hass.async_create_task(_async_register_lovelace_resource(hass))

    async_at_start(hass, _schedule_resource_registration)

    return True


async def _async_register_lovelace_resource(hass: HomeAssistant) -> None:
    """Lovelace-Ressource für die Victron VRM API Card registrieren / aktualisieren."""
    try:
        from homeassistant.components.lovelace import _STORAGE_KEY  # noqa: F401
    except ImportError:
        pass

    try:
        lovelace_data = hass.data.get("lovelace")
        if not lovelace_data:
            _LOGGER.debug("Lovelace nicht geladen – übersprungen")
            return

        # In HA 2023+ ist lovelace_data ein LovelaceData-Objekt mit .resources-Attribut.
        # In älteren Versionen war es ein Dict mit "resources"-Key.
        if hasattr(lovelace_data, "resources"):
            resources = lovelace_data.resources
        elif isinstance(lovelace_data, dict):
            resources = lovelace_data.get("resources")
        else:
            resources = None

        if resources is None:
            _LOGGER.debug(
                "Lovelace läuft im YAML-Modus – bitte Ressource manuell hinzufügen: %s",
                _LOVELACE_CARD_URL,
            )
            return

        # Basis-URL ohne ?v=... für Vergleich
        _base_url = _LOVELACE_CARD_URL.split("?")[0]

        # Alle existierenden Einträge mit gleicher Basis-URL finden
        existing = [
            item for item in resources.async_items()
            if item.get("url", "").split("?")[0] == _base_url
        ]

        # Wenn bereits die exakt richtige URL existiert: nichts tun
        if any(item.get("url") == _LOVELACE_CARD_URL for item in existing):
            return

        # Alte Einträge löschen (verhindert doppelte customElements.define-Aufrufe)
        for item in existing:
            try:
                await resources.async_delete_item(item["id"])
                _LOGGER.info("Alter Lovelace-Ressourcen-Eintrag entfernt: %s", item.get("url"))
            except Exception as del_exc:  # noqa: BLE001
                _LOGGER.warning("Konnte alten Eintrag nicht löschen: %s", del_exc)

        # Neuen Eintrag anlegen
        await resources.async_create_item({"res_type": "module", "url": _LOVELACE_CARD_URL})
        _LOGGER.info(
            "Victron VRM API Card als Lovelace-Ressource registriert: %s", _LOVELACE_CARD_URL
        )
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning(
            "Automatische Lovelace-Ressourcenregistrierung fehlgeschlagen: %s", exc
        )

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
