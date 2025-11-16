"""Platform for sensor entities from Victron VRM."""
import logging
from datetime import timedelta
import aiohttp

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_SITE_ID,
    CONF_TOKEN,
    CONF_BATTERY_INSTANCE,
    CONF_MULTI_INSTANCE,
    DEFAULT_SCAN_INTERVAL_BATTERY,
    DEFAULT_SCAN_INTERVAL_OVERALL,
    DEFAULT_SCAN_INTERVAL_MULTI,
)

_LOGGER = logging.getLogger(__name__)


# --- 1. VRM Data Coordinator ---------------------------------------------------
class VrmDataCoordinator(DataUpdateCoordinator):
    """Manages the fetching of VRM data for a single endpoint."""

    def __init__(self, hass: HomeAssistant, site_id: str, token: str, endpoint: str, name: str, interval: int):
        """Initialize the coordinator."""
        self.site_id = site_id
        self.token = token
        self.endpoint = endpoint
        self.base_url = "https://vrmapi.victronenergy.com/v2/installations/"

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        url = f"{self.base_url}{self.site_id}/{self.endpoint}"
        headers = {"X-Authorization": f"Token {self.token}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status not in (200, 204):
                        _LOGGER.error("API-Fehler bei %s: Status %d", self.endpoint, response.status)
                        raise UpdateFailed(f"API-Fehler bei {self.endpoint}: Status {response.status}")
                    
                    if response.status == 204:
                        return None 

                    data = await response.json()

                    if "records" in data:
                        return data.get("records", {})
                    return data 

        except aiohttp.ClientError as err:
            _LOGGER.error("Verbindungsfehler beim Abrufen der Daten für %s: %s", self.endpoint, err)
            raise UpdateFailed(f"Verbindungsfehler: {err}")
        except Exception as err:
            _LOGGER.error("Unbekannter Fehler beim Abrufen der Daten für %s: %s", self.endpoint, err)
            raise UpdateFailed(f"Unbekannter Fehler: {err}")


# --- 2. Statische Konfigurationen (Fix für C901/E501) ---

BATTERY_SENSORS_CONFIG = {
    "soc": ("51", "State of charge", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, "%", "mdi:battery-50"),
    "voltage": ("47", "Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:current-dc"),
    "current": ("49", "Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-dc"),
    "consumed": ("50", "Consumed Amphours", None, SensorStateClass.TOTAL_INCREASING, "Ah", "mdi:battery-alert-variant-outline"),
    "ttg": ("52", "Time to go", None, SensorStateClass.MEASUREMENT, "h", "mdi:timer-sand"),
    "temp": ("115", "Battery temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer"),
    "min_cell_voltage": ("173", "Minimum Cell Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:battery-low"),
    "max_cell_voltage": ("174", "Maximum Cell Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:battery-high"),
}

MULTI_STATUS_SENSORS_CONFIG = {
    "ac_in_voltage": ("8", "AC Input Voltage L1", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:transmission-tower"),
    "ac_in_power": ("17", "AC Input Power L1", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:transmission-tower"),
    "ac_out_voltage": ("20", "AC Output Voltage L1", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:power-socket-eu"),
    "ac_out_power": ("29", "AC Output Power L1", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:power-socket-eu"),
    "dc_voltage": ("32", "DC Bus Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:current-dc"),
    "dc_current": ("33", "DC Bus Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-dc"),
    "inverter_state": ("40", "VE.Bus State", None, None, None, "mdi:flash"),
    "multi_temp": ("521", "MultiPlus Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer"),
}

OVERALL_PERIODS = ["today", "week", "month", "year"]
OVERALL_METRICS = {
    "total_solar_yield": ("Solar Yield", SensorDeviceClass.ENERGY, "mdi:solar-power"),
    "total_consumption": ("Consumption", SensorDeviceClass.ENERGY, "mdi:power-plug"),
    "grid_history_from": ("Grid Energy In", SensorDeviceClass.ENERGY, "mdi:transmission-tower"),
    "grid_history_to": ("Grid Energy Out", SensorDeviceClass.ENERGY, "mdi:home-export-outline"),
}

# --- 3. Setup-Funktion -----------------------------------------------------------

def _get_device_info(site_id: str, name: str, model: str, suffix: str):
    """Generates the device info dictionary for an entity group."""
    return {
        "identifiers": {(DOMAIN, f"{site_id}{suffix}")},
        "name": name,
        "manufacturer": "Victron VRM API",
        "model": model,
        "via_device": (DOMAIN, site_id),
    }

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up VRM sensors from a config entry."""

    config_data = hass.data[DOMAIN][entry.entry_id]

    # Daten aus der Config extrahieren
    site_id = config_data[CONF_SITE_ID]
    token = config_data[CONF_TOKEN]
    battery_instance_id = config_data.get(CONF_BATTERY_INSTANCE, 0)
    multi_instance_id = config_data.get(CONF_MULTI_INSTANCE, 0)

    overall_endpoint = "overallstats"

    # Dynamische Erstellung der Endpoints (E501 Fix durch Umbruch)
    battery_endpoint = (
        f"widgets/BatterySummary?instance={battery_instance_id}" 
        if battery_instance_id 
        else "widgets/BatterySummary"
    )
    multi_status_endpoint = (
        f"widgets/Status?instance={multi_instance_id}" 
        if multi_instance_id 
        else "widgets/Status"
    )

    # Initialisiere Koordinatoren
    battery_summary_coord = VrmDataCoordinator(
        hass, site_id, token, battery_endpoint, "VRM Battery Summary", 
        DEFAULT_SCAN_INTERVAL_BATTERY
    )
    overall_stats_coord = VrmDataCoordinator(
        hass, site_id, token, overall_endpoint, "VRM Overall Stats", 
        DEFAULT_SCAN_INTERVAL_OVERALL
    )
    multi_status_coord = VrmDataCoordinator(
        hass, site_id, token, multi_status_endpoint, "VRM MultiPlus Status", 
        DEFAULT_SCAN_INTERVAL_MULTI
    )
    
    # Initialen Refresh ausführen und Fehler abfangen
    coordinators = [battery_summary_coord, overall_stats_coord, multi_status_coord]
    
    for coordinator in coordinators:
        try:
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.warning(
                "Initialer Refresh des %s Koordinators fehlgeschlagen: %s", 
                coordinator.name, err
            )

    entities: list[SensorEntity] = []

    # Definiere Geräte-Infos (Verwendung der Hilfsfunktion)
    battery_device_info = _get_device_info(
        site_id, "VRM Battery Summary", "Battery Summary", "_battery"
    )
    multi_device_info = _get_device_info(
        site_id, "VRM MultiPlus Status", "MultiPlus Status", "_multiplus"
    )
    overall_device_info = _get_device_info(
        site_id, "VRM Overall Stats", "Overall Statistics", "_overall"
    )

    # --- Entitäten-Erstellung ---
    
    if battery_summary_coord.data:
        for key, (data_id, name, device_class, state_class, unit, icon) in BATTERY_SENSORS_CONFIG.items():
            entities.append(
                VrmBatterySummarySensor(
                    battery_summary_coord, site_id, key, data_id, name, device_class, 
                    state_class, unit, icon, battery_device_info
                )
            )

    if multi_status_coord.data:
        for key, (data_id, name, device_class, state_class, unit, icon) in MULTI_STATUS_SENSORS_CONFIG.items():
            entities.append(
                VrmMultiStatusSensor(
                    multi_status_coord, site_id, key, data_id, name, device_class, 
                    state_class, unit, icon, multi_device_info
                )
            )

    if overall_stats_coord.data:
        for period in OVERALL_PERIODS:
            for metric_key, (metric_name, device_class, icon) in OVERALL_METRICS.items():
                key = f"{period}_{metric_key}"
                name = f"{period.capitalize()} {metric_name}"
                data_path = [period, "totals", metric_key]
                entities.append(
                    VrmOverallStatsSensor(
                        overall_stats_coord, site_id, key, data_path, name, device_class,
                        SensorStateClass.TOTAL_INCREASING, "kWh", icon, overall_device_info
                    )
                )

    async_add_entities(entities, True)


# --- 4. Basisklasse für Sensoren -------------------------------------------------

class VrmBaseSensor(CoordinatorEntity, SensorEntity):
    """Basisklasse für alle VRM Sensoren."""

    def __init__(self, coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator)
        self._attr_unique_id = f"{site_id}_{device_info['name'].lower().replace(' ', '_')}_{key}"
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = device_info


# --- 5. Battery Summary Sensor ---------------------------------------------------

class VrmBatterySummarySensor(VrmBaseSensor):
    """Represents a single value from the VRM Battery Summary data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info)
        self._data_id = data_id
    
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        attr = data.get(self._data_id, {})
        return attr.get("valueFloat")


# --- 6. Overall Stats Sensor -----------------------------------------------------

class VrmOverallStatsSensor(VrmBaseSensor):
    """Represents a single value from the VRM Overall Stats data."""
    def __init__(self, coordinator, site_id, key, data_path, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info)
        self._data_path = data_path
    
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        value = self.coordinator.data
        try:
            for key in self._data_path:
                value = value[key]
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, str):
                return float(value)
            return None
        except (KeyError, TypeError, ValueError):
            return None
            

# --- 7. MultiPlus Status Sensor ----------------------------------------------

class VrmMultiStatusSensor(VrmBaseSensor):
    """Represents a single value from the VRM MultiPlus Status data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info)
        self._data_id = data_id
    
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        data_item = data.get(self._data_id, {})
        if not data_item:
            return None
        value_float = data_item.get("valueFloat")
        if value_float is not None:
            return value_float
        value_enum = data_item.get("nameEnum")
        if value_enum is not None:
            return value_enum
        return data_item.get("value")
