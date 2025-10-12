"""Config flow for Freebox Connect integration."""
from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_APP_TOKEN,
    CONF_USE_HTTPS,
    DEFAULT_APP_ID,
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_DEVICE_NAME,
    DOMAIN,
)
from .freebox_api import FreeboxAPI, FreeboxAuthorizationError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=46535): int,
    }
)


class FreeboxConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Freebox Connect."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.discovery_info: dict[str, Any] = {}
        self.freebox_api: FreeboxAPI | None = None
        self.app_token: str | None = None
        self.track_id: int | None = None
        self.use_https: bool = True


    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        # Extract host from discovery
        host = discovery_info.host
        port = discovery_info.port or 46535

        # Get Freebox name from properties if available
        properties = discovery_info.properties or {}
        fbx_name = properties.get("fbx_name", "Freebox")

        # Set unique ID to prevent duplicate entries
        await self.async_set_unique_id(f"{host}_{port}")
        self._abort_if_unique_id_configured()

        # Store discovery info for later use
        self.discovery_info = {
            CONF_HOST: host,
            CONF_PORT: port,
            "name": fbx_name,
        }

        # Show confirmation form to user
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the discovered Freebox."""
        if user_input is not None:
            return await self._async_create_entry_from_discovery()

        # Show form to user
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self.discovery_info.get("name", "Freebox"),
                "host": self.discovery_info[CONF_HOST],
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # If no host provided, try to discover
            if not user_input.get(CONF_HOST):
                return await self.async_step_discovery_scan()

            # Validate connection
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, 46535)

            # Check if already configured
            await self.async_set_unique_id(f"{host}_{port}")
            self._abort_if_unique_id_configured()

            # Try to connect to the Freebox
            success, use_https, api_info = await self._async_test_connection(host, port)
            if success:
                # Store use_https and device info for later
                self.use_https = use_https

                # Extract device model from API info
                device_name = "Freebox"
                if api_info:
                    device_name = api_info.get("device_name", "Freebox")

                # Store discovery info for title
                self.discovery_info = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    "name": device_name,
                }

                # Connection successful, now request authorization
                self.freebox_api = FreeboxAPI(
                    host=host,
                    port=port,
                    app_id=DEFAULT_APP_ID,
                    app_name=DEFAULT_APP_NAME,
                    app_version=DEFAULT_APP_VERSION,
                    device_name=DEFAULT_DEVICE_NAME,
                    use_https=use_https,
                )
                return await self.async_step_authorize()
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_discovery_scan(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Scan for Freebox on the network."""
        # Try to discover Freebox via mDNS
        # For now, fallback to asking user for manual entry
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=46535): int,
                }
            ),
            errors={"base": "discovery_failed"},
        )

    async def _async_test_connection(self, host: str, port: int) -> tuple[bool, bool, dict[str, Any] | None]:
        """Test connection to Freebox.

        Returns:
            Tuple of (success: bool, use_https: bool, api_info: dict | None)
        """
        session = async_get_clientsession(self.hass)

        # Create SSL context that accepts self-signed certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Try HTTPS first (Freebox API typically uses HTTPS)
        try:
            url = f"https://{host}:{port}/api_version"
            async with session.get(url, ssl=ssl_context, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    api_info = await response.json()
                    return True, True, api_info
        except Exception:
            pass

        # Fallback to HTTP if HTTPS fails
        try:
            url = f"http://{host}:{port}/api_version"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    api_info = await response.json()
                    return True, False, api_info
        except Exception:
            pass

        _LOGGER.error(f"Cannot connect to Freebox at {host}:{port} using HTTPS or HTTP")
        return False, True, None

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Request authorization from Freebox."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # User clicked continue after pressing the button
            return await self.async_step_check_auth()

        # Request authorization
        try:
            session = async_get_clientsession(self.hass)
            self.app_token, self.track_id = await self.freebox_api.request_authorization(session)

            return self.async_show_form(
                step_id="authorize",
                description_placeholders={
                    "message": "Appuyez sur le bouton de votre Freebox pour autoriser Home Assistant.\n\nUne fois que vous avez appuyé sur le bouton, cliquez sur 'Continuer'."
                },
            )
        except FreeboxAuthorizationError as err:
            _LOGGER.error(f"Authorization request failed: {err}")
            errors["base"] = "auth_failed"
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )
        except Exception as err:
            _LOGGER.exception(f"Unexpected error during authorization: {err}")
            errors["base"] = "unknown"
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

    async def async_step_check_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Check authorization status."""
        session = async_get_clientsession(self.hass)

        # Wait for authorization with timeout
        max_attempts = 30  # 30 attempts with 2 second delay = 1 minute
        for attempt in range(max_attempts):
            try:
                status = await self.freebox_api.track_authorization(session, self.track_id)

                if status == "granted":
                    # Authorization granted, show final step with permissions info
                    return await self.async_step_finish()
                elif status == "denied":
                    _LOGGER.error("Authorization denied by user")
                    return self.async_abort(reason="auth_denied")
                elif status == "timeout":
                    _LOGGER.error("Authorization timeout")
                    return self.async_abort(reason="auth_timeout")

                # Still pending, wait and retry
                await asyncio.sleep(2)

            except Exception as err:
                _LOGGER.error(f"Error checking authorization: {err}")
                return self.async_abort(reason="auth_check_failed")

        # Timeout
        _LOGGER.error("Authorization check timed out")
        return self.async_abort(reason="auth_timeout")

    async def _async_create_entry_from_discovery(self) -> FlowResult:
        """Create entry from discovery info."""
        host = self.discovery_info[CONF_HOST]
        port = self.discovery_info[CONF_PORT]
        name = self.discovery_info.get("name", "Freebox")

        success, use_https, api_info = await self._async_test_connection(host, port)
        if success:
            # Store use_https for later
            self.use_https = use_https

            # Update device name from API if available
            if api_info:
                device_name = api_info.get("device_name", "Freebox")
                self.discovery_info["name"] = device_name

            # Connection successful, now request authorization
            self.freebox_api = FreeboxAPI(
                host=host,
                port=port,
                app_id=DEFAULT_APP_ID,
                app_name=DEFAULT_APP_NAME,
                app_version=DEFAULT_APP_VERSION,
                device_name=DEFAULT_DEVICE_NAME,
                use_https=use_https,
            )
            return await self.async_step_authorize()

        return self.async_abort(reason="cannot_connect")

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Final step with permissions information."""
        if user_input is not None:
            # Create entry with device name if available
            device_name = self.discovery_info.get("name", "Freebox")
            title = device_name if device_name != "Freebox" else f"Freebox ({self.freebox_api.host})"

            return self.async_create_entry(
                title=title,
                data={
                    CONF_HOST: self.freebox_api.host,
                    CONF_PORT: self.freebox_api.port,
                    CONF_APP_TOKEN: self.app_token,
                    CONF_USE_HTTPS: self.use_https,
                },
            )

        return self.async_show_form(
            step_id="finish",
            description_placeholders={
                "message": "✅ Autorisation accordée !\n\n⚠️ IMPORTANT : Pour que toutes les fonctionnalités fonctionnent (contrôle LED, WiFi, redémarrage, etc.), vous devez activer les droits de gestion :\n\n1. Allez sur http://mafreebox.freebox.fr/\n2. Connectez-vous\n3. Allez dans 'Paramètres de la Freebox' → 'Gestion des accès'\n4. Cherchez 'Home Assistant Freebox Connect'\n5. Activez TOUS les droits de gestion\n6. Enregistrez\n\nCliquez sur 'Terminer' pour finaliser la configuration."
            },
        )
