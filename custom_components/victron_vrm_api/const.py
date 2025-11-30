"""Constants for the VRM Victron Energy integration."""

# Die Domäne (muss mit dem Ordnernamen übereinstimmen)
DOMAIN = "victron_vrm_api"

# Konfigurationsschlüssel (Erwartet nun eine durch Komma getrennte Liste von Instanz-IDs als String)
CONF_SITE_ID = "site_id"
CONF_TOKEN = "token"
CONF_BATTERY_INSTANCE = "battery_instance_ids"      # Instance IDs der Batterien (String: '1, 2')
CONF_MULTI_INSTANCE = "multi_instance_ids"          # Instance IDs des MultiPlus (String: '100')
CONF_PV_INVERTER_INSTANCE = "pv_instance_ids"       # Instance IDs des PV Inverters (String: '200, 201')
CONF_TANK_INSTANCE = "tank_instance_ids"            # Instance IDs des Tanks (String: '300')
CONF_SOLAR_CHARGER_INSTANCE = "solar_charger_ids"   # Instance IDs des Solar Chargers (String: '400, 401')

# Standard-Aktualisierungsintervalle (in Sekunden)
DEFAULT_SCAN_INTERVAL_BATTERY = 20       # 20 Sekunden
DEFAULT_SCAN_INTERVAL_MULTI = 20         # 20 Sekunden 
DEFAULT_SCAN_INTERVAL_PV_INVERTER = 20   # 20 Sekunden
DEFAULT_SCAN_INTERVAL_TANK = 60          # 60 Sekunden 
DEFAULT_SCAN_INTERVAL_SOLAR_CHARGER = 20 # 20 Sekunden 
DEFAULT_SCAN_INTERVAL_OVERALL = 300      # 5 Minuten
