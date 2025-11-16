"""Constants for the VRM Victron Energy integration."""

# Die Domäne (muss mit dem Ordnernamen übereinstimmen)
DOMAIN = "victron_vrm_api"

# Konfigurationsschlüssel
CONF_SITE_ID = "site_id"
CONF_TOKEN = "token"
CONF_BATTERY_INSTANCE = "battery_instance_id" # Instance ID der Batterie
CONF_MULTI_INSTANCE = "multi_instance_id"     # Instance ID des MultiPlus (Status)

# Standard-Aktualisierungsintervalle (in Sekunden)
DEFAULT_SCAN_INTERVAL_BATTERY = 10     # 10 Sekunden
DEFAULT_SCAN_INTERVAL_MULTI = 10       # 10 Sekunden 
DEFAULT_SCAN_INTERVAL_OVERALL = 300    # 5 Minuten

