"""Device tracker platform for Freebox Connect."""
from __future__ import annotations

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TRACK_NETWORK_DEVICES, DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Connect device tracker platform."""
    # Device tracking is disabled - use official Freebox integration instead
    return


class FreeboxDeviceTracker(CoordinatorEntity, ScannerEntity):
    """Representation of a Freebox network device."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_data: dict,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._mac = device_data.get("l2ident", {}).get("id")
        self._attr_unique_id = f"{entry.entry_id}_device_{self._mac}"
        self._attr_name = device_data.get("primary_name") or self._mac

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.ROUTER

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected."""
        if lan_devices := self.coordinator.data.get("lan_devices"):
            if isinstance(lan_devices, list):
                for device in lan_devices:
                    if device.get("l2ident", {}).get("id") == self._mac:
                        return device.get("active", False)
        return False

    @property
    def ip_address(self) -> str | None:
        """Return the primary IP address (IPv4 preferred)."""
        if lan_devices := self.coordinator.data.get("lan_devices"):
            if isinstance(lan_devices, list):
                for device in lan_devices:
                    if device.get("l2ident", {}).get("id") == self._mac:
                        # Get IPv4 address first
                        if l3connectivities := device.get("l3connectivities"):
                            for conn in l3connectivities:
                                if conn.get("af") == "ipv4":
                                    return conn.get("addr")
                            # Fallback to IPv6 if no IPv4
                            for conn in l3connectivities:
                                if conn.get("af") == "ipv6":
                                    return conn.get("addr")
        return None

    @property
    def mac_address(self) -> str | None:
        """Return the MAC address."""
        return self._mac

    @property
    def hostname(self) -> str | None:
        """Return the hostname."""
        if lan_devices := self.coordinator.data.get("lan_devices"):
            if isinstance(lan_devices, list):
                for device in lan_devices:
                    if device.get("l2ident", {}).get("id") == self._mac:
                        return device.get("primary_name")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if lan_devices := self.coordinator.data.get("lan_devices"):
            if isinstance(lan_devices, list):
                for device in lan_devices:
                    if device.get("l2ident", {}).get("id") == self._mac:
                        attributes = {
                            "vendor": device.get("vendor_name"),
                            "interface": device.get("interface"),
                            "last_seen": device.get("last_time_reachable"),
                            "access_point": device.get("access_point"),
                        }

                        # Add all IP addresses (IPv4 and IPv6)
                        if l3connectivities := device.get("l3connectivities"):
                            ipv4_addresses = []
                            ipv6_addresses = []
                            for conn in l3connectivities:
                                if conn.get("af") == "ipv4" and conn.get("addr"):
                                    ipv4_addresses.append(conn.get("addr"))
                                elif conn.get("af") == "ipv6" and conn.get("addr"):
                                    ipv6_addresses.append(conn.get("addr"))

                            if ipv4_addresses:
                                attributes["ipv4_addresses"] = ipv4_addresses
                            if ipv6_addresses:
                                attributes["ipv6_addresses"] = ipv6_addresses

                        # Add connection type if available
                        if l2ident := device.get("l2ident"):
                            if conn_type := l2ident.get("type"):
                                attributes["connection_type"] = conn_type

                        return attributes
        return {}
