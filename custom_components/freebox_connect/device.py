"""Device management for Freebox Connect."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


def get_freebox_server_device(entry_id: str, system_data: dict) -> DeviceInfo:
    """Get device info for Freebox Server."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_server")},
        name="Freebox Server",
        manufacturer="Free",
        model=system_data.get("box_flavor", "Freebox"),
        sw_version=system_data.get("firmware_version"),
        serial_number=system_data.get("serial"),
        configuration_url=f"http://mafreebox.freebox.fr",
    )


def get_freebox_repeater_device(entry_id: str, repeater_data: dict) -> DeviceInfo:
    """Get device info for a Freebox Repeater."""
    # Extract repeater identifier
    repeater_id = repeater_data.get("id", "unknown")
    repeater_name = repeater_data.get("name", f"Répéteur {repeater_id}")

    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_repeater_{repeater_id}")},
        name=f"Freebox {repeater_name}",
        manufacturer="Free",
        model=repeater_data.get("model", "Freebox Repeater"),
        sw_version=repeater_data.get("firmware_version"),
        serial_number=repeater_data.get("serial"),
        via_device=(DOMAIN, f"{entry_id}_server"),  # Link to server
    )


class FreeboxDeviceEntity(Entity):
    """Base class for Freebox entities with device association."""

    def __init__(self, device_info: DeviceInfo) -> None:
        """Initialize the entity."""
        self._attr_device_info = device_info

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return self._attr_device_info
