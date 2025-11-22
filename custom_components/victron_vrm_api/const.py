"""Constants for the VRM Victron Energy integration."""

# Die Domäne (muss mit dem Ordnernamen übereinstimmen)
DOMAIN = "victron_vrm_api"

# Konfigurationsschlüssel
CONF_SITE_ID = "site_id"
CONF_TOKEN = "token"
CONF_BATTERY_INSTANCE = "battery_instance_id"    # Instance ID der Batterie
CONF_MULTI_INSTANCE = "multi_instance_id"        # Instance ID des MultiPlus
CONF_PV_INVERTER_INSTANCE = "pv_instance_id"     # Instance ID des PV Inverters

# Standard-Aktualisierungsintervalle (in Sekunden)
DEFAULT_SCAN_INTERVAL_BATTERY = 20     # 30 Sekunden
DEFAULT_SCAN_INTERVAL_MULTI = 20       # 30 Sekunden 
DEFAULT_SCAN_INTERVAL_PV_INVERTER = 20 # 30 Sekunden
DEFAULT_SCAN_INTERVAL_OVERALL = 300    # 5 Minuten
