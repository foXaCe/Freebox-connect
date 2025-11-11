"""Freebox API authentication and communication."""

from __future__ import annotations

import hashlib
import hmac
import logging
import ssl
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class FreeboxAuthorizationError(Exception):
    """Exception raised when authorization fails."""


class FreeboxAPI:
    """Handle Freebox API authentication and requests."""

    def __init__(
        self,
        host: str,
        port: int = 46535,
        app_id: str = "home_assistant_freebox_connect",
        app_name: str = "Home Assistant Freebox Connect",
        app_version: str = "0.1.0",
        device_name: str = "Home Assistant",
        use_https: bool = True,
    ) -> None:
        """Initialize Freebox API client."""
        self.host = host
        self.port = port
        self.use_https = use_https
        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}:{port}"

        # App identification
        self.app_id = app_id
        self.app_name = app_name
        self.app_version = app_version
        self.device_name = device_name

        # Auth tokens
        self.app_token: str | None = None
        self.session_token: str | None = None
        self.challenge: str | None = None

        # SSL context for self-signed certificates (only for HTTPS)
        if use_https:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
        else:
            self.ssl_context = None

    def _get_ssl_context(self):
        """Get SSL context for requests (None for HTTP, context for HTTPS)."""
        return self.ssl_context if self.use_https else False

    async def get_api_version(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        """Get Freebox API version information."""
        url = f"{self.base_url}/api_version"
        async with session.get(url, ssl=self._get_ssl_context()) as response:
            if response.status == 200:
                return await response.json()
            raise FreeboxAuthorizationError(
                f"Failed to get API version: {response.status}"
            )

    async def request_authorization(
        self, session: aiohttp.ClientSession
    ) -> tuple[str, int]:
        """
        Request authorization from Freebox.

        Returns:
            Tuple of (app_token, track_id) - track_id is used to check auth status
        """
        url = f"{self.base_url}/api/v11/login/authorize"

        payload = {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "device_name": self.device_name,
        }

        _LOGGER.debug(f"Requesting authorization from Freebox: {payload}")

        async with session.post(
            url, json=payload, ssl=self._get_ssl_context()
        ) as response:
            if response.status != 200:
                raise FreeboxAuthorizationError(
                    f"Failed to request authorization: {response.status}"
                )

            data = await response.json()

            if not data.get("success"):
                error = data.get("msg", "Unknown error")
                raise FreeboxAuthorizationError(
                    f"Authorization request failed: {error}"
                )

            result = data["result"]
            app_token = result["app_token"]
            track_id = result["track_id"]

            _LOGGER.info(
                f"Authorization requested. Please press the button on your Freebox. Track ID: {track_id}"
            )

            return app_token, track_id

    async def track_authorization(
        self, session: aiohttp.ClientSession, track_id: int
    ) -> str:
        """
        Track authorization status.

        Returns:
            Status: 'pending', 'granted', 'denied', 'timeout', 'unknown'
        """
        url = f"{self.base_url}/api/v11/login/authorize/{track_id}"

        async with session.get(url, ssl=self._get_ssl_context()) as response:
            if response.status != 200:
                return "unknown"

            data = await response.json()

            if not data.get("success"):
                return "unknown"

            result = data["result"]
            status = result.get("status", "unknown")

            _LOGGER.debug(f"Authorization status: {status}")

            return status

    async def open_session(self, session: aiohttp.ClientSession) -> str:
        """
        Open a session with the Freebox.

        Returns:
            Session token to use for authenticated requests
        """
        if not self.app_token:
            raise FreeboxAuthorizationError(
                "No app_token available. Please authorize first."
            )

        # Get challenge
        url = f"{self.base_url}/api/v11/login"
        async with session.get(url, ssl=self._get_ssl_context()) as response:
            if response.status != 200:
                raise FreeboxAuthorizationError(
                    f"Failed to get challenge: {response.status}"
                )

            data = await response.json()

            if not data.get("success"):
                raise FreeboxAuthorizationError("Failed to get challenge")

            self.challenge = data["result"]["challenge"]

        # Compute password using HMAC-SHA1
        password = hmac.new(
            self.app_token.encode(), self.challenge.encode(), hashlib.sha1
        ).hexdigest()

        # Open session
        url = f"{self.base_url}/api/v11/login/session/"
        payload = {
            "app_id": self.app_id,
            "password": password,
        }

        async with session.post(
            url, json=payload, ssl=self._get_ssl_context()
        ) as response:
            if response.status != 200:
                raise FreeboxAuthorizationError(
                    f"Failed to open session: {response.status}"
                )

            data = await response.json()

            if not data.get("success"):
                error = data.get("msg", "Unknown error")
                raise FreeboxAuthorizationError(f"Session opening failed: {error}")

            self.session_token = data["result"]["session_token"]
            _LOGGER.info("Session opened successfully")

            return self.session_token

    async def check_permissions(
        self, session: aiohttp.ClientSession
    ) -> dict[str, Any] | None:
        """
        Check granted permissions for the app.

        Returns:
            Dictionary of permissions or None if failed
        """
        try:
            result = await self.get(session, "/api/v11/login/perms/")
            if result:
                _LOGGER.debug(f"Current permissions: {result}")
                return result
            return None
        except Exception as err:
            _LOGGER.error(f"Error checking permissions: {err}")
            return None

    async def close_session(self, session: aiohttp.ClientSession) -> None:
        """Close the current session."""
        if not self.session_token:
            return

        url = f"{self.base_url}/api/v11/login/logout/"
        headers = {"X-Fbx-App-Auth": self.session_token}

        try:
            async with session.post(
                url, headers=headers, ssl=self._get_ssl_context()
            ) as response:
                if response.status == 200:
                    _LOGGER.debug("Session closed successfully")
                else:
                    _LOGGER.warning(f"Failed to close session: {response.status}")
        except Exception as err:
            _LOGGER.warning(f"Error closing session: {err}")
        finally:
            self.session_token = None

    async def get(
        self, session: aiohttp.ClientSession, endpoint: str
    ) -> dict[str, Any] | None:
        """
        Make an authenticated GET request to the Freebox API.

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint (e.g., "/api/v11/system/")

        Returns:
            API response result or None if failed
        """
        if not self.session_token:
            await self.open_session(session)

        url = f"{self.base_url}{endpoint}"
        headers = {"X-Fbx-App-Auth": self.session_token}

        try:
            async with session.get(
                url, headers=headers, ssl=self._get_ssl_context()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        return data.get("result")
                    _LOGGER.warning(f"API call to {endpoint} failed: {data.get('msg')}")
                    return None
                if response.status == 403:
                    # Session expired, try to reopen
                    _LOGGER.info("Session expired, reopening...")
                    await self.open_session(session)
                    # Retry the request
                    headers = {"X-Fbx-App-Auth": self.session_token}
                    async with session.get(
                        url, headers=headers, ssl=self._get_ssl_context()
                    ) as retry_response:
                        if retry_response.status == 200:
                            data = await retry_response.json()
                            if data.get("success"):
                                return data.get("result")
                        return None
                else:
                    _LOGGER.warning(f"Failed to fetch {endpoint}: {response.status}")
                    return None
        except Exception as err:
            _LOGGER.error(f"Error fetching {endpoint}: {err}")
            return None

    async def put(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Make an authenticated PUT request to the Freebox API.

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint (e.g., "/api/v11/wifi/config/")
            payload: Optional JSON payload to send

        Returns:
            API response result or None if failed
        """
        if not self.session_token:
            await self.open_session(session)

        url = f"{self.base_url}{endpoint}"
        headers = {"X-Fbx-App-Auth": self.session_token}

        try:
            async with session.put(
                url, headers=headers, json=payload, ssl=self._get_ssl_context()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        return data.get("result")
                    _LOGGER.warning(f"API PUT to {endpoint} failed: {data.get('msg')}")
                    return None
                if response.status == 403:
                    # Session expired, try to reopen
                    _LOGGER.info("Session expired, reopening...")
                    await self.open_session(session)
                    # Retry the request
                    headers = {"X-Fbx-App-Auth": self.session_token}
                    async with session.put(
                        url, headers=headers, json=payload, ssl=self._get_ssl_context()
                    ) as retry_response:
                        if retry_response.status == 200:
                            data = await retry_response.json()
                            if data.get("success"):
                                return data.get("result")
                        return None
                else:
                    _LOGGER.warning(f"Failed to PUT {endpoint}: {response.status}")
                    return None
        except Exception as err:
            _LOGGER.error(f"Error performing PUT on {endpoint}: {err}")
            return None

    async def post(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Make an authenticated POST request to the Freebox API.

        Args:
            session: aiohttp ClientSession
            endpoint: API endpoint (e.g., "/api/v11/system/reboot/")
            payload: Optional JSON payload to send

        Returns:
            API response result or None if failed
        """
        if not self.session_token:
            await self.open_session(session)

        url = f"{self.base_url}{endpoint}"
        headers = {"X-Fbx-App-Auth": self.session_token}

        try:
            async with session.post(
                url, headers=headers, json=payload, ssl=self._get_ssl_context()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        return data.get("result")
                    _LOGGER.warning(f"API POST to {endpoint} failed: {data.get('msg')}")
                    return None
                if response.status == 403:
                    # Session expired, try to reopen
                    _LOGGER.info("Session expired, reopening...")
                    await self.open_session(session)
                    # Retry the request
                    headers = {"X-Fbx-App-Auth": self.session_token}
                    async with session.post(
                        url, headers=headers, json=payload, ssl=self._get_ssl_context()
                    ) as retry_response:
                        if retry_response.status == 200:
                            data = await retry_response.json()
                            if data.get("success"):
                                return data.get("result")
                        return None
                else:
                    _LOGGER.warning(f"Failed to POST {endpoint}: {response.status}")
                    return None
        except Exception as err:
            _LOGGER.error(f"Error POSTing {endpoint}: {err}")
            return None

    def set_app_token(self, app_token: str) -> None:
        """Set the app token (from saved configuration)."""
        self.app_token = app_token
        _LOGGER.debug("App token set")
