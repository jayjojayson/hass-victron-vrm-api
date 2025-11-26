"""Constants for the VRM Victron Energy integration."""

# Die Domäne (muss mit dem Ordnernamen übereinstimmen)
DOMAIN = "victron_vrm_api"

# Konfigurationsschlüssel
CONF_SITE_ID = "site_id"
CONF_TOKEN = "token"
CONF_BATTERY_INSTANCE = "battery_instance_id"      # Instance ID der Batterie
CONF_MULTI_INSTANCE = "multi_instance_id"          # Instance ID des MultiPlus
CONF_PV_INVERTER_INSTANCE = "pv_instance_id"       # Instance ID des PV Inverters
CONF_TANK_INSTANCE = "tank_instance_id"            # Instance ID des Tanks
CONF_SOLAR_CHARGER_INSTANCE = "solar_charger_id"   # Instance ID des Solar Chargers

# Standard-Aktualisierungsintervalle (in Sekunden)
DEFAULT_SCAN_INTERVAL_BATTERY = 20       # 20 Sekunden
DEFAULT_SCAN_INTERVAL_MULTI = 20         # 20 Sekunden 
DEFAULT_SCAN_INTERVAL_PV_INVERTER = 20   # 20 Sekunden
DEFAULT_SCAN_INTERVAL_TANK = 60          # 60 Sekunden 
DEFAULT_SCAN_INTERVAL_SOLAR_CHARGER = 20 # 20 Sekunden 
DEFAULT_SCAN_INTERVAL_OVERALL = 300      # 5 Minuten
