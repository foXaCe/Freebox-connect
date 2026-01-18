"""Binary sensor platform for Freebox Connect."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator
from .device import get_freebox_server_device


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Connect binary sensor platform."""
    coordinator: FreeboxConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get system data for device info
    system_data = coordinator.data.get("system", {})
    server_device = get_freebox_server_device(entry.entry_id, system_data)

    entities = [
        FreeboxInternetConnectivitySensor(coordinator, entry, server_device),
    ]

    async_add_entities(entities)


class FreeboxInternetConnectivitySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of Freebox internet connectivity sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_internet_connectivity"
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_internet"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_icon = "mdi:web"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if internet is connected."""
        if connection := self.coordinator.data.get("connection"):
            return connection.get("state") == "up"
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and "connection" in self.coordinator.data
        )
