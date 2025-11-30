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
    CONF_TANK_INSTANCE,
    CONF_SOLAR_CHARGER_INSTANCE,
    DEFAULT_SCAN_INTERVAL_BATTERY,
    DEFAULT_SCAN_INTERVAL_OVERALL,
    DEFAULT_SCAN_INTERVAL_MULTI,
    DEFAULT_SCAN_INTERVAL_PV_INVERTER,
    DEFAULT_SCAN_INTERVAL_TANK,
    DEFAULT_SCAN_INTERVAL_SOLAR_CHARGER,
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

                    # Standard-Verhalten für Widgets (z.B. BatterySummary, PVInverterStatus, TankSummary):
                    if "records" in data:
                        return data.get("records", {})
                        
                    return data 

        except aiohttp.ClientError as err:
            _LOGGER.error("Verbindungsfehler beim Abrufen der Daten für %s: %s", self.endpoint, err)
            raise UpdateFailed(f"Verbindungsfehler: {err}")
        except Exception as err:
            _LOGGER.error("Unbekannter Fehler beim Abrufen der Daten für %s: %s", self.endpoint, err)
            raise UpdateFailed(f"Unbekannter Fehler: {err}")


# --- 2. Hilfsfunktion zur ID-Verarbeitung -----------------------------------------
def _parse_instance_ids(config_string: str) -> list[int]:
    """Parses a comma-separated string of instance IDs into a list of unique integers."""
    if not config_string:
        return []
    
    ids = set()
    for part in config_string.split(','):
        try:
            # Entferne Leerzeichen und versuche die Umwandlung
            instance_id = int(part.strip())
            # 0 ist der Standard/Deaktiviert-Wert, nur > 0 hinzufügen
            if instance_id > 0:
                ids.add(instance_id)
        except ValueError:
            _LOGGER.warning("Ungültige Instanz-ID '%s' in der Konfiguration ignoriert.", part.strip())
            continue
    return sorted(list(ids))


# --- 3. Setup-Funktion -----------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up VRM sensors from a config entry."""

    config_data = hass.data[DOMAIN][entry.entry_id]

    site_id = config_data[CONF_SITE_ID]
    token = config_data[CONF_TOKEN]
    
    # Instance IDs als String-Listen abrufen und parsen
    battery_instance_ids = _parse_instance_ids(config_data.get(CONF_BATTERY_INSTANCE, ""))
    multi_instance_ids = _parse_instance_ids(config_data.get(CONF_MULTI_INSTANCE, ""))
    pv_inverter_instance_ids = _parse_instance_ids(config_data.get(CONF_PV_INVERTER_INSTANCE, ""))
    tank_instance_ids = _parse_instance_ids(config_data.get(CONF_TANK_INSTANCE, ""))
    solar_charger_instance_ids = _parse_instance_ids(config_data.get(CONF_SOLAR_CHARGER_INSTANCE, ""))
    
    
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

    # Dictionary, um Koordinatoren und Geräte-Infos pro Instanz-ID zu speichern
    device_data = {
        "battery": {},
        "multi": {},
        "pv_inverter": {},
        "tank": {},
        "solar_charger": {}
    }

    # Definiere das Hub-Gerät (Hauptgerät)
    hub_device_info = { 
        "identifiers": {(DOMAIN, site_id)},
        "name": f"VRM Site {site_id}",
        "manufacturer": "Victron VRM API",
        "model": "VRM Hub",
    }
    
    # Definiere das Overall Stats Gerät (WIEDER HINZUGEFÜGT)
    overall_device_info = {
        "identifiers": {(DOMAIN, f"{site_id}_overall")},
        "name": "Stats Overall",
        "manufacturer": "Victron VRM API",
        "model": "Overall Statistics",
        "via_device": (DOMAIN, site_id),
    }
    
    # Temporäre Liste aller dynamischen Koordinatoren für den initialen Refresh
    dynamic_coordinators = []

    # --- Initialisiere dynamische Koordinatoren und Geräte-Infos pro Instanz ---
    
    # 1. Batterien
    for instance_id in battery_instance_ids:
        battery_endpoint = f"widgets/BatterySummary?instance={instance_id}"
        coord_name = f"VRM Battery {instance_id} Summary"
        battery_summary_coord = VrmDataCoordinator(
            hass, site_id, token, battery_endpoint, coord_name, DEFAULT_SCAN_INTERVAL_BATTERY
        )
        dynamic_coordinators.append(battery_summary_coord)
        device_data["battery"][instance_id] = {
            'coordinator': battery_summary_coord,
            'device_info': {
                "identifiers": {(DOMAIN, f"{site_id}_battery_{instance_id}")},
                "name": f"Battery {instance_id}",
                "manufacturer": "Victron VRM API",
                "model": f"instance_id {instance_id}",
                "via_device": (DOMAIN, site_id),
            }
        }

    # 2. MultiPlus
    for instance_id in multi_instance_ids:
        multi_status_endpoint = f"widgets/Status?instance={instance_id}"
        coord_name = f"VRM MultiPlus {instance_id} Status"
        multi_status_coord = VrmDataCoordinator(
            hass, site_id, token, multi_status_endpoint, coord_name, DEFAULT_SCAN_INTERVAL_MULTI
        )
        dynamic_coordinators.append(multi_status_coord)
        device_data["multi"][instance_id] = {
            'coordinator': multi_status_coord,
            'device_info': {
                "identifiers": {(DOMAIN, f"{site_id}_multiplus_{instance_id}")},
                "name": f"MultiPlus {instance_id}",
                "manufacturer": "Victron VRM API",
                "model": f"instance_id {instance_id}",
                "via_device": (DOMAIN, site_id),
            }
        }
        
    # 3. PV Inverter
    for instance_id in pv_inverter_instance_ids:
        pv_inverter_endpoint = f"widgets/PVInverterStatus?instance={instance_id}"
        coord_name = f"VRM PV Inverter {instance_id} Status"
        pv_inverter_coord = VrmDataCoordinator(
            hass, site_id, token, pv_inverter_endpoint, coord_name, DEFAULT_SCAN_INTERVAL_PV_INVERTER
        )
        dynamic_coordinators.append(pv_inverter_coord)
        device_data["pv_inverter"][instance_id] = {
            'coordinator': pv_inverter_coord,
            'device_info': {
                "identifiers": {(DOMAIN, f"{site_id}_pvinverter_{instance_id}")},
                "name": f"PV Inverter {instance_id}",
                "manufacturer": "Victron VRM API",
                "model": f"instance_id {instance_id}",
                "via_device": (DOMAIN, site_id),
            }
        }

    # 4. Tank
    for instance_id in tank_instance_ids:
        tank_endpoint = f"widgets/TankSummary?instance={instance_id}"
        coord_name = f"VRM Tank {instance_id} Summary"
        tank_coord = VrmDataCoordinator(
            hass, site_id, token, tank_endpoint, coord_name, DEFAULT_SCAN_INTERVAL_TANK
        )
        dynamic_coordinators.append(tank_coord)
        device_data["tank"][instance_id] = {
            'coordinator': tank_coord,
            'device_info': {
                "identifiers": {(DOMAIN, f"{site_id}_tank_{instance_id}")},
                "name": f"Tank {instance_id}",
                "manufacturer": "Victron VRM API",
                "model": f"instance_id {instance_id}",
                "via_device": (DOMAIN, site_id),
            }
        }

    # 5. Solar Charger
    for instance_id in solar_charger_instance_ids:
        solar_charger_endpoint = f"widgets/SolarChargerSummary?instance={instance_id}"
        coord_name = f"VRM Solar Charger {instance_id} Summary"
        solar_charger_coord = VrmDataCoordinator(
            hass, site_id, token, solar_charger_endpoint, coord_name, DEFAULT_SCAN_INTERVAL_SOLAR_CHARGER
        )
        dynamic_coordinators.append(solar_charger_coord)
        device_data["solar_charger"][instance_id] = {
            'coordinator': solar_charger_coord,
            'device_info': {
                "identifiers": {(DOMAIN, f"{site_id}_solarcharger_{instance_id}")},
                "name": f"Solar Charger {instance_id}",
                "manufacturer": "Victron VRM API",
                "model": f"instance_id {instance_id}",
                "via_device": (DOMAIN, site_id),
            }
        }
    
    # Initialen Refresh ausführen
    for coordinator in [overall_stats_coord, stats_coord] + dynamic_coordinators:
        try:
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.warning("Initialer Refresh des %s Koordinators fehlgeschlagen: %s", coordinator.name, err)


    entities: list[SensorEntity] = []


    # --- 1. Battery Summary Sensoren ---
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

    for instance_id, data in device_data["battery"].items():
        coord = data['coordinator']
        dev_info = data['device_info']
        if coord.data:
            for key, (data_id, name, device_class, state_class, unit, icon) in battery_sensors_config.items():
                entities.append(
                    VrmBatterySummarySensor(
                        coord, site_id, 
                        f"{key}_{instance_id}", 
                        data_id, 
                        f"{name} (Batt {instance_id})", 
                        device_class, state_class, unit, icon, dev_info
                    )
                )
            entities.append(
                VrmBatteryPowerSensor(
                    coord, site_id, 
                    f"{power_sensor_key}_{instance_id}", 
                    f"{power_sensor_name} (Batt {instance_id})", 
                    dev_info
                )
            )

    # --- 2. Battery Additional Stats Sensoren ---
    additional_stats = {
        "Bc": ("Battery to Consumers Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down"),
        "Bg": ("Battery to Grid Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down"), 
    }

    if stats_coord.data:
        for instance_id, data in device_data["battery"].items():
            dev_info = data['device_info']
            for json_key, (name, device_class, icon) in additional_stats.items():
                data_path = ["totals", json_key]
                entities.append(
                    VrmOverallStatsSensor(
                        stats_coord, site_id, f"stats_{json_key}_{instance_id}", data_path, f"{name} (Batt {instance_id})",
                        device_class, SensorStateClass.TOTAL_INCREASING, "kWh", icon, dev_info 
                    )
                )

    # --- 3. MultiPlus Status Sensoren ---
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

    for instance_id, data in device_data["multi"].items():
        coord = data['coordinator']
        dev_info = data['device_info']
        if coord.data:
            for key, (data_id, name, device_class, state_class, unit, icon) in multi_status_sensors_config.items():
                entities.append(
                    VrmMultiStatusSensor(
                        coord, site_id, f"{key}_{instance_id}", data_id, f"{name} (Multi {instance_id})", 
                        device_class, state_class, unit, icon, dev_info
                    )
                )
            entities.append(
                VrmMultiPlusDCPowerSensor(
                    coord, site_id, f"{multi_dc_power_key}_{instance_id}", f"{multi_dc_power_name} (Multi {instance_id})", dev_info
                )
            )

    # --- 3.5. MultiPlus Additional Stats Sensoren ---
    multi_additional_stats = {
        "Gc": ("Grid to Consumers Today", SensorDeviceClass.ENERGY, "mdi:transmission-tower"),
        "Gb": ("Grid to Battery Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down"),
    }

    if stats_coord.data:
        for instance_id, data in device_data["multi"].items():
            dev_info = data['device_info']
            for json_key, (name, device_class, icon) in multi_additional_stats.items():
                data_path = ["totals", json_key]
                entities.append(
                    VrmOverallStatsSensor(
                        stats_coord, site_id, f"stats_{json_key}_{instance_id}", data_path, f"{name} (Multi {instance_id})",
                        device_class, SensorStateClass.TOTAL_INCREASING, "kWh", icon, dev_info
                    )
                )

    # --- 3.6. PV Inverter Additional Stats Sensoren ---
    pv_additional_stats = {
        "Pc": ("PV to Consumers Today", SensorDeviceClass.ENERGY, "mdi:solar-power-variant-outline"),
        "Pb": ("PV to Battery Today", SensorDeviceClass.ENERGY, "mdi:battery-arrow-down-outline"),
        "Pg": ("PV to Grid Today", SensorDeviceClass.ENERGY, "mdi:home-export-outline"),          
    }

    if stats_coord.data:
        for instance_id, data in device_data["pv_inverter"].items():
            dev_info = data['device_info']
            for json_key, (name, device_class, icon) in pv_additional_stats.items():
                data_path = ["totals", json_key]
                entities.append(
                    VrmOverallStatsSensor(
                        stats_coord, site_id, f"stats_{json_key}_{instance_id}", data_path, f"{name} (PV {instance_id})",
                        device_class, SensorStateClass.TOTAL_INCREASING, "kWh", icon, dev_info 
                    )
                )
            entities.append(
                VrmPvTotalTodaySensor(
                    stats_coord, site_id, f"pv_total_today_{instance_id}", f"PV Total Today (PV {instance_id})", dev_info
                )
            )
        
    # --- 3.7. PV Inverter Sensoren Leistung ---
    pv_inverter_sensors_config = {
        "ac_voltage_l1": ("203", "L1 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
        "ac_current_l1": ("204", "L1 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
        "ac_power_l1":   ("205", "L1 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:solar-power"),
        "ac_energy_l1":  ("206", "L1 Energy",  SensorDeviceClass.ENERGY,  SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-panel"),
        "ac_voltage_l2": ("207", "L2 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
        "ac_current_l2": ("208", "L2 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
        "ac_power_l2":   ("209", "L2 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:solar-power"),
        "ac_energy_l2":  ("210", "L2 Energy",  SensorDeviceClass.ENERGY,  SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-panel"),
        "ac_voltage_l3": ("211", "L3 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
        "ac_current_l3": ("212", "L3 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
        "ac_power_l3":   ("213", "L3 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:solar-power"),
        "ac_energy_l3":  ("214", "L3 Energy",  SensorDeviceClass.ENERGY,  SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-panel"),
        "status_code":   ("246", "Status",     None,                     None,                          None, "mdi:list-status"),
    }

    for instance_id, data in device_data["pv_inverter"].items():
        coord = data['coordinator']
        dev_info = data['device_info']
        if coord.data and coord.data.get("data"):
            actual_data = coord.data.get("data", {})
            for key, (data_id, name, device_class, state_class, unit, icon) in pv_inverter_sensors_config.items():
                if data_id in actual_data:
                    entities.append(
                        VrmPvInverterSensor(
                            coord, site_id, f"{key}_{instance_id}", data_id, f"{name} (PV {instance_id})", 
                            device_class, state_class, unit, icon, dev_info
                        )
                    )

    # --- 3.8. Tank Sensoren ---
    tank_sensors_config = {
        "level":     ("330", "Level",     None,                     SensorStateClass.MEASUREMENT, "%",  "mdi:cup-water"),
        "remaining": ("331", "Remaining", SensorDeviceClass.VOLUME, SensorStateClass.TOTAL, "m³", "mdi:cup-water"), 
        "capacity":  ("328", "Capacity",  SensorDeviceClass.VOLUME, SensorStateClass.TOTAL, "m³", "mdi:beaker"),      
        "status":    ("443", "Status",    None,                     None,                         None, "mdi:list-status"),
        "type":      ("329", "Type",      None,                     None,                         None, "mdi:information-outline"),
        "name":      ("638", "Custom Name", None,                   None,                         None, "mdi:tag-text"),
    }

    for instance_id, data in device_data["tank"].items():
        coord = data['coordinator']
        dev_info = data['device_info']
        if coord.data and coord.data.get("data"):
            actual_tank_data = coord.data.get("data", {})
            for key, (data_id, name, device_class, state_class, unit, icon) in tank_sensors_config.items():
                if str(data_id) in actual_tank_data:
                    entities.append(
                        VrmTankSensor(
                            coord, site_id, f"{key}_{instance_id}", data_id, f"{name} (Tank {instance_id})", 
                            device_class, state_class, unit, icon, dev_info
                        )
                    )

    # --- 3.9. Solar Charger Sensoren ---
    solar_charger_sensors_config = {
        "battery_watts":   ("107", "Battery Watts",     SensorDeviceClass.POWER,     SensorStateClass.MEASUREMENT,      "W",   "mdi:battery-charging-90"),
        "battery_voltage": ("81",  "Battery Voltage",   SensorDeviceClass.VOLTAGE,   SensorStateClass.MEASUREMENT,      "V",   "mdi:current-dc"),
        "charge_state":    ("85",  "Charge State",      None,                        None,                              None,  "mdi:solar-power"),
        "battery_temp":    ("83",  "Battery Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT,  "°C",  "mdi:thermometer"),
        "yield_today":     ("94",  "Yield Today",       SensorDeviceClass.ENERGY,    SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-power"),
        "yield_yesterday": ("96",  "Yield Yesterday",   SensorDeviceClass.ENERGY,    SensorStateClass.TOTAL_INCREASING, "kWh", "mdi:solar-panel"),
        "relay_status":    ("90",  "Relay Status",      None,                        None,                              None,  "mdi:electric-switch"),
    }

    for instance_id, data in device_data["solar_charger"].items():
        coord = data['coordinator']
        dev_info = data['device_info']
        if coord.data and coord.data.get("data"):
            actual_sc_data = coord.data.get("data", {})
            for key, (data_id, name, device_class, state_class, unit, icon) in solar_charger_sensors_config.items():
                if str(data_id) in actual_sc_data:
                    entities.append(
                        VrmSolarChargerSensor(
                            coord, site_id, f"{key}_{instance_id}", data_id, f"{name} (SC {instance_id})", 
                            device_class, state_class, unit, icon, dev_info
                        )
                    )

    # --- 4. Overall Stats Sensoren (Nutzt wieder overall_device_info) ---------------------
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
                        "kWh", icon, overall_device_info # WIEDER HERGESTELLT
                    )
                )

    async_add_entities(entities, True)


# --- 5. Basisklasse für Sensoren -----------
class VrmBaseSensor(CoordinatorEntity, SensorEntity):
    """Basisklasse für alle VRM Sensoren."""
    def __init__(self, coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator)
        
        unique_slug = slugify(f"{device_info['name']}_{key}")
        self._attr_unique_id = f"vrm_v2_{site_id}_{unique_slug}"
        
        self._attr_name = name
        self.entity_id = f"sensor.vrm_{slugify(name)}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = device_info 

# --- 6. Battery Summary Sensor ---------------------------------------------------
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

# --- 6.5. Calculated Battery Power Sensor --------------------------------------
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

# --- 6.6. Calculated MultiPlus DC Power Sensor --------------------------------------
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

# --- 6.7. Calculated PV Total Today Sensor --------------------------------------
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
        
        try:
            pc = float(totals.get(self.PC_KEY, 0.0))
            pb = float(totals.get(self.PB_KEY, 0.0))
            pg = float(totals.get(self.PG_KEY, 0.0))
        except (TypeError, ValueError):
            _LOGGER.warning("Mindestens ein PV-Wert (Pc, Pb, Pg) ist nicht als Zahl vorhanden.")
            return 0.0

        total_pv = pc + pb + pg
        
        return round(total_pv, 3)

# --- 7. Overall Stats Sensor -----------------------------------------------------
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
            
# --- 8. MultiPlus Status Sensor ----------------------------------------------
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

# --- 9. PV Inverter Sensor (VOM NUTZER GEWÜNSCHTE VERSION) --------------------
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

# --- 10. Tank Sensor ----------------------------------------------------------
class VrmTankSensor(VrmBaseSensor):
    """Represents a single value from the VRM Tank Status data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info)
        self._data_id = data_id
        
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        attr = data.get(str(self._data_id), {}) 
        if not attr:
            return None
            
        value_float = attr.get("valueFloat")
        if value_float is not None:
            return value_float
            
        value_enum = attr.get("nameEnum")
        if value_enum is not None:
            return value_enum
        return attr.get("value")

# --- 11. Solar Charger Sensor -------------------------------------------------
class VrmSolarChargerSensor(VrmBaseSensor):
    """Represents a single value from the VRM Solar Charger Status data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info)
        self._data_id = data_id
        
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        attr = data.get(str(self._data_id), {}) 
        if not attr:
            return None
            
        value_float = attr.get("valueFloat")
        if value_float is not None:
            return value_float
            
        value_enum = attr.get("nameEnum")
        if value_enum is not None:
            return value_enum
        return attr.get("value")
