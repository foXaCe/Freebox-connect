"""Sensor platform for Freebox Connect."""
from __future__ import annotations

import time

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator
from .device import get_freebox_repeater_device, get_freebox_server_device


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Connect sensor platform."""
    coordinator: FreeboxConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get system data for device info
    system_data = coordinator.data.get("system", {})
    server_device = get_freebox_server_device(entry.entry_id, system_data)

    entities = [
        FreeboxConnectionSensor(coordinator, entry, server_device),
        FreeboxSystemSensor(coordinator, entry, server_device),
        FreeboxWiFiStateSensor(coordinator, entry, server_device),
        FreeboxStorageSensor(coordinator, entry, server_device),
        FreeboxServerConnectedDevicesSensor(coordinator, entry, server_device),
    ]

    # Add repeater entities
    repeater_data = coordinator.data.get("repeater", [])
    if isinstance(repeater_data, list):
        for repeater in repeater_data:
            # Validate repeater has required fields
            if not repeater.get("id"):
                continue

            repeater_device = get_freebox_repeater_device(entry.entry_id, repeater)
            entities.extend([
                FreeboxRepeaterSignalSensor(coordinator, entry, repeater, repeater_device),
                FreeboxRepeaterStateSensor(coordinator, entry, repeater, repeater_device),
                FreeboxRepeaterUptimeSensor(coordinator, entry, repeater, repeater_device),
                FreeboxRepeaterConnectedDevicesSensor(coordinator, entry, repeater, repeater_device),
            ])

    async_add_entities(entities)


class FreeboxConnectionSensor(CoordinatorEntity, SensorEntity):
    """Representation of Freebox connection status sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connection_status"
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_connection_status"
        self._attr_icon = "mdi:wan"
        self._attr_device_info = device_info
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["up", "down", "unknown"]

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if connection := self.coordinator.data.get("connection"):
            return connection.get("state", "unknown")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if connection := self.coordinator.data.get("connection"):
            attributes = {
                "type": connection.get("type"),
                "media": connection.get("media"),
                "ipv4": connection.get("ipv4"),
                "rate_down": connection.get("rate_down"),
                "rate_up": connection.get("rate_up"),
            }

            # Add IPv6 if available
            if ipv6 := connection.get("ipv6"):
                attributes["ipv6"] = ipv6

            return attributes
        return {}


class FreeboxSystemSensor(CoordinatorEntity, SensorEntity):
    """Representation of Freebox system sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_system_uptime"
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_uptime"
        self._attr_icon = "mdi:timer"
        self._attr_device_info = device_info

    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in a human-readable way."""
        if seconds < 60:
            return f"{seconds} s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes} min {secs} s"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} h {minutes} min"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            minutes = (seconds % 3600) // 60
            return f"{days} j {hours} h {minutes} min"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if system := self.coordinator.data.get("system"):
            uptime = system.get("uptime_val") or system.get("uptime")
            # Si c'est une chaîne, essayer de la convertir
            if isinstance(uptime, str):
                # L'API retourne parfois une chaîne formatée, chercher uptime_val
                uptime = system.get("uptime_val", 0)
            if uptime and isinstance(uptime, (int, float)):
                return self._format_uptime(int(uptime))
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if system := self.coordinator.data.get("system"):
            uptime = system.get("uptime_val") or system.get("uptime")
            if isinstance(uptime, str):
                uptime = system.get("uptime_val", 0)

            attributes = {
                "serial": system.get("serial"),
                "firmware": system.get("firmware_version"),
                "mac": system.get("mac"),
                "uptime_seconds": uptime if isinstance(uptime, (int, float)) else 0,
            }

            # Only add model if it's not null
            if model := system.get("model_name"):
                attributes["model"] = model

            return attributes
        return {}


class FreeboxWiFiStateSensor(CoordinatorEntity, SensorEntity):
    """Representation of Freebox WiFi state sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_wifi_state"
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_wifi_state"
        self._attr_icon = "mdi:wifi"
        self._attr_device_info = device_info
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["enabled", "disabled"]

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if wifi_state := self.coordinator.data.get("wifi_state"):
            # L'API retourne {"enabled": true/false} ou {"state": "on"/"off"}
            enabled = wifi_state.get("enabled")
            if enabled is not None:
                return "enabled" if enabled is True else "disabled"

            # Fallback: vérifier le champ "state"
            state = wifi_state.get("state")
            if state:
                return "enabled" if state in ["on", "enabled", "active", "1", 1] else "disabled"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if wifi_state := self.coordinator.data.get("wifi_state"):
            attributes = {}

            # Add power saving if available
            if power_saving := wifi_state.get("power_saving_capability"):
                attributes["power_saving"] = power_saving

            # Add detected WiFi bands
            if expected_phys := wifi_state.get("expected_phys"):
                detected_bands = [
                    phy.get("band")
                    for phy in expected_phys
                    if phy.get("detected")
                ]
                if detected_bands:
                    attributes["detected_bands"] = ", ".join(detected_bands)

            return attributes
        return {}


class FreeboxRepeaterSignalSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Freebox repeater signal sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        repeater_data: dict,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._repeater_id = repeater_data.get("id", "unknown")
        self._attr_unique_id = f"{entry.entry_id}_repeater_{self._repeater_id}_signal"
        self._attr_has_entity_name = True
        self._attr_translation_key = "signal_quality"
        self._attr_icon = "mdi:signal"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        # Try direct field names first
                        signal = (
                            repeater.get("signal_quality")
                            or repeater.get("link_quality")
                            or repeater.get("signal")
                            or repeater.get("rssi")
                        )

                        if signal is not None:
                            return int(signal)

                        # Check backhaul array for best connection signal
                        if backhaul := repeater.get("backhaul"):
                            if isinstance(backhaul, list):
                                # Find the best backhaul (marked as best: True)
                                for bh in backhaul:
                                    if bh.get("best") and bh.get("signal"):
                                        # Convert dBm to quality percentage
                                        # Signal is negative dBm (-30 to -90)
                                        # -30 dBm = excellent (100%), -90 dBm = poor (0%)
                                        signal_dbm = bh.get("signal")
                                        quality = max(0, min(100, ((signal_dbm + 90) * 100) // 60))
                                        return quality

                                # If no best backhaul, use first one with signal
                                for bh in backhaul:
                                    if bh.get("signal"):
                                        signal_dbm = bh.get("signal")
                                        quality = max(0, min(100, ((signal_dbm + 90) * 100) // 60))
                                        return quality
                        return None
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        # API uses 'status' field, not 'state'
                        status = repeater.get("status") or repeater.get("state")
                        connected = repeater.get("connected_devices", 0)

                        attributes = {
                            "state": status,
                            "connected_devices": connected,
                        }

                        # Add repeater identification info
                        if name := repeater.get("name"):
                            attributes["name"] = name
                        if mac := repeater.get("main_mac") or repeater.get("mac"):
                            attributes["mac"] = mac
                        if model := repeater.get("model"):
                            attributes["model"] = model

                        return attributes
        return {}


class FreeboxStorageSensor(CoordinatorEntity, SensorEntity):
    """Representation of Freebox storage sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_storage_total"
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_storage"
        self._attr_icon = "mdi:harddisk"
        self._attr_native_unit_of_measurement = "GB"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = device_info

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if storage := self.coordinator.data.get("storage"):
            if isinstance(storage, list) and len(storage) > 0:
                # Convert bytes to GB
                total_bytes = sum(disk.get("total_bytes", 0) for disk in storage)
                return round(total_bytes / (1024**3), 2)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if storage := self.coordinator.data.get("storage"):
            if isinstance(storage, list):
                return {
                    "disks": [
                        {
                            "name": disk.get("name") or f"Disque {disk.get('type', 'unknown').upper()}",
                            "type": disk.get("type"),
                            "total_gb": round(disk.get("total_bytes", 0) / (1024**3), 2),
                            "used_gb": round(
                                (disk.get("total_bytes", 0) - disk.get("free_bytes", 0)) / (1024**3),
                                2,
                            ),
                        }
                        for disk in storage
                    ]
                }
        return {}


class FreeboxServerConnectedDevicesSensor(CoordinatorEntity, SensorEntity):
    """Representation of Freebox server connected devices sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_server_connected_devices"
        self._attr_has_entity_name = True
        self._attr_translation_key = "connected_devices"
        self._attr_icon = "mdi:devices"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        count = 0
        if lan_devices := self.coordinator.data.get("lan_devices"):
            if isinstance(lan_devices, list):
                for device in lan_devices:
                    if device.get("active"):
                        # Count devices connected to gateway (main Freebox)
                        access_point = device.get("access_point", {})
                        if access_point.get("type") == "gateway":
                            count += 1
        return count

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        attributes = {}
        connected_device_names = []

        if lan_devices := self.coordinator.data.get("lan_devices"):
            if isinstance(lan_devices, list):
                for device in lan_devices:
                    if device.get("active"):
                        access_point = device.get("access_point", {})
                        if access_point.get("type") == "gateway":
                            device_name = device.get("primary_name", "unknown")
                            connected_device_names.append(device_name)

        if connected_device_names:
            attributes["connected"] = connected_device_names

        return attributes


class FreeboxRepeaterStateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Freebox repeater state sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        repeater_data: dict,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._repeater_id = repeater_data.get("id", "unknown")
        self._attr_unique_id = f"{entry.entry_id}_repeater_{self._repeater_id}_state"
        self._attr_has_entity_name = True
        self._attr_translation_key = "state"
        self._attr_icon = "mdi:state-machine"
        self._attr_device_info = device_info
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["running", "stopped", "unknown"]

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        # API uses 'status' field, not 'state'
                        return repeater.get("status") or repeater.get("state", "unknown")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        attributes = {}

                        # Add repeater identification and status info
                        if name := repeater.get("name"):
                            attributes["name"] = name
                        if signal := repeater.get("signal_quality"):
                            attributes["signal_quality"] = signal
                        if connected := repeater.get("connected_devices"):
                            attributes["connected_devices"] = connected
                        if mac := repeater.get("main_mac") or repeater.get("mac"):
                            attributes["mac"] = mac
                        if model := repeater.get("model"):
                            attributes["model"] = model
                        # Try uptime field first, then calculate from boot_time
                        uptime = repeater.get("uptime")
                        if uptime is None and (boot_time := repeater.get("boot_time")):
                            current_time = int(time.time())
                            uptime = current_time - boot_time
                        if uptime:
                            attributes["uptime"] = uptime

                        return attributes
        return {}


class FreeboxRepeaterUptimeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Freebox repeater uptime sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        repeater_data: dict,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._repeater_id = repeater_data.get("id", "unknown")
        self._attr_unique_id = f"{entry.entry_id}_repeater_{self._repeater_id}_uptime"
        self._attr_has_entity_name = True
        self._attr_translation_key = "uptime"
        self._attr_icon = "mdi:timer"
        self._attr_device_info = device_info

    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in a human-readable way."""
        if seconds < 60:
            return f"{seconds} s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes} min {secs} s"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} h {minutes} min"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            minutes = (seconds % 3600) // 60
            return f"{days} j {hours} h {minutes} min"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        # Try uptime field first
                        uptime = repeater.get("uptime")

                        # If not found, calculate from boot_time
                        if uptime is None and (boot_time := repeater.get("boot_time")):
                            current_time = int(time.time())
                            uptime = current_time - boot_time

                        if uptime and isinstance(uptime, (int, float)):
                            return self._format_uptime(int(uptime))
        return None

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        # Try uptime field first
                        uptime = repeater.get("uptime")

                        # If not found, calculate from boot_time
                        if uptime is None and (boot_time := repeater.get("boot_time")):
                            current_time = int(time.time())
                            uptime = current_time - boot_time

                        attributes = {
                            "uptime_seconds": uptime if isinstance(uptime, (int, float)) else 0,
                        }

                        # Add additional repeater info
                        # API uses 'status' field, not 'state'
                        if status := repeater.get("status") or repeater.get("state"):
                            attributes["state"] = status
                        if name := repeater.get("name"):
                            attributes["name"] = name
                        if firmware := repeater.get("firmware_version"):
                            attributes["firmware"] = firmware
                        if mac := repeater.get("main_mac") or repeater.get("mac"):
                            attributes["mac"] = mac
                        if model := repeater.get("model"):
                            attributes["model"] = model
                        if serial := repeater.get("sn") or repeater.get("serial"):
                            attributes["serial"] = serial

                        return attributes
        return {}


class FreeboxRepeaterConnectedDevicesSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Freebox repeater connected devices sensor."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        repeater_data: dict,
        device_info: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._repeater_id = repeater_data.get("id", "unknown")
        self._attr_unique_id = f"{entry.entry_id}_repeater_{self._repeater_id}_connected_devices"
        self._attr_has_entity_name = True
        self._attr_translation_key = "connected_devices"
        self._attr_icon = "mdi:devices"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        # Count devices connected to this repeater by matching access_point
                        # with repeater's fronthaul BSSIDs
                        count = 0

                        # Get all BSSIDs from this repeater's fronthaul
                        repeater_bssids = []
                        if fronthaul := repeater.get("fronthaul"):
                            if isinstance(fronthaul, list):
                                for fh in fronthaul:
                                    if bssid := fh.get("bssid"):
                                        repeater_bssids.append(bssid.upper())

                        # Count LAN devices connected to this repeater's access points
                        if repeater_bssids and (lan_devices := self.coordinator.data.get("lan_devices")):
                            if isinstance(lan_devices, list):
                                for device in lan_devices:
                                    if device.get("active"):
                                        # Get BSSID from wifi_information if device is connected via WiFi
                                        wifi_info = device.get("access_point", {}).get("wifi_information", {})
                                        bssid = wifi_info.get("bssid", "").upper() if wifi_info else ""

                                        if bssid and bssid in repeater_bssids:
                                            count += 1

                        return count
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional attributes."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        attributes = {}

                        # Add repeater identification info
                        if name := repeater.get("name"):
                            attributes["name"] = name
                        # API uses 'status' field, not 'state'
                        if status := repeater.get("status") or repeater.get("state"):
                            attributes["state"] = status
                        if signal := repeater.get("signal_quality"):
                            attributes["signal_quality"] = signal
                        if mac := repeater.get("main_mac") or repeater.get("mac"):
                            attributes["mac"] = mac
                        if model := repeater.get("model"):
                            attributes["model"] = model

                        # Add list of connected device names
                        connected_device_names = []
                        repeater_bssids = []
                        if fronthaul := repeater.get("fronthaul"):
                            if isinstance(fronthaul, list):
                                for fh in fronthaul:
                                    if bssid := fh.get("bssid"):
                                        repeater_bssids.append(bssid.upper())

                        if repeater_bssids and (lan_devices := self.coordinator.data.get("lan_devices")):
                            if isinstance(lan_devices, list):
                                for device in lan_devices:
                                    if device.get("active"):
                                        wifi_info = device.get("access_point", {}).get("wifi_information", {})
                                        bssid = wifi_info.get("bssid", "").upper() if wifi_info else ""
                                        if bssid and bssid in repeater_bssids:
                                            device_name = device.get("primary_name", "unknown")
                                            connected_device_names.append(device_name)

                        if connected_device_names:
                            attributes["connected"] = connected_device_names

                        return attributes
        return {}
