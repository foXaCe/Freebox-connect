"""Data update coordinator for Freebox Connect."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientSession
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_CONNECTION,
    API_LAN_BROWSER_PUB,
    API_LCD,
    API_REPEATER,
    API_STORAGE,
    API_SYSTEM,
    API_WIFI_AP,
    API_WIFI_CONFIG,
    API_WIFI_STATE,
    DOMAIN,
    UPDATE_INTERVAL,
)
from .freebox_api import FreeboxAPI

_LOGGER = logging.getLogger(__name__)


class FreeboxConnectDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Freebox data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: ClientSession,
        host: str,
        port: int = 46535,
        app_token: str | None = None,
        use_https: bool = True,
    ) -> None:
        """Initialize the coordinator."""
        self.session = session
        self.host = host
        self.port = port

        # Initialize Freebox API client
        self.api = FreeboxAPI(host=host, port=port, use_https=use_https)
        if app_token:
            self.api.set_app_token(app_token)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Freebox API."""
        try:
            data = {}

            # Check permissions on first update
            if not hasattr(self, "_permissions_checked"):
                permissions = await self.api.check_permissions(self.session)
                if permissions:
                    data["permissions"] = permissions
                self._permissions_checked = True

            # Fetch system info
            system_data = await self.api.get(self.session, API_SYSTEM)
            if system_data:
                data["system"] = system_data

            # Fetch connection info
            connection_data = await self.api.get(self.session, API_CONNECTION)
            if connection_data:
                data["connection"] = connection_data

            # Fetch WiFi info
            wifi_config_data = await self.api.get(self.session, API_WIFI_CONFIG)
            if wifi_config_data:
                data["wifi_config"] = wifi_config_data

            wifi_ap_data = await self.api.get(self.session, API_WIFI_AP)
            if wifi_ap_data:
                data["wifi_ap"] = wifi_ap_data

            wifi_state_data = await self.api.get(self.session, API_WIFI_STATE)
            if wifi_state_data:
                data["wifi_state"] = wifi_state_data

            # Fetch repeater info
            repeater_data = await self.api.get(self.session, API_REPEATER)
            if repeater_data:
                data["repeater"] = repeater_data

            # Fetch storage info
            storage_data = await self.api.get(self.session, API_STORAGE)
            if storage_data:
                data["storage"] = storage_data

            # Fetch LAN devices
            lan_devices = await self.api.get(self.session, API_LAN_BROWSER_PUB)
            if lan_devices:
                data["lan_devices"] = lan_devices

            # Fetch LCD config
            lcd_config = await self.api.get(self.session, API_LCD)
            if lcd_config:
                data["lcd_config"] = lcd_config

            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with Freebox API: {err}") from err
