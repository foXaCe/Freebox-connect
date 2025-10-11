"""Button platform for Freebox Connect."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_REPEATER, API_SYSTEM_REBOOT, DOMAIN
from .coordinator import FreeboxConnectDataUpdateCoordinator
from .device import get_freebox_repeater_device, get_freebox_server_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Freebox Connect button platform."""
    coordinator: FreeboxConnectDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get system data for device info
    system_data = coordinator.data.get("system", {})
    server_device = get_freebox_server_device(entry.entry_id, system_data)

    buttons = [
        FreeboxRebootButton(coordinator, entry, server_device),
    ]

    # Add repeater buttons
    repeater_data = coordinator.data.get("repeater", [])
    if isinstance(repeater_data, list):
        for repeater in repeater_data:
            # Validate repeater has required fields
            if not repeater.get("id"):
                _LOGGER.debug(f"Skipping repeater without ID: {repeater}")
                continue

            # Log repeater state for debugging
            state = repeater.get("state", "unknown")
            _LOGGER.debug(f"Found repeater {repeater.get('id')} with state: {state}")

            # Create buttons for all repeaters (don't filter by state)
            repeater_device = get_freebox_repeater_device(entry.entry_id, repeater)
            buttons.append(
                FreeboxRepeaterRebootButton(coordinator, entry, repeater, repeater_device)
            )
            _LOGGER.debug(f"Added reboot button for repeater {repeater.get('id')}")

    async_add_entities(buttons)


class FreeboxButtonBase(CoordinatorEntity, ButtonEntity):
    """Base class for Freebox buttons."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        translation_key: str,
        icon: str,
        device_info: dict,
        device_class: ButtonDeviceClass | None = None,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_unique_id = f"{entry.entry_id}_{translation_key.lower().replace(' ', '_')}"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class FreeboxRebootButton(FreeboxButtonBase):
    """Button to reboot the Freebox."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        device_info: dict,
    ) -> None:
        """Initialize the reboot button."""
        super().__init__(
            coordinator,
            entry,
            "freebox_reboot",
            "mdi:restart",
            device_info,
            ButtonDeviceClass.RESTART,
        )

    async def async_press(self) -> None:
        """Handle the button press - reboot the Freebox."""
        _LOGGER.info("Rebooting Freebox...")
        try:
            result = await self.coordinator.api.post(
                self.coordinator.session,
                API_SYSTEM_REBOOT
            )
            # Reboot endpoint may return None or empty result (server is rebooting)
            if result is not None:
                _LOGGER.info("Freebox reboot initiated successfully")
            else:
                _LOGGER.info("Freebox reboot command sent (server is rebooting)")
        except Exception as err:
            _LOGGER.error(f"Error rebooting Freebox: {err}")


class FreeboxRepeaterRebootButton(FreeboxButtonBase):
    """Button to reboot a Freebox repeater."""

    def __init__(
        self,
        coordinator: FreeboxConnectDataUpdateCoordinator,
        entry: ConfigEntry,
        repeater_data: dict,
        device_info: dict,
    ) -> None:
        """Initialize the repeater reboot button."""
        self._repeater_id = repeater_data.get("id", "unknown")
        super().__init__(
            coordinator,
            entry,
            "reboot",
            "mdi:restart",
            device_info,
            ButtonDeviceClass.RESTART,
        )
        # Update unique_id to include repeater_id
        self._attr_unique_id = f"{entry.entry_id}_repeater_{self._repeater_id}_reboot"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Check if coordinator has successful update
        if not self.coordinator.last_update_success:
            return False

        # Check if repeater still exists in data
        repeater_data = self.coordinator.data.get("repeater", [])
        if isinstance(repeater_data, list):
            for repeater in repeater_data:
                if repeater.get("id") == self._repeater_id:
                    return True

        return False

    async def async_press(self) -> None:
        """Handle the button press - reboot the repeater."""
        _LOGGER.info(f"Rebooting Freebox repeater {self._repeater_id}...")
        try:
            # Try with trailing slash
            result = await self.coordinator.api.post(
                self.coordinator.session,
                f"{API_REPEATER}{self._repeater_id}/reboot/"
            )
            if result is not None:
                _LOGGER.info(f"Freebox repeater {self._repeater_id} reboot initiated successfully")
                await self.coordinator.async_request_refresh()
            else:
                # Try without trailing slash
                _LOGGER.debug(f"Retrying reboot without trailing slash for repeater {self._repeater_id}")
                result = await self.coordinator.api.post(
                    self.coordinator.session,
                    f"{API_REPEATER}{self._repeater_id}/reboot"
                )
                if result is not None:
                    _LOGGER.info(f"Freebox repeater {self._repeater_id} reboot initiated successfully")
                    await self.coordinator.async_request_refresh()
                else:
                    _LOGGER.debug(f"Reboot endpoint not available for repeater {self._repeater_id} (this is normal for some repeater models)")
        except Exception as err:
            _LOGGER.error(f"Error rebooting Freebox repeater {self._repeater_id}: {err}")
