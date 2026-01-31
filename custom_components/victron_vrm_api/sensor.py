"""Platform for sensor entities from Victron VRM."""
import logging
from datetime import timedelta, datetime, timezone
import aiohttp
from typing import Any

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
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_SITE_ID,
    CONF_TOKEN,
    CONF_BATTERY_INSTANCE,
    CONF_MULTI_INSTANCE, 
    CONF_PV_INVERTER_INSTANCE,
    CONF_TANK_INSTANCE,
    CONF_SOLAR_CHARGER_INSTANCE,
    CONF_GRID_INSTANCE,
    DEFAULT_SCAN_INTERVAL_BATTERY,
    DEFAULT_SCAN_INTERVAL_OVERALL,
    DEFAULT_SCAN_INTERVAL_MULTI,
    DEFAULT_SCAN_INTERVAL_PV_INVERTER,
    DEFAULT_SCAN_INTERVAL_TANK,
    DEFAULT_SCAN_INTERVAL_SOLAR_CHARGER,
    DEFAULT_SCAN_INTERVAL_SYSTEM_OVERVIEW,
    DEFAULT_SCAN_INTERVAL_DIAGNOSTICS,
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
                    
                    # WICHTIG: System Overview hat eine 'records' -> 'devices' Struktur
                    if "records" in data and "devices" in data["records"]:
                        return data["records"]
                    
                    # WICHTIG: Diagnostics Endpoint liefert oft direkt 'records' oder eine Liste
                    if "records" in data:
                        return data["records"]
                    
                    # Fallback
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
            if instance_id >= 0:
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
    grid_instance_ids = _parse_instance_ids(config_data.get(CONF_GRID_INSTANCE, ""))
    
    
    # Endpoints definieren (Statische Endpunkte)
    overall_endpoint = "overallstats"
    stats_endpoint = "stats?type=kwh&interval=15mins"
    system_overview_endpoint = "system-overview"
    diagnostics_endpoint = "diagnostics?count=50"

    # Initialisiere Koordinatoren (Immer vorhanden)
    overall_stats_coord = VrmDataCoordinator(
        hass, site_id, token, overall_endpoint, "VRM Overall Stats", DEFAULT_SCAN_INTERVAL_OVERALL
    )
    stats_coord = VrmDataCoordinator(
        hass, site_id, token, stats_endpoint, "VRM Energy Stats", DEFAULT_SCAN_INTERVAL_OVERALL
    )
    # Coordinator für System Overview
    system_overview_coord = VrmDataCoordinator(
        hass, site_id, token, system_overview_endpoint, "VRM System Overview", DEFAULT_SCAN_INTERVAL_SYSTEM_OVERVIEW
    )
    # Coordinator für Diagnostics
    diagnostics_coord = VrmDataCoordinator(
        hass, site_id, token, diagnostics_endpoint, "VRM Diagnostics", DEFAULT_SCAN_INTERVAL_DIAGNOSTICS
    )

    # Dictionary, um Koordinatoren und Geräte-Infos pro Instanz-ID zu speichern
    device_data = {
        "battery": {},
        "multi": {},
        "pv_inverter": {},
        "tank": {},
        "solar_charger": {}
    }

    # Definiere das System Overview Gerät (Das Parent-Device für alle anderen)
    # Es hat KEIN via_device mehr, da es jetzt das Hauptgerät ist.
    system_overview_device_info = {
        "identifiers": {(DOMAIN, f"{site_id}_system_overview")},
        "name": "System Overview",
        "manufacturer": "Victron Energy",
        "model": "Device List",
    }

    # --- FIX 2: Hauptgerät (jetzt System Overview) explizit registrieren ---
    # Dies verhindert Warnungen über "non existing via_device", da das Hub-Gerät
    # nun existiert, bevor Kind-Geräte (Batterien etc.) darauf verweisen.
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        **system_overview_device_info
    )
    
    # Definiere das Overall Stats Gerät
    overall_device_info = {
        "identifiers": {(DOMAIN, f"{site_id}_overall")},
        "name": "Stats Overall",
        "manufacturer": "Victron VRM API",
        "model": "Overall Statistics",
        "via_device": (DOMAIN, f"{site_id}_system_overview"), # Verweist auf System Overview
    }
    
    # Temporäre Liste aller dynamischen Koordinatoren für den initialen Refresh
    dynamic_coordinators = []

    # --- Initialisiere dynamische Koordinatoren und Geräte-Infos pro Instanz ---
    
    # 1. Batterien (Erweitert um History und Alarms Coordinator)
    for instance_id in battery_instance_ids:
        # Standard Battery Summary
        battery_endpoint = f"widgets/BatterySummary?instance={instance_id}"
        coord_name = f"VRM Battery {instance_id} Summary"
        battery_summary_coord = VrmDataCoordinator(
            hass, site_id, token, battery_endpoint, coord_name, DEFAULT_SCAN_INTERVAL_BATTERY
        )
        dynamic_coordinators.append(battery_summary_coord)

        # History Data (für Charge Cycles)
        history_endpoint = f"widgets/HistoricData?instance={instance_id}"
        history_coord_name = f"VRM Battery {instance_id} History"
        battery_history_coord = VrmDataCoordinator(
            hass, site_id, token, history_endpoint, history_coord_name, DEFAULT_SCAN_INTERVAL_BATTERY
        )
        dynamic_coordinators.append(battery_history_coord)
        
        # Alarms Data
        alarm_endpoint = f"widgets/BatteryMonitorWarningsAndAlarms?instance={instance_id}"
        alarm_coord_name = f"VRM Battery {instance_id} Alarms"
        battery_alarm_coord = VrmDataCoordinator(
            hass, site_id, token, alarm_endpoint, alarm_coord_name, DEFAULT_SCAN_INTERVAL_BATTERY
        )
        dynamic_coordinators.append(battery_alarm_coord)

        device_data["battery"][instance_id] = {
            'coordinator': battery_summary_coord,
            'history_coordinator': battery_history_coord, 
            'alarm_coordinator': battery_alarm_coord,
            'device_info': {
                "identifiers": {(DOMAIN, f"{site_id}_battery_{instance_id}")},
                "name": f"Battery {instance_id}",
                "manufacturer": "Victron VRM API",
                "model": f"instance_id {instance_id}",
                "via_device": (DOMAIN, f"{site_id}_system_overview"), # Verweist auf System Overview
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
                "via_device": (DOMAIN, f"{site_id}_system_overview"), # Verweist auf System Overview
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
                "via_device": (DOMAIN, f"{site_id}_system_overview"), # Verweist auf System Overview
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
                "via_device": (DOMAIN, f"{site_id}_system_overview"), # Verweist auf System Overview
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
                "via_device": (DOMAIN, f"{site_id}_system_overview"), # Verweist auf System Overview
            }
        }
    
    # Initialen Refresh ausführen (inklusive system_overview_coord und diagnostics_coord)
    all_coordinators = [overall_stats_coord, stats_coord, system_overview_coord, diagnostics_coord] + dynamic_coordinators
    for coordinator in all_coordinators:
        try:
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.warning("Initialer Refresh des %s Koordinators fehlgeschlagen: %s", coordinator.name, err)


    entities: list[SensorEntity] = []


    # --- 1. Battery Summary Sensoren ---
    # FIX 1: consumed state class von TOTAL_INCREASING auf MEASUREMENT geändert (Wert kann negativ sein)
    battery_sensors_config = {
        "soc": ("51", "State of charge", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, "%", "mdi:battery-50"),
        "voltage": ("47", "Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:current-dc"),
        "current": ("49", "Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-dc"),
        "consumed": ("50", "Consumed Amphours", None, SensorStateClass.MEASUREMENT, "Ah", "mdi:battery-alert-variant-outline"),
        "ttg": ("52", "Time to go", None, SensorStateClass.MEASUREMENT, "h", "mdi:timer-sand"),
        "temp": ("115", "Battery Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, "°C", "mdi:thermometer"),
        "min_cell_voltage": ("173", "Minimum Cell Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:battery-low"),
        "max_cell_voltage": ("174", "Maximum Cell Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:battery-high"),
        "charge_cycles": ("58", "Charge Cycles", None, SensorStateClass.TOTAL_INCREASING, None, "mdi:battery-sync"),
    }
    
    power_sensor_key = "power"
    power_sensor_name = "Battery Power"

    for instance_id, data in device_data["battery"].items():
        summary_coord = data['coordinator']
        history_coord = data['history_coordinator']
        alarm_coord = data['alarm_coordinator']
        dev_info = data['device_info']
        
        # Standard Summary Sensoren
        for key, (data_id, name, device_class, state_class, unit, icon) in battery_sensors_config.items():
            
            # WICHTIG: Auswahl des richtigen Koordinators
            if key == "charge_cycles":
                active_coord = history_coord
            else:
                active_coord = summary_coord

            # Prüfen ob Daten im gewählten Koordinator vorhanden sind
            if active_coord.data and active_coord.data.get("data"):
                actual_data = active_coord.data.get("data", {})
                
                # Prüfen ob die spezifische ID (z.B. 58) in den Daten ist
                if data_id in actual_data:
                    precision = None
                    if unit == "V":
                        precision = 2
                    if key in ["min_cell_voltage", "max_cell_voltage"]:
                        precision = 3

                    entities.append(
                        VrmBatterySummarySensor(
                            active_coord, site_id, 
                            f"{key}_{instance_id}", 
                            data_id, 
                            name, # Friendly Name ohne ID 
                            device_class, state_class, unit, icon, dev_info, precision
                        )
                    )
        
        # Power Sensor nutzt immer Summary Coord
        if summary_coord.data:
            entities.append(
                VrmBatteryPowerSensor(
                    summary_coord, site_id, 
                    f"{power_sensor_key}_{instance_id}", 
                    power_sensor_name, 
                    dev_info
                )
            )

            # Cell Voltage Diff Sensor (requires 173 and 174)
            actual_data = summary_coord.data.get("data", {})
            if "173" in actual_data and "174" in actual_data:
                 entities.append(
                    VrmBatteryCellVoltageDiffSensor(
                        summary_coord, site_id,
                        f"cell_voltage_diff_{instance_id}",
                        "Cell Voltage Difference",
                        dev_info
                    )
                )
            
        # --- 1.1 Battery Alarm & Warning Sensors ---
        battery_alarms_config = {
            "119": ("Low voltage alarm", None, None, None, "mdi:battery-alert"),
            "120": ("High voltage alarm", None, None, None, "mdi:battery-alert"),
            "121": ("Low starter-voltage alarm", None, None, None, "mdi:car-battery"),
            "122": ("High starter-voltage alarm", None, None, None, "mdi:car-battery"),
            "123": ("Low state-of-charge alarm", None, None, None, "mdi:battery-low"),
            "124": ("Low battery temperature alarm", None, None, None, "mdi:thermometer-alert"),
            "125": ("High battery temperature alarm", None, None, None, "mdi:thermometer-alert"),
            "126": ("Mid-voltage alarm", None, None, None, "mdi:battery-alert"),
            "155": ("Low fused-voltage alarm", None, None, None, "mdi:fuse-alert"),
            "156": ("High fused-voltage alarm", None, None, None, "mdi:fuse-alert"),
            "157": ("Fuse blown alarm", None, None, None, "mdi:fuse-off"),
            "158": ("High internal-temperature alarm", None, None, None, "mdi:thermometer-alert"),
            "286": ("Cell Imbalance alarm", None, None, None, "mdi:battery-alert-variant"),
            "287": ("High charge current alarm", None, None, None, "mdi:current-dc"),
            "288": ("High discharge current alarm", None, None, None, "mdi:current-dc"),
            "289": ("Internal Failure", None, None, None, "mdi:alert-circle"),
            "459": ("High charge temperature alarm", None, None, None, "mdi:thermometer-alert"),
            "460": ("Low charge temperature alarm", None, None, None, "mdi:thermometer-alert"),
            "522": ("Low cell voltage", None, None, None, "mdi:battery-alert"),
            "739": ("Charge blocked", None, None, None, "mdi:battery-charging-off"),
            "740": ("Discharge blocked", None, None, None, "mdi:battery-off"),
        }
        
        if alarm_coord.data and alarm_coord.data.get("data"):
            alarm_data = alarm_coord.data.get("data", {})
            for data_id, (name, device_class, state_class, unit, icon) in battery_alarms_config.items():
                if data_id in alarm_data:
                    entities.append(
                        VrmBatteryAlarmSensor(
                            alarm_coord, site_id,
                            f"alarm_{data_id}_{instance_id}",
                            data_id,
                            name,
                            device_class,
                            state_class,
                            unit,
                            icon,
                            dev_info
                        )
                    )
    
    # --- 1.2. Batteries Total Power Sensor ---
    # Sammle alle Battery Summary Coordinators
    battery_summary_coordinators = []
    for data in device_data["battery"].values():
        battery_summary_coordinators.append(data['coordinator'])
        
    if battery_summary_coordinators:
         entities.append(
            VrmBatteriesTotalPowerSensor(
                battery_summary_coordinators,
                site_id,
                overall_device_info
            )
         )

    # --- 1.3. Solar Charger Total Power Sensor ---
    solar_charger_coordinators = []
    for data in device_data["solar_charger"].values():
        solar_charger_coordinators.append(data['coordinator'])
        
    if solar_charger_coordinators:
        entities.append(
            VrmSolarChargersTotalPowerSensor(
                solar_charger_coordinators,
                site_id,
                overall_device_info
            )
        )

    # --- 1.4. PV Inverter Total Power Sensor ---
    pv_inverter_coordinators = []
    for data in device_data["pv_inverter"].values():
        pv_inverter_coordinators.append(data['coordinator'])

    if pv_inverter_coordinators:
        entities.append(
            VrmPvInvertersTotalPowerSensor(
                pv_inverter_coordinators,
                site_id,
                overall_device_info
            )
        )
        
    # --- 1.5. DC Loads Sensor ---
    multi_coordinators = []
    for data in device_data["multi"].values():
        multi_coordinators.append(data['coordinator'])

    if (solar_charger_coordinators or pv_inverter_coordinators) and battery_summary_coordinators:
        entities.append(
            VrmDcLoadsSensor(
                solar_charger_coordinators,
                pv_inverter_coordinators,
                battery_summary_coordinators,
                multi_coordinators,
                site_id,
                overall_device_info
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
                        stats_coord, site_id, f"stats_{json_key}_{instance_id}", data_path, name,
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
        # SOC entfernt (ID 51), da System SOC genutzt wird
    }
    
    multi_dc_power_key = "dc_power"
    multi_dc_power_name = "DC Bus Power"

    for instance_id, data in device_data["multi"].items():
        coord = data['coordinator']
        dev_info = data['device_info']
        if coord.data:
            for key, (data_id, name, device_class, state_class, unit, icon) in multi_status_sensors_config.items():
                precision = 2 if unit == "V" else None
                entities.append(
                    VrmMultiStatusSensor(
                        coord, site_id, f"{key}_{instance_id}", data_id, name, 
                        device_class, state_class, unit, icon, dev_info, precision
                    )
                )
            entities.append(
                VrmMultiPlusDCPowerSensor(
                    coord, site_id, f"{multi_dc_power_key}_{instance_id}", multi_dc_power_name, dev_info
                )
            )

    # --- 3.1 MultiPlus System SOC (from Diagnostics) ---
    # Wir fügen den System SOC (ID 144) aus den Diagnostics dem ERSTEN konfigurierten MultiPlus hinzu.
    # WICHTIG: Filterung auf Instance 0 (System)
    if diagnostics_coord.data and multi_instance_ids:
        # Wir nehmen einfach den ersten MultiPlus als Zielgerät für den SOC
        target_multi_instance = multi_instance_ids[0]
        target_multi_info = device_data["multi"][target_multi_instance]['device_info']
        
        entities.append(
            VrmDiagnosticsSensor(
                diagnostics_coord,
                site_id,
                f"multi_system_soc_{target_multi_instance}",
                144, # idDataAttribute für Battery SOC
                "System State of Charge",
                SensorDeviceClass.BATTERY,
                SensorStateClass.MEASUREMENT,
                "%",
                "mdi:battery-50",
                target_multi_info,
                precision=1,
                instance_id=0 # Explizit Systeminstanz
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
                        stats_coord, site_id, f"stats_{json_key}_{instance_id}", data_path, name,
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
                        stats_coord, site_id, f"stats_{json_key}_{instance_id}", data_path, name,
                        device_class, SensorStateClass.TOTAL_INCREASING, "kWh", icon, dev_info 
                    )
                )
            entities.append(
                VrmPvTotalTodaySensor(
                    stats_coord, site_id, f"pv_total_today_{instance_id}", "PV Total Today", dev_info
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
                    precision = 2 if unit == "V" else None
                    entities.append(
                        VrmPvInverterSensor(
                            coord, site_id, f"{key}_{instance_id}", data_id, name, 
                            device_class, state_class, unit, icon, dev_info, precision
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
                            coord, site_id, f"{key}_{instance_id}", data_id, name, 
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
                    precision = 2 if unit == "V" else None
                    entities.append(
                        VrmSolarChargerSensor(
                            coord, site_id, f"{key}_{instance_id}", data_id, name, 
                            device_class, state_class, unit, icon, dev_info, precision
                        )
                    )

    # --- 4. Overall Stats Sensoren ---
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

    # --- 5. System Overview Sensoren (Gruppierung unter einem Gerät) ---
    if system_overview_coord.data and "devices" in system_overview_coord.data:
        devices_list = system_overview_coord.data.get("devices", [])
        
        # Konfiguration der Felder, die wir als Sensoren haben wollen
        overview_fields = {
            "firmwareVersion": ("Firmware", None, None, None, "mdi:chip"),
            "lastConnection": ("Last Connection", SensorDeviceClass.TIMESTAMP, None, None, "mdi:clock-check"),
            "productName": ("Product Name", None, None, None, "mdi:information"),
            "remoteOnLan": ("Remote IP", None, None, None, "mdi:ip-network"),
            "connectionInformation": ("Connection Info", None, None, None, "mdi:connection"),
            "autoUpdate": ("Auto Update", None, None, None, "mdi:update"),
            "batteryFamily": ("Battery Family", None, None, None, "mdi:battery-heart-variant"),
            "batteryManufacturer": ("Battery Manufacturer", None, None, None, "mdi:factory"),
            "machineSerialNumber": ("Serial Number", None, None, None, "mdi:barcode"),
            "instance": ("Instance ID", None, None, None, "mdi:identifier"),
        }

        for device in devices_list:
            dev_instance = device.get("instance")
            dev_identifier = device.get("identifier")
            dev_name = device.get("name", "Unknown Device")
            dev_custom_name = device.get("customName")
            
            final_name_prefix = dev_custom_name if dev_custom_name else dev_name
            
            unique_ref = None
            if dev_instance is not None:
                current_type_id = device.get('idDeviceType')
                unique_ref = f"type{current_type_id}_inst{dev_instance}"
            elif dev_identifier:
                unique_ref = f"id_{dev_identifier}"
            else:
                unique_ref = f"type_{device.get('idDeviceType')}_{slugify(dev_name)}"
            
            for field_key, (suffix, dev_class, state_class, unit, icon) in overview_fields.items():
                if field_key in device:
                    entities.append(
                        VrmSystemOverviewSensor(
                            system_overview_coord,
                            site_id,
                            f"overview_{unique_ref}_{field_key}", # Unique ID Key
                            unique_ref, 
                            field_key, 
                            f"{final_name_prefix} {suffix}", 
                            dev_class,
                            state_class,
                            unit,
                            icon,
                            system_overview_device_info 
                        )
                    )
    
    # --- 6. ESS Sensoren (aus Diagnostics in System Overview) ---
    # Diese Werte kommen aus dem Diagnostics Endpoint, gehören aber logisch zur Systemübersicht
    # WICHTIG: Filterung auf Instance 0
    if diagnostics_coord.data:
        ess_sensors_config = {
            332: ("ESS Battery Life State", None, None, None, "mdi:battery-heart-outline"),
            333: ("ESS Battery Life SOC Limit", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery-negative"),
            334: ("ESS Minimum SOC", None, SensorStateClass.MEASUREMENT, "%", "mdi:battery-lock"),
            469: ("ESS Scheduled Charging", None, None, None, "mdi:calendar-clock"),
        }

        for data_id, (name, dev_class, state_class, unit, icon) in ess_sensors_config.items():
            entities.append(
                VrmDiagnosticsSensor(
                    diagnostics_coord,
                    site_id,
                    f"ess_status_{data_id}",
                    data_id,
                    name,
                    dev_class,
                    state_class,
                    unit,
                    icon,
                    system_overview_device_info,
                    instance_id=0 # Explizit Systeminstanz
                )
            )

    # --- 7. Grid Meter Sensoren (aus Diagnostics, Manuell Konfiguriert) ---
    if diagnostics_coord.data and grid_instance_ids:
        # Wir iterieren über die konfigurierten Instanz-IDs
        for grid_instance_id in grid_instance_ids:
            
            grid_device_info = {
                "identifiers": {(DOMAIN, f"{site_id}_grid_meter_{grid_instance_id}")},
                "name": f"Grid Meter {grid_instance_id}",
                "manufacturer": "Victron Energy",
                "model": "Grid Meter",
                "via_device": (DOMAIN, f"{site_id}_system_overview"), # Verweist auf System Overview
            }
            
            # Grid Sensoren Konfiguration (ID -> Config)
            grid_sensors_config = {
                834: ("Grid L1 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
                835: ("Grid L1 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
                379: ("Grid L1 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:transmission-tower"),
                
                837: ("Grid L2 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
                838: ("Grid L2 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
                380: ("Grid L2 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:transmission-tower"),
                
                840: ("Grid L3 Voltage", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "V", "mdi:flash-triangle"),
                841: ("Grid L3 Current", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "A", "mdi:current-ac"),
                381: ("Grid L3 Power",   SensorDeviceClass.POWER,   SensorStateClass.MEASUREMENT, "W", "mdi:transmission-tower"),
            }
            
            for data_id, (name, dev_class, state_class, unit, icon) in grid_sensors_config.items():
                precision = 1 if unit == "V" else None
                entities.append(
                    VrmDiagnosticsSensor(
                        diagnostics_coord,
                        site_id,
                        f"grid_{grid_instance_id}_{data_id}",
                        data_id,
                        name,
                        dev_class,
                        state_class,
                        unit,
                        icon,
                        grid_device_info,
                        precision,
                        instance_id=grid_instance_id # Explizit filtern
                    )
                )
            
            # Total Grid Power Sensor hinzufügen (Klasse filtert bereits intern auf Instanz ID)
            entities.append(
                VrmGridTotalPowerSensor(
                    diagnostics_coord,
                    site_id,
                    grid_instance_id,
                    grid_device_info
                )
            )

    async_add_entities(entities, True)


# --- 5. Basisklasse für Sensoren -----------
class VrmBaseSensor(CoordinatorEntity, SensorEntity):
    """Basisklasse für alle VRM Sensoren."""
    def __init__(self, coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision=None):
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
        self._attr_suggested_display_precision = precision

# --- 6. Battery Summary Sensor ---------------------------------------------------
class VrmBatterySummarySensor(VrmBaseSensor):
    """Represents a single value from the VRM Battery Summary data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
        self._data_id = data_id
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        attr = data.get(self._data_id, {})
        return attr.get("valueFloat")

# --- 6.1 Battery Alarm Sensor --------------------------------------------
class VrmBatteryAlarmSensor(VrmBaseSensor):
    """Represents a Battery Alarm Status (Text from Enum)."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
        self._data_id = data_id

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        
        records_data = self.coordinator.data.get("data", {})
        specific_data = records_data.get(self._data_id, {})
        
        raw_value = None
        try:
            first_index = specific_data.get("0", {})
            raw_value = first_index.get("0")
        except (AttributeError, KeyError):
            return None

        if raw_value is None:
            return None

        enums = self.coordinator.data.get("enums", {})
        specific_enums = enums.get(self._data_id, {})
        
        human_readable = specific_enums.get(str(raw_value))
        if human_readable:
            return human_readable
        
        return raw_value

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

# --- 6.5.5. Calculated Battery Cell Voltage Diff Sensor ------------------------
class VrmBatteryCellVoltageDiffSensor(VrmBaseSensor):
    """Calculates difference between Max (174) and Min (173) Cell Voltage."""
    
    MIN_CELL_VOLTAGE_ID = "173"
    MAX_CELL_VOLTAGE_ID = "174"

    def __init__(self, coordinator, site_id, key, name, device_info):
        super().__init__(
            coordinator, site_id, key, name, SensorDeviceClass.VOLTAGE,
            SensorStateClass.MEASUREMENT, "V", "mdi:battery-alert-variant-outline", device_info, precision=3
        )

    @property
    def native_value(self) -> float:
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        min_v = data.get(self.MIN_CELL_VOLTAGE_ID, {}).get("valueFloat")
        max_v = data.get(self.MAX_CELL_VOLTAGE_ID, {}).get("valueFloat")

        if min_v is None or max_v is None:
            return None
        try:
            return round(max_v - min_v, 3) 
        except (TypeError, ValueError):
            return None

# --- 6.5.6. Calculated Batteries Total Power Sensor ----------------------------
class VrmBatteriesTotalPowerSensor(SensorEntity):
    """Calculates Total Power of all Batteries."""
    
    VOLTAGE_DATA_ID = "47"
    CURRENT_DATA_ID = "49"

    def __init__(self, coordinators, site_id, device_info):
        self.coordinators = coordinators
        self._attr_unique_id = f"vrm_v2_{site_id}_batteries_total_power"
        self._attr_name = "Batteries Power Total"
        self.entity_id = f"sensor.vrm_batteries_power_total"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"
        self._attr_icon = "mdi:battery-charging-100"
        self._attr_device_info = device_info
        
    async def async_added_to_hass(self):
        """Register callbacks."""
        await super().async_added_to_hass()
        for coordinator in self.coordinators:
            self.async_on_remove(
                coordinator.async_add_listener(self.async_write_ha_state)
            )

    @property
    def native_value(self):
        total_power = 0.0
        # Check if we have any data at all
        has_data = False
        
        for coordinator in self.coordinators:
            if not coordinator.data:
                continue
            
            data = coordinator.data.get("data", {})
            voltage = data.get(self.VOLTAGE_DATA_ID, {}).get("valueFloat")
            current = data.get(self.CURRENT_DATA_ID, {}).get("valueFloat")
            
            if voltage is not None and current is not None:
                has_data = True
                total_power += (voltage * current)
                
        if not has_data:
            return 0.0
            
        return round(total_power, 2)

# --- 6.5.7. Calculated Solar Chargers Total Power Sensor -----------------------
class VrmSolarChargersTotalPowerSensor(SensorEntity):
    """Calculates Total Power of all Solar Chargers."""
    
    POWER_DATA_ID = "107"

    def __init__(self, coordinators, site_id, device_info):
        self.coordinators = coordinators
        self._attr_unique_id = f"vrm_v2_{site_id}_solar_chargers_total_power"
        self._attr_name = "Solar Chargers Power Total"
        self.entity_id = f"sensor.vrm_solar_chargers_power_total"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"
        self._attr_icon = "mdi:solar-power"
        self._attr_device_info = device_info
        
    async def async_added_to_hass(self):
        """Register callbacks."""
        await super().async_added_to_hass()
        for coordinator in self.coordinators:
            self.async_on_remove(
                coordinator.async_add_listener(self.async_write_ha_state)
            )

    @property
    def native_value(self):
        total_power = 0.0
        has_data = False
        
        for coordinator in self.coordinators:
            if not coordinator.data:
                continue
            
            data = coordinator.data.get("data", {})
            # ID 107 is Battery Watts
            power = data.get(self.POWER_DATA_ID, {}).get("valueFloat")
            
            if power is not None:
                has_data = True
                total_power += power
                
        if not has_data:
            return 0.0
            
        return round(total_power, 2)

# --- 6.5.8. Calculated PV Inverters Total Power Sensor -------------------------
class VrmPvInvertersTotalPowerSensor(SensorEntity):
    """Calculates Total Power of all PV Inverters."""
    
    L1_POWER_ID = "205"
    L2_POWER_ID = "209"
    L3_POWER_ID = "213"

    def __init__(self, coordinators, site_id, device_info):
        self.coordinators = coordinators
        self._attr_unique_id = f"vrm_v2_{site_id}_pv_inverters_total_power"
        self._attr_name = "PV Inverters Power Total"
        self.entity_id = f"sensor.vrm_pv_inverters_power_total"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"
        self._attr_icon = "mdi:solar-power-variant"
        self._attr_device_info = device_info
        
    async def async_added_to_hass(self):
        """Register callbacks."""
        await super().async_added_to_hass()
        for coordinator in self.coordinators:
            self.async_on_remove(
                coordinator.async_add_listener(self.async_write_ha_state)
            )

    @property
    def native_value(self):
        total_power = 0.0
        has_data = False
        
        for coordinator in self.coordinators:
            if not coordinator.data:
                continue
            
            data = coordinator.data.get("data", {})
            
            l1 = data.get(self.L1_POWER_ID, {}).get("valueFloat")
            l2 = data.get(self.L2_POWER_ID, {}).get("valueFloat")
            l3 = data.get(self.L3_POWER_ID, {}).get("valueFloat")
            
            current_inv_power = 0.0
            found_val = False
            
            if l1 is not None:
                current_inv_power += l1
                found_val = True
            if l2 is not None:
                current_inv_power += l2
                found_val = True
            if l3 is not None:
                current_inv_power += l3
                found_val = True
                
            if found_val:
                has_data = True
                total_power += current_inv_power

        if not has_data:
            return 0.0
            
        return round(total_power, 2)

# --- 6.5.9. Calculated DC Loads Sensor -----------------------------------------
class VrmDcLoadsSensor(SensorEntity):
    """Calculates DC Loads."""
    
    # Solar Charger Power ID
    SC_POWER_ID = "107"
    
    # PV Inverter Power IDs
    PV_L1_ID = "205"
    PV_L2_ID = "209"
    PV_L3_ID = "213"
    
    # Battery Power IDs
    BATT_VOLTAGE_ID = "47"
    BATT_CURRENT_ID = "49"
    
    # MultiPlus DC Power IDs
    MULTI_DC_VOLTAGE_ID = "32"
    MULTI_DC_CURRENT_ID = "33"

    def __init__(self, sc_coordinators, pv_coordinators, batt_coordinators, multi_coordinators, site_id, device_info):
        self.sc_coordinators = sc_coordinators
        self.pv_coordinators = pv_coordinators
        self.batt_coordinators = batt_coordinators
        self.multi_coordinators = multi_coordinators
        
        self._attr_unique_id = f"vrm_v2_{site_id}_dc_loads"
        self._attr_name = "DC Loads"
        self.entity_id = f"sensor.vrm_dc_loads"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"
        self._attr_icon = "mdi:flash-outline"
        self._attr_device_info = device_info
        
    async def async_added_to_hass(self):
        """Register callbacks."""
        await super().async_added_to_hass()
        all_coords = (self.sc_coordinators + self.pv_coordinators + 
                      self.batt_coordinators + self.multi_coordinators)
        for coordinator in all_coords:
            self.async_on_remove(
                coordinator.async_add_listener(self.async_write_ha_state)
            )

    @property
    def native_value(self):
        # Formula: (Total Solar + Total PV) - Total Battery Power - Total MultiPlus DC Power
        
        total_solar = 0.0
        for c in self.sc_coordinators:
            if c.data:
                val = c.data.get("data", {}).get(self.SC_POWER_ID, {}).get("valueFloat")
                if val is not None:
                    total_solar += val
                    
        total_pv = 0.0
        for c in self.pv_coordinators:
            if c.data:
                d = c.data.get("data", {})
                for pid in [self.PV_L1_ID, self.PV_L2_ID, self.PV_L3_ID]:
                    val = d.get(pid, {}).get("valueFloat")
                    if val is not None:
                        total_pv += val

        total_batt = 0.0
        for c in self.batt_coordinators:
            if c.data:
                d = c.data.get("data", {})
                v = d.get(self.BATT_VOLTAGE_ID, {}).get("valueFloat")
                i = d.get(self.BATT_CURRENT_ID, {}).get("valueFloat")
                if v is not None and i is not None:
                    total_batt += (v * i)

        total_multi = 0.0
        for c in self.multi_coordinators:
            if c.data:
                d = c.data.get("data", {})
                v = d.get(self.MULTI_DC_VOLTAGE_ID, {}).get("valueFloat")
                i = d.get(self.MULTI_DC_CURRENT_ID, {}).get("valueFloat")
                if v is not None and i is not None:
                    total_multi += (v * i)
                    
        return round((total_solar + total_pv) - total_batt - total_multi, 2)

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
    def __init__(self, coordinator, site_id, key, data_path, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
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
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
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

# --- 9. PV Inverter Sensor --------------------
class VrmPvInverterSensor(VrmBaseSensor):
    """Represents a single value from the VRM PV Inverter Status data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
        self._data_id = data_id
        
    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        data = self.coordinator.data.get("data", {})
        attr = data.get(self._data_id, {})
        if not attr:
            return None
            
        value_float = attr.get("valueFloat")
        if value_float is not None:
            return value_float
            
        value_enum = attr.get("nameEnum")
        if value_enum is not None:
            return value_enum
        return attr.get("value")

# --- 10. Tank Sensor ----------------------------------------------------------
class VrmTankSensor(VrmBaseSensor):
    """Represents a single value from the VRM Tank Status data."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
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
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
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

# --- 12. System Overview Sensor ----------------------------------------
class VrmSystemOverviewSensor(VrmBaseSensor):
    """Represents a generic value from the System Overview data."""
    def __init__(self, coordinator, site_id, key, unique_ref, json_key, name, device_class, state_class, unit, icon, device_info, precision=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
        self._unique_ref = unique_ref
        self._json_key = json_key

    @property
    def native_value(self):
        if not self.coordinator.data or "devices" not in self.coordinator.data:
            return None
            
        devices = self.coordinator.data["devices"]
        
        target_device = None
        for device in devices:
            dev_instance = device.get("instance")
            dev_identifier = device.get("identifier")
            dev_name = device.get("name", "Unknown")
            
            current_ref = None
            if dev_instance is not None:
                current_type_id = device.get('idDeviceType')
                current_ref = f"type{current_type_id}_inst{dev_instance}"
            elif dev_identifier:
                current_ref = f"id_{dev_identifier}"
            else:
                 current_ref = f"type_{device.get('idDeviceType')}_{slugify(dev_name)}"
                 
            if current_ref == self._unique_ref:
                target_device = device
                break
        
        if not target_device:
            return None
            
        value = target_device.get(self._json_key)
        
        if self.device_class == SensorDeviceClass.TIMESTAMP:
            if value is not None and isinstance(value, int):
                return datetime.fromtimestamp(value, tz=timezone.utc)
        
        return value

# --- 13. Diagnostics Sensor ----------------------------------------
class VrmDiagnosticsSensor(VrmBaseSensor):
    """Represents a value from the Diagnostics/installations API."""
    def __init__(self, coordinator, site_id, key, data_id, name, device_class, state_class, unit, icon, device_info, precision=None, instance_id=None):
        super().__init__(coordinator, site_id, key, name, device_class, state_class, unit, icon, device_info, precision)
        self._data_id = int(data_id)
        self._target_instance_id = instance_id

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        
        # Diagnostics Data ist normalerweise eine Liste von Records
        records = self.coordinator.data
        if not isinstance(records, list):
            return None
            
        # Suche den Eintrag mit dem passenden idDataAttribute und optionaler Instance ID
        target_record = None
        for item in records:
            # Wenn Instance ID angegeben wurde, filtern wir danach
            if self._target_instance_id is not None:
                if item.get("instance") != self._target_instance_id:
                    continue
            
            # Prüfen ob ID übereinstimmt
            if item.get("idDataAttribute") == self._data_id:
                target_record = item
                break
        
        if not target_record:
            return None
            
        # Priorität: formattedValue für nicht-numerische Klassen (Status), rawValue für Zahlen
        # Ausnahme: Wenn device_class None ist (also z.B. Text), nehmen wir formattedValue
        
        if self.device_class is None and self.state_class is None:
             # Text-Sensor (z.B. ESS Status)
             return target_record.get("formattedValue")
        
        # Numerischer Sensor
        val = target_record.get("rawValue")
        
        # Manchmal ist rawValue auch ein String im JSON, sicherstellen dass es float ist
        try:
             return float(val)
        except (TypeError, ValueError):
             return val

# --- 14. Grid Total Power Sensor ----------------------------------------
class VrmGridTotalPowerSensor(SensorEntity):
    """Calculates Total Grid Power (L1+L2+L3) from Diagnostics."""
    
    L1_POWER_ID = 379
    L2_POWER_ID = 380
    L3_POWER_ID = 381

    def __init__(self, coordinator, site_id, grid_instance_id, device_info):
        self.coordinator = coordinator
        self._attr_unique_id = f"vrm_v2_{site_id}_grid_total_power_{grid_instance_id}"
        self._attr_name = "Grid Total Power"
        self.entity_id = f"sensor.vrm_grid_total_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"
        self._attr_icon = "mdi:transmission-tower-export"
        self._attr_device_info = device_info
        self._grid_instance_id = grid_instance_id
        
    async def async_added_to_hass(self):
        """Register callbacks."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self):
        if not self.coordinator.data:
            return 0.0
            
        records = self.coordinator.data
        if not isinstance(records, list):
            return 0.0

        l1 = 0.0
        l2 = 0.0
        l3 = 0.0
        has_data = False
        
        # Wir durchsuchen die Liste nach den 3 Power IDs
        for item in records:
            # Filterung nach Instanz ID, um Konflikte mit anderen Grid Metern zu vermeiden
            if item.get("instance") != self._grid_instance_id:
                continue

            attr_id = item.get("idDataAttribute")
            if attr_id in [self.L1_POWER_ID, self.L2_POWER_ID, self.L3_POWER_ID]:
                val = item.get("rawValue")
                try:
                    val_float = float(val)
                    if attr_id == self.L1_POWER_ID: l1 = val_float
                    if attr_id == self.L2_POWER_ID: l2 = val_float
                    if attr_id == self.L3_POWER_ID: l3 = val_float
                    has_data = True
                except (TypeError, ValueError):
                    continue
                    
        if not has_data:
            return 0.0
            
        return round(l1 + l2 + l3, 2)
        