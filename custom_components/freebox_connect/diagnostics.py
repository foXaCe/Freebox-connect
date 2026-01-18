"""Diagnostics support for Freebox Connect."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_APP_TOKEN, DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator

TO_REDACT = {
    CONF_APP_TOKEN,
    CONF_HOST,
    "serial",
    "mac",
    "main_mac",
    "ipv4",
    "ipv6",
    "bssid",
    "app_token",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: FreeboxConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    diagnostics_data = {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }

    return diagnostics_data
