"""Update platform for Freebox Connect."""

from __future__ import annotations

import logging

from homeassistant.components.update import UpdateEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator
from .device import get_freebox_server_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Connect update platform."""
    coordinator: FreeboxConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get system data for device info
    system_data = coordinator.data.get("system", {})
    server_device = get_freebox_server_device(entry.entry_id, system_data)

    entities = [
        FreeboxFirmwareUpdateEntity(coordinator, entry, server_device),
    ]

    async_add_entities(entities)


class FreeboxFirmwareUpdateEntity(CoordinatorEntity, UpdateEntity):
    """Representation of Freebox firmware update entity."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_firmware_update"
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_firmware"
        self._attr_device_info = device_info
        self._attr_title = "Freebox Firmware"

    @property
    def installed_version(self) -> str | None:
        """Return the current installed version."""
        if system := self.coordinator.data.get("system"):
            version = system.get("firmware_version")
            return version if version else "Unknown"
        return "Unknown"

    @property
    def latest_version(self) -> str | None:
        """Return the latest available version."""
        # For now, return the installed version since we don't have access
        # to the update endpoint. This can be improved later.
        return self.installed_version

    @property
    def release_url(self) -> str | None:
        """Return the URL for release notes."""
        # Freebox changelog URL
        return "https://www.free.fr/assistance/7478-freebox-revolution-quelles-sont-les-evolutions-du-firmware-freebox-server.html"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success and "system" in self.coordinator.data
        )
