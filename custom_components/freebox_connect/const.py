"""Constants for the Freebox Connect integration."""

from datetime import timedelta

DOMAIN = "freebox_connect"

# API endpoints
API_VERSION_ENDPOINT = "/api_version"
API_LOGIN_SESSION = "/api/v15/login/session/"
API_LOGIN_PERMS = "/api/v11/login/perms/"
API_SYSTEM = "/api/v11/system/"
API_SYSTEM_WOP = "/api/v11/system/wop"

# WiFi endpoints
API_WIFI_CONFIG = "/api/v11/wifi/config/"
API_WIFI_CONFIG_RESET = "/api/v11/wifi/config/reset/"
API_WIFI_STATE = "/api/v11/wifi/state/"
API_WIFI_AP = "/api/v13/wifi/ap/"
API_WIFI_BSS = "/api/v14/wifi/bss/"
API_WIFI_DEFAULT = "/api/v14/wifi/default"
API_WIFI_DIAG = "/api/v14/wifi/diag"
API_WIFI_CUSTOM_KEY = "/api/v11/wifi/custom_key/"

# System action endpoints
API_SYSTEM_REBOOT = "/api/v11/system/reboot/"

# LCD action endpoints
API_LCD_HIDE_WIFI_KEY = "/api/v11/lcd/config/"
API_LCD_ROTATE = "/api/v11/lcd/config/"

# Network endpoints
API_CONNECTION = "/api/v11/connection/"
API_LAN_BROWSER_INTERFACES = "/api/v11/lan/browser/interfaces/"
API_LAN_BROWSER_PUB = "/api/v11/lan/browser/pub/"
API_LAN_BROWSER_TYPES = "/api/v11/lan/browser/types/"

# Repeater
API_REPEATER = "/api/v11/repeater/"

# Storage & Phone
API_STORAGE = "/api/v11/storage/disk/"
API_CALL_LOG = "/api/v11/call/log/"
API_CALL_ACCOUNT = "/api/v11/call/account"
API_CALL_VOICEMAIL = "/api/v11/call/voicemail"

# System features
API_LCD = "/api/v11/lcd/config/"
API_STANDBY = "/api/v11/standby/status/"
API_PLAYER = "/api/v11/player"
API_CAMERA = "/api/v11/camera/"
API_WDO = "/api/v11/wdo/reqs/wmr"

# Notifications
API_NOTIF_TARGETS = "/api/v11/notif/targets/"

# Update interval
UPDATE_INTERVAL = timedelta(seconds=30)

# Configuration
CONF_APP_ID = "app_id"
CONF_APP_TOKEN = "app_token"
CONF_TRACK_ID = "track_id"
CONF_TRACK_NETWORK_DEVICES = "track_network_devices"
CONF_USE_HTTPS = "use_https"

# Default app info
DEFAULT_APP_ID = "home_assistant_freebox_connect"
DEFAULT_APP_NAME = "Home Assistant Freebox Connect"
DEFAULT_APP_VERSION = "0.1.0"
DEFAULT_DEVICE_NAME = "Home Assistant"
