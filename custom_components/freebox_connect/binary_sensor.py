"""Binary sensor platform for Freebox Connect."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Connect binary sensor platform."""
    coordinator: FreeboxConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FreeboxInternetConnectivitySensor(coordinator, entry),
    ]

    async_add_entities(entities)


class FreeboxInternetConnectivitySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of Freebox internet connectivity sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_internet_connectivity"
        self._attr_name = "Freebox Internet"
        self._attr_device_class = "connectivity"
        self._attr_icon = "mdi:web"

    @property
    def is_on(self) -> bool | None:
        """Return true if internet is connected."""
        if connection := self.coordinator.data.get("connection"):
            return connection.get("state") == "up"
        return None
