"""Switch platform for Freebox Connect."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_LCD, API_REPEATER, API_WIFI_CONFIG, DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator
from .device import get_freebox_repeater_device, get_freebox_server_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Connect switch platform."""
    coordinator: FreeboxConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get system data for device info
    system_data = coordinator.data.get("system", {})
    server_device = get_freebox_server_device(entry.entry_id, system_data)

    switches = [
        FreeboxWiFiSwitch(coordinator, entry, server_device),
        FreeboxServerLEDSwitch(coordinator, entry, server_device),
        FreeboxHideWiFiKeySwitch(coordinator, entry, server_device),
        FreeboxRotateDisplaySwitch(coordinator, entry, server_device),
    ]

    # Add repeater switches
    repeater_data = coordinator.data.get("repeater", [])
    if isinstance(repeater_data, list):
        for repeater in repeater_data:
            # Validate repeater has required fields
            if not repeater.get("id"):
                continue

            repeater_device = get_freebox_repeater_device(entry.entry_id, repeater)
            # Only add LED switch (repeaters cannot be disabled via API)
            switches.append(
                FreeboxRepeaterLEDSwitch(coordinator, entry, repeater, repeater_device)
            )
            _LOGGER.debug(f"Added LED switch for repeater {repeater.get('id')}")

    async_add_entities(switches)


class FreeboxWiFiSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable WiFi."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the WiFi switch."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_wifi"
        self._attr_icon = "mdi:wifi"
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_unique_id = f"{entry.entry_id}_wifi_enabled"
        self._attr_device_info = device_info
        self._attr_assumed_state = False

    @property
    def is_on(self) -> bool:
        """Return true if WiFi is on."""
        wifi_config = self.coordinator.data.get("wifi_config")
        if wifi_config:
            return wifi_config.get("enabled", False)
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and "wifi_config" in self.coordinator.data
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn WiFi on."""
        _LOGGER.info("Turning Freebox WiFi on...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_WIFI_CONFIG, {"enabled": True}
            )
            _LOGGER.info("Freebox WiFi turned on successfully")
            # Update coordinator data immediately to avoid visual bounce
            if "wifi_config" in self.coordinator.data:
                self.coordinator.data["wifi_config"]["enabled"] = True
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error turning on Freebox WiFi: {err}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn WiFi off."""
        _LOGGER.info("Turning Freebox WiFi off...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_WIFI_CONFIG, {"enabled": False}
            )
            _LOGGER.info("Freebox WiFi turned off successfully")
            # Update coordinator data immediately to avoid visual bounce
            if "wifi_config" in self.coordinator.data:
                self.coordinator.data["wifi_config"]["enabled"] = False
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error turning off Freebox WiFi: {err}")


class FreeboxServerLEDSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable LED brightness on Freebox Server."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the server LED switch."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = "freebox_led_indicator"
        self._attr_icon = "mdi:led-on"
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_unique_id = f"{entry.entry_id}_server_led"
        self._attr_device_info = device_info
        self._attr_assumed_state = False

    @property
    def is_on(self) -> bool:
        """Return true if LED is on (not hidden)."""
        lcd_config = self.coordinator.data.get("lcd_config")
        if lcd_config and "hide_status_led" in lcd_config:
            # LED is ON if NOT hidden
            return not lcd_config.get("hide_status_led", False)
        # Default to on if data not available
        return True

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and "lcd_config" in self.coordinator.data
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn LED on (show status LED)."""
        _LOGGER.info("Turning Freebox server LED on...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_LCD, {"hide_status_led": False}
            )
            _LOGGER.info("Freebox server LED turned on successfully")
            # Update coordinator data immediately to avoid visual bounce
            if "lcd_config" in self.coordinator.data:
                self.coordinator.data["lcd_config"]["hide_status_led"] = False
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error turning on Freebox server LED: {err}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn LED off (hide status LED)."""
        _LOGGER.info("Turning Freebox server LED off...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_LCD, {"hide_status_led": True}
            )
            _LOGGER.info("Freebox server LED turned off successfully")
            # Update coordinator data immediately to avoid visual bounce
            if "lcd_config" in self.coordinator.data:
                self.coordinator.data["lcd_config"]["hide_status_led"] = True
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error turning off Freebox server LED: {err}")


class FreeboxRepeaterLEDSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to enable/disable LED indicator on Freebox repeater."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        repeater_data: dict,
        device_info: dict,
    ) -> None:
        """Initialize the repeater LED switch."""
        super().__init__(coordinator)
        self._repeater_id = repeater_data.get("id", "unknown")
        self._attr_has_entity_name = True
        self._attr_translation_key = "led_indicator"
        self._attr_icon = "mdi:led-on"
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_unique_id = f"{entry.entry_id}_repeater_{self._repeater_id}_led"
        self._attr_device_info = device_info
        self._attr_assumed_state = False

    @property
    def is_on(self) -> bool:
        """Return true if LED is on."""
        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        # API uses "led_activated"
                        return repeater.get("led_activated", True)
        return True  # Default to on if not found

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        if repeater_data := self.coordinator.data.get("repeater"):
            if isinstance(repeater_data, list):
                for repeater in repeater_data:
                    if repeater.get("id") == self._repeater_id:
                        return True
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn LED indicator on."""
        _LOGGER.info(f"Turning Freebox repeater {self._repeater_id} LED on...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session,
                f"{API_REPEATER}{self._repeater_id}",
                {"led_activated": True},
            )
            _LOGGER.info(
                f"Freebox repeater {self._repeater_id} LED turned on successfully"
            )
            # Update coordinator data immediately to avoid visual bounce
            if repeater_data := self.coordinator.data.get("repeater"):
                if isinstance(repeater_data, list):
                    for repeater in repeater_data:
                        if repeater.get("id") == self._repeater_id:
                            repeater["led_activated"] = True
                            break
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(
                f"Error turning on Freebox repeater {self._repeater_id} LED: {err}"
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn LED indicator off."""
        _LOGGER.info(f"Turning Freebox repeater {self._repeater_id} LED off...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session,
                f"{API_REPEATER}{self._repeater_id}",
                {"led_activated": False},
            )
            _LOGGER.info(
                f"Freebox repeater {self._repeater_id} LED turned off successfully"
            )
            # Update coordinator data immediately to avoid visual bounce
            if repeater_data := self.coordinator.data.get("repeater"):
                if isinstance(repeater_data, list):
                    for repeater in repeater_data:
                        if repeater.get("id") == self._repeater_id:
                            repeater["led_activated"] = False
                            break
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(
                f"Error turning off Freebox repeater {self._repeater_id} LED: {err}"
            )


class FreeboxHideWiFiKeySwitch(CoordinatorEntity, SwitchEntity):
    """Switch to hide/show WiFi key on Freebox display."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the hide WiFi key switch."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = "hide_wifi_key"
        self._attr_icon = "mdi:key-wireless"
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_unique_id = f"{entry.entry_id}_hide_wifi_key"
        self._attr_device_info = device_info
        self._attr_assumed_state = False

    @property
    def is_on(self) -> bool:
        """Return true if WiFi key is hidden."""
        lcd_config = self.coordinator.data.get("lcd_config")
        if lcd_config:
            return lcd_config.get("hide_wifi_key", False)
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and "lcd_config" in self.coordinator.data
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Hide WiFi key on display."""
        _LOGGER.info("Hiding Freebox WiFi key on display...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_LCD, {"hide_wifi_key": True}
            )
            _LOGGER.info("Freebox WiFi key hidden successfully")
            if "lcd_config" in self.coordinator.data:
                self.coordinator.data["lcd_config"]["hide_wifi_key"] = True
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error hiding Freebox WiFi key: {err}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Show WiFi key on display."""
        _LOGGER.info("Showing Freebox WiFi key on display...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_LCD, {"hide_wifi_key": False}
            )
            _LOGGER.info("Freebox WiFi key shown successfully")
            if "lcd_config" in self.coordinator.data:
                self.coordinator.data["lcd_config"]["hide_wifi_key"] = False
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error showing Freebox WiFi key: {err}")


class FreeboxRotateDisplaySwitch(CoordinatorEntity, SwitchEntity):
    """Switch to rotate Freebox display orientation (0° / 180°)."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the rotate display switch."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = "display_rotated_180°"
        self._attr_icon = "mdi:phone-rotate-landscape"
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._attr_unique_id = f"{entry.entry_id}_rotate_display"
        self._attr_device_info = device_info
        self._attr_assumed_state = False

    @property
    def is_on(self) -> bool:
        """Return true if display is rotated 180°."""
        lcd_config = self.coordinator.data.get("lcd_config")
        if lcd_config:
            orientation = lcd_config.get("orientation", 0)
            return orientation == 180
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and "lcd_config" in self.coordinator.data
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Rotate display to 180°."""
        _LOGGER.info("Rotating Freebox display to 180°...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_LCD, {"orientation": 180}
            )
            _LOGGER.info("Freebox display rotated to 180° successfully")
            if "lcd_config" in self.coordinator.data:
                self.coordinator.data["lcd_config"]["orientation"] = 180
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error rotating Freebox display: {err}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Rotate display to 0° (normal)."""
        _LOGGER.info("Rotating Freebox display to 0° (normal)...")
        try:
            await self.coordinator.api.put(
                self.coordinator.session, API_LCD, {"orientation": 0}
            )
            _LOGGER.info("Freebox display rotated to 0° successfully")
            if "lcd_config" in self.coordinator.data:
                self.coordinator.data["lcd_config"]["orientation"] = 0
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error(f"Error rotating Freebox display: {err}")
