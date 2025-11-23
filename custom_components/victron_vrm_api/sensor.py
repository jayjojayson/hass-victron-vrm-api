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
from homeassistant.util import slugify
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
    CONF_PV_INVERTER_INSTANCE,
    DEFAULT_SCAN_INTERVAL_BATTERY,
    DEFAULT_SCAN_INTERVAL_OVERALL,
    DEFAULT_SCAN_INTERVAL_MULTI,
    DEFAULT_SCAN_INTERVAL_PV_INVERTER,
)

_LOGGER = logging.getLogger(__name__)


# --- 1. VRM Data Coordinator ----------------------------------------------------
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

                    # WICHTIG: Wenn 'totals' enthalten ist (für stats Endpoint), gib alles zurück.
                    if "totals" in data:
                        return data

                    # Standard-Verhalten für Widgets (z.B. BatterySummary, PVInverterStatus):
                    if "records" in data:
                        return data.get("records", {})
                        
                    return data 

        except aiohttp.ClientError as err:
            _LOGGER.error("Verbindungsfehler beim Abrufen der Daten für %s: %s", self.endpoint, err)
            raise UpdateFailed(f"Verbindungsfehler: {err}")
        except Exception as err:
            _LOGGER.error("Unbekannter Fehler beim Abrufen der Daten für %s: %s", self.endpoint, err)
            raise UpdateFailed(f"Unbekannter Fehler: {err}")


# --- 2. Setup-Funktion -----------------------------------------------------------

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up VRM sensors from a config entry."""

    config_data = hass.data[DOMAIN][entry.entry_id]

    site_id = config_data[CONF_SITE_ID]
    token = config_data[CONF_TOKEN]
    
    # Instance IDs auf 0 gesetzt, wenn nicht konfiguriert
    battery_instance_id = config_data.get(CONF_BATTERY_INSTANCE, 0)
    multi_instance_id = config_data.get(CONF_MULTI_INSTANCE, 0) 
    pv_inverter_instance_id = config_data.get(CONF_PV_INVERTER_INSTANCE, 0) 
    
    
    # Endpoints definieren (Statische Endpunkte)
    overall_endpoint = "overallstats"
    stats_endpoint = "stats?type=kwh&interval=15mins"

    # Initialisiere Koordinatoren (Immer vorhanden)
    overall_stats_coord = VrmDataCoordinator(
        hass, site_id, token, overall_endpoint, "VRM Overall Stats", DEFAULT_SCAN_INTERVAL_OVERALL
    )
    stats_coord = VrmDataCoordinator(
        hass, site_id, token, stats_endpoint, "VRM Energy Stats", DEFAULT_SCAN_INTERVAL_OVERALL
    )

    # Initialisiere Koordinatoren (Bedingt: Nur wenn Instance ID größer 0)
    
    # Batterie
    battery_summary_coord = None
    if battery_instance_id != 0:
        battery_endpoint = f"widgets/BatterySummary?instance={battery_instance_id}"
        battery_summary_coord = VrmDataCoordinator(
            hass, site_id, token, battery_endpoint, "VRM Battery Summary", DEFAULT_SCAN_INTERVAL_BATTERY
        )

    # MultiPlus
    multi_status_coord = None
    if multi_instance_id != 0:
        multi_status_endpoint = f"widgets/Status?instance={multi_instance_id}"
        multi_status_coord = VrmDataCoordinator(
            hass, site_id, token, multi_status_endpoint, "VRM MultiPlus Status", DEFAULT_SCAN_INTERVAL_MULTI
        )
        
    # PV Inverter
    pv_inverter_coord = None
    if pv_inverter_instance_id != 0:
        pv_inverter_endpoint = f"widgets/PVInverterStatus?instance={pv_inverter_instance_id}"
        pv_inverter_coord = VrmDataCoordinator(
            hass, site_id, token, pv_inverter_endpoint, "VRM PV Inverter Status", DEFAULT_SCAN_INTERVAL_PV_INVERTER
        )
    
    # Initialen Refresh ausführen (dynamische Liste)
    coordinators = [overall_stats_coord, stats_coord]
    
    if battery_summary_coord:
        coordinators.append(battery_summary_coord)
    if multi_status_coord:
        coordinators.append(multi_status_coord)
    if pv_inverter_coord:
        coordinators.append(pv_inverter_coord)
    
    for coordinator in coordinators:
        try:
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.warning("Initialer Refresh des %s Koordinators fehlgeschlagen: %s", coordinator.name, err)


    entities: list[SensorEntity] = []

    # Definiere Geräte-Infos
    hub_device_info = {
        "identifiers": {(DOMAIN, site_id)},
        "name": f"VRM Site {site_id}",
        "manufacturer": "Victron VRM API",
        "model": "VRM Hub",
    }
    battery_device_info = {
        "identifiers": {(DOMAIN, f"{site_id}_battery")},
        "name": "Battery",
        "manufacturer": "Victron VRM API",
        "model": f"instance_id {battery_instance_id}",
        "via_device": (DOMAIN, site_id),
    }
    multi_device_info = {
        "identifiers": {(DOMAIN, f"{site_id}_multiplus")},
        "name": "MultiPlus",
        "manufacturer": "Victron VRM API",
        "model": f"instance_id {multi_instance_id}",
        "via_device": (DOMAIN, site_id),
    }
    pv_inverter_device_info = {
        "identifiers": {(DOMAIN, f"{site_id}_pvinverter")},
        "name": "PV Inverter",
        "manufacturer": "Victron VRM API",
        "model": f"instance_id {pv_inverter_instance_id}", 
        "via_device": (DOMAIN, site_id),
    }
    overall_device_info = {
        "identifiers": {(DOMAIN, f"{site_id}_overall")},
        "name": "Stats Overall",
        "manufacturer": "Victron VRM API",
        "model": "Overall Statistics",
        "via_device": (DOMAIN, site_id),
    }


    # --- 1. Battery Summary Sensoren ------------------------------------------------
    battery_sensors_config = {
        "soc": ("51", "State of charge", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, "%", "mdi:battery-50"),
        "voltage": ("47", "Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:current-dc"),
        "current": ("49", "Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-dc"),
        "consumed": ("50", "Consumed Amphours", None, SensorStateClass.TOTAL_INCREASING, "Ah", "mdi:battery-alert-variant-outline"),
        "ttg": ("52", "Time to go", None, SensorStateClass.MEASUREMENT, "h", "mdi:timer-sand"),
        "temp": ("115", "Battery Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer"),
        "min_cell_voltage": ("173", "Minimum Cell Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:battery-low"),
        "max_cell_voltage": ("174", "Maximum Cell Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:battery-high"),
    }
    
    power_sensor_key = "power"
    power_sensor_name = "Battery Power"

    # Hinzufügen der Sensoren nur, wenn der Koordinator existiert (Instance ID > 0)
    if battery_summary_coord and battery_summary_coord.data:
        for key, (data_id, name, device_class, state_class, unit, icon) in battery_sensors_config.items():
            entities.append(
                VrmBatterySummarySensor(
                    battery_summary_coord, site_id, key, data_id, name, device_class, state_class, unit, icon, battery_device_info
                )
            )
        entities.append(
            VrmBatteryPowerSensor(
                battery_summary_coord, site_id, power_sensor_key, power_sensor_name, battery_device_info
            )
        )

    # --- 2. Battery Additional Stats Sensoren (Bc, Bg) ---------------------------------
    additional_stats = {
        "Bc": ("Battery to Consumers Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down"),
        "Bg": ("Battery to Grid Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down"), 
    }

    if battery_summary_coord and stats_coord.data:
        for json_key, (name, device_class, icon) in additional_stats.items():
            data_path = ["totals", json_key]
            
            entities.append(
                VrmOverallStatsSensor(
                    stats_coord, 
                    site_id, 
                    f"stats_{json_key}",
                    data_path, 
                    name, 
                    device_class,
                    SensorStateClass.TOTAL_INCREASING, 
                    "kWh", 
                    icon, 
                    battery_device_info 
                )
            )

    # --- 3. MultiPlus Status Sensoren --------------------------------------------
    multi_status_sensors_config = {
        "ac_in_voltage": ("8", "AC Input Voltage L1", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:transmission-tower"),
        "ac_in_power": ("17", "AC Input Power L1", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:transmission-tower"),
        "ac_out_voltage": ("20", "AC Output Voltage L1", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:power-socket-eu"),
        "ac_out_power": ("29", "AC Output Power L1", SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "W", "mdi:power-socket-eu"),
        "dc_voltage": ("32", "DC Bus Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:current-dc"),
        "dc_current": ("33", "DC Bus Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-dc"),
        "inverter_state": ("40", "VE.Bus State", None, None, None, "mdi:flash"),
        "multi_temp": ("521", "MultiPlus Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer"),
    }
    
    multi_dc_power_key = "dc_power"
    multi_dc_power_name = "DC Bus Power"

    if multi_status_coord and multi_status_coord.data:
        for key, (data_id, name, device_class, state_class, unit, icon) in multi_status_sensors_config.items():
            entities.append(
                VrmMultiStatusSensor(
                    multi_status_coord, site_id, key, data_id, name, device_class, state_class, unit, icon, multi_device_info
                )
            )
        entities.append(
            VrmMultiPlusDCPowerSensor(
                multi_status_coord, site_id, multi_dc_power_key, multi_dc_power_name, multi_device_info
            )
        )

    # --- 3.5. MultiPlus Additional Stats Sensoren (Gc, Gb) ---------------------------------
    multi_additional_stats = {
        "Gc": ("Grid to Consumers Today", SensorDeviceClass.ENERGY, "mdi:transmission-tower"),
        "Gb": ("Grid to Battery Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down"),
    }

    if multi_status_coord and stats_coord.data:
        for json_key, (name, device_class, icon) in multi_additional_stats.items():
            data_path = ["totals", json_key]
            
            entities.append(
                VrmOverallStatsSensor(
                    stats_coord, 
                    site_id, 
                    f"stats_{json_key}",
                    data_path, 
                    name, 
                    device_class,
                    SensorStateClass.TOTAL_INCREASING, 
                    "kWh", 
                    icon, 
                    multi_device_info
                )
            )

    # --- 3.6. PV Inverter Additional Stats Sensoren (Pc, Pb, Pg) -----------------------
    # Diese Sensoren werden vom Vorhandensein des PV Inverter Coordinators abhängig gemacht.
    pv_additional_stats = {
        "Pc": ("PV to Consumers Today", SensorDeviceClass.ENERGY, "mdi:solar-power-variant-outline"),
        "Pb": ("PV to Battery Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down-outline"),
        "Pg": ("PV to Grid Today", SensorDeviceClass.ENERGY, "mdi:home-export-outline"),          
    }

    if pv_inverter_coord and stats_coord.data:
        for json_key, (name, device_class, icon) in pv_additional_stats.items():
            data_path = ["totals", json_key]
            
            entities.append(
                VrmOverallStatsSensor(
                    stats_coord, 
                    site_id, 
                    f"stats_{json_key}",
                    data_path, 
                    name, 
                    device_class,
                    SensorStateClass.TOTAL_INCREASING, 
                    "kWh", 
                    icon, 
                    pv_inverter_device_info 
                )
            )
        
        entities.append(
            VrmPvTotalTodaySensor(
                stats_coord,
                site_id,
                "pv_total_today",
                "PV Total Today",
                pv_inverter_device_info
            )
        )
        
    # --- 3.7. PV Inverter Sensoren Leistung (L1, L2, L3 dynamisch) ------------------------
    pv_inverter_sensors_config = {
        # L1
        "ac_voltage_l1": ("203", "L1 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
        "ac_current_l1": ("204", "L1 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
        "ac_power_l1":   ("205", "L1 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:solar-power"),
        "ac_energy_l1":  ("206", "L1 Energy",  SensorDeviceClass.ENERGY,  SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-panel"),
        # L2
        "ac_voltage_l2": ("207", "L2 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
        "ac_current_l2": ("208", "L2 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
        "ac_power_l2":   ("209", "L2 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:solar-power"),
        "ac_energy_l2":  ("210", "L2 Energy",  SensorDeviceClass.ENERGY,  SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-panel"),
        # L3
        "ac_voltage_l3": ("211", "L3 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
        "ac_current_l3": ("212", "L3 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
        "ac_power_l3":   ("213", "L3 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:solar-power"),
        "ac_energy_l3":  ("214", "L3 Energy",  SensorDeviceClass.ENERGY,  SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-panel"),
        # Status
        "status_code":   ("246", "Status",     None,                     None,                          None, "mdi:list-status"),
    }

    if pv_inverter_coord and pv_inverter_coord.data:
        # Wir holen uns die tatsächlichen Daten-Records (z.B. keys "203", "207", etc.)
        actual_data = pv_inverter_coord.data.get("data", {})
        
        for key, (data_id, name, device_class, state_class, unit, icon) in pv_inverter_sensors_config.items():
            # PRÜFUNG: Existiert diese Data-ID in der API-Antwort?
            # Wenn ja -> Sensor erstellen. Wenn nein -> überspringen.
            if data_id in actual_data:
                entities.append(
                    VrmPvInverterSensor(
                        pv_inverter_coord, site_id, key, data_id, name, device_class, state_class, unit, icon, pv_inverter_device_info
                    )
                )


    # --- 4. Overall Stats Sensoren --------------------------------------------------
    periods = ["today", "week", "month", "year"]
    metrics = {
        "total_solar_yield": ("Solar Yield", SensorDeviceClass.ENERGY, "mdi:solar-power"),
        "total_consumption": ("Consumption", SensorDeviceClass.ENERGY, "mdi:power-plug"),
        "grid_history_from": ("Grid Energy In", SensorDeviceClass.ENERGY, "mdi:transmission-tower"),
        "grid_history_to": ("Grid Energy Out", SensorDeviceClass.ENERGY, "mdi:home-export-outline"),
    }

    if overall_stats_coord.data:
        for period in periods:
            for metric_key, (metric_name, device_class, icon) in metrics.items():
                key = f"{period}_{metric_key}"
                name = f"{period.capitalize()} {metric_name}"
                data_path = [period, "totals", metric_key]
                entities.append(
                    VrmOverallStatsSensor(
                        overall_stats_coord, site_id, key, data_path, name, device_class,
                        SensorStateClass.TOTAL_INCREASING, 
                        "kWh", icon, overall_device_info
                    )
                )

    async_add_entities(entities, True)


# --- 3. Basisklasse für Sensoren -------------------------------------------------
class VrmBaseSensor(CoordinatorEntity, SensorEntity):
    """Basisklasse für alle VRM Sensoren."""
    def __init__(self, coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator)
        # vrm_v2_ stellt sicher, dass neue Entitätennamen vergeben werden 
        self._attr_unique_id = f"vrm_v2_{site_id}_{device_info['name'].lower().replace(' ', '_')}_{key}"
        self._attr_name = name
        self.entity_id = f"sensor.vrm_{slugify(name)}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = device_info 

# --- 4. Battery Summary Sensor ---------------------------------------------------
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

# --- 4.5. Calculated Battery Power Sensor --------------------------------------
class VrmBatteryPowerSensor(VrmBaseSensor):
    """Calculates Battery Power (Voltage * Current) from Battery Summary data."""
    
    VOLTAGE_DATA_ID = "47"
    CURRENT_DATA_ID = "49"

    def __init__(self, coordinator, site_id, key, name, device_info):
        super().__init__(
            coordinator, site_id, key, name, SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT, "W", None, device_info
        )

    @property
    def native_value(self) -> float:
        if not self.coordinator.data:
            return 0.0
        data = self.coordinator.data.get("data", {})
        voltage = data.get(self.VOLTAGE_DATA_ID, {}).get("valueFloat")
        current = data.get(self.CURRENT_DATA_ID, {}).get("valueFloat")

        if voltage is None or current is None:
            return 0.0
        try:
            return round(voltage * current, 2) 
        except (TypeError, ValueError):
            return 0.0

# --- 4.6. Calculated MultiPlus DC Power Sensor --------------------------------------
class VrmMultiPlusDCPowerSensor(VrmBaseSensor):
    """Calculates MultiPlus DC Power (Voltage * Current) from Multi Status data."""
    
    VOLTAGE_DATA_ID = "32"
    CURRENT_DATA_ID = "33"

    def __init__(self, coordinator, site_id, key, name, device_info):
        super().__init__(
            coordinator, site_id, key, name, SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT, "W", None, device_info
        )

    @property
    def native_value(self) -> float:
        if not self.coordinator.data:
            return 0.0
        data = self.coordinator.data.get("data", {})
        voltage = data.get(self.VOLTAGE_DATA_ID, {}).get("valueFloat")
        current = data.get(self.CURRENT_DATA_ID, {}).get("valueFloat")

        if voltage is None or current is None:
            return 0.0
        try:
            return round(voltage * current, 2) 
        except (TypeError, ValueError):
            return 0.0

# --- 4.7. Calculated PV Total Today Sensor --------------------------------------
class VrmPvTotalTodaySensor(VrmBaseSensor):
    """Calculates total PV energy produced today (Pc + Pb + Pg)."""
    
    PC_KEY = "Pc"
    PB_KEY = "Pb"
    PG_KEY = "Pg"

    def __init__(self, coordinator, site_id, key, name, device_info):
        super().__init__(
            coordinator, site_id, key, name, SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-power", device_info
        )

    @property
    def native_value(self) -> float:
        if not self.coordinator.data or "totals" not in self.coordinator.data:
            return 0.0
        
        totals = self.coordinator.data.get("totals", {})
        
        # Sicherstellen, dass alle Werte vorhanden und float-konvertierbar sind
        try:
            pc = float(totals.get(self.PC_KEY, 0.0))
            pb = float(totals.get(self.PB_KEY, 0.0))
            pg = float(totals.get(self.PG_KEY, 0.0))
        except (TypeError, ValueError):
            _LOGGER.warning("Mindestens ein PV-Wert (Pc, Pb, Pg) ist nicht als Zahl vorhanden.")
            return 0.0

        # Die Summe ist die Gesamt-PV-Erzeugung heute
        total_pv = pc + pb + pg
        
        return round(total_pv, 3)

# --- 5. Overall Stats Sensor -----------------------------------------------------
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
            return 0.0 
            
# --- 6. MultiPlus Status Sensor ----------------------------------------------
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

# --- 7. PV Inverter Sensor (UPDATED) ------------------------------------------
class VrmPvInverterSensor(VrmBaseSensor):
    """Represents a single value from the VRM PV Inverter Status data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info)
        self._data_id = data_id
        
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        attr = data.get(self._data_id, {})
        if not attr:
            return None
            
        # Logik analog zu MultiPlus Sensor erweitert für Status-Codes (Enum/String)
        value_float = attr.get("valueFloat")
        if value_float is not None:
            return value_float
            
        # Fallback für Status oder andere nicht-numerische Werte (z.B. ID 246)
        value_enum = attr.get("nameEnum")
        if value_enum is not None:
            return value_enum
        return attr.get("value")
