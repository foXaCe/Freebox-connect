"""Device management for Freebox Connect."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

# `via_device` (identifier tuple) is deprecated in favour of `via_device_id`
# (device registry id). Detect which one the running HA core supports.
_SUPPORTS_VIA_DEVICE_ID = "via_device_id" in DeviceInfo.__annotations__


def get_freebox_server_device(entry_id: str, system_data: dict) -> DeviceInfo:
    """Get device info for Freebox Server."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_server")},
        name="Freebox Server",
        manufacturer="Free",
        model=system_data.get("box_flavor", "Freebox"),
        sw_version=system_data.get("firmware_version"),
        serial_number=system_data.get("serial"),
        configuration_url="http://mafreebox.freebox.fr",
    )


def get_freebox_repeater_device(
    entry_id: str, repeater_data: dict, server_device_id: str | None = None
) -> DeviceInfo:
    """Get device info for a Freebox Repeater."""
    # Extract repeater identifier
    repeater_id = repeater_data.get("id", "unknown")
    repeater_name = repeater_data.get("name", f"Repeater {repeater_id}")

    device_info = DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_repeater_{repeater_id}")},
        name=f"Freebox {repeater_name}",
        manufacturer="Free",
        model=repeater_data.get("model", "Freebox Repeater"),
        sw_version=repeater_data.get("firmware_version"),
        serial_number=repeater_data.get("serial"),
    )

    # Link the repeater to the Freebox Server
    if _SUPPORTS_VIA_DEVICE_ID and server_device_id:
        device_info["via_device_id"] = server_device_id
    elif not _SUPPORTS_VIA_DEVICE_ID:
        device_info["via_device"] = (DOMAIN, f"{entry_id}_server")

    return device_info
