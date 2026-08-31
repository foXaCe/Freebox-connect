"""Freebox Connect integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_APP_TOKEN, CONF_USE_HTTPS, DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator
from .device import get_freebox_server_device

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.BUTTON,
    Platform.SWITCH,
    Platform.UPDATE,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Freebox Connect from a config entry."""
    coordinator = FreeboxConnectDataUpdateCoordinator(
        hass,
        session=async_get_clientsession(hass),
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, 46535),
        app_token=entry.data.get(CONF_APP_TOKEN),
        use_https=entry.data.get(CONF_USE_HTTPS, True),
    )

    await coordinator.async_config_entry_first_refresh()

    # Register the Freebox Server device upfront so child devices (repeaters)
    # can reference it through `via_device_id`.
    server_device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        **get_freebox_server_device(entry.entry_id, coordinator.data.get("system", {})),
    )
    coordinator.server_device_id = server_device.id

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
