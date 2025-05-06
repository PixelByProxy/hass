"""API for the Minecraft Server integration."""

from dataclasses import dataclass
from datetime import datetime
import logging

from aiohttp import ClientError, ClientSession

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

LOOKUP_TIMEOUT: float = 10
DATA_UPDATE_TIMEOUT: float = 10
DATA_UPDATE_RETRIES: int = 3


@dataclass
class WorkerData:
    """Representation of Pool worker data."""

    name: str
    best_difficulty: float
    hash_rate: float
    start_time: datetime
    last_seen: datetime


@dataclass
class ClientData:
    """Representation of Pool client data."""

    best_difficulty: float
    worker_count: int
    worker_list: list[WorkerData] | None = None


class PublicPoolServerAddressError(Exception):
    """Raised when the input address is invalid."""


class PublicPoolServerConnectionError(Exception):
    """Raised when no data can be fetched from the server."""


class PublicPoolServerClientError(Exception):
    """Raised when the client was not found."""


class PoolNotInitializedError(Exception):
    """Raised when APIs are used although server instance is not initialized yet."""


class PublicPoolServer:
    """Public Pool Server API."""

    def __init__(self, hass: HomeAssistant, url: str, address: str) -> None:
        """Initialize server instance."""
        self._hass = hass
        self._url = url
        self._address = address

    async def async_initialize(self) -> None:
        """Perform async initialization of server instance."""
        try:
            await self.async_get_data()
            _LOGGER.debug(
                "Initializing server instance with address '%s'", self._address
            )
        except ValueError as error:
            raise PublicPoolServerAddressError(
                f"Lookup of '{self._address}' failed: {self._get_error_message(error)}"
            ) from error

        _LOGGER.debug(
            "Initialized server instance with address '%s'",
            self._address,
        )

    async def async_is_online(self) -> bool:
        """Check if the server is online, supporting both Java and Bedrock Edition servers."""
        try:
            await self.async_get_data()
        except PublicPoolServerConnectionError as error:
            _LOGGER.debug(
                "Connection check failed: %s",
                self._get_error_message(error),
            )
            return False

        return True

    async def async_get_data(self) -> ClientData:
        """Get updated data from the server, supporting both Java and Bedrock Edition servers."""

        # check if initialized
        if self._url is None or self._address is None:
            raise PoolNotInitializedError(
                f"Server instance with address '{self._address}' is not initialized"
            )

        url = f"{self._url}/api/client/{self._address}"
        _LOGGER.debug("Fetching workers from %s", url)

        try:
            async with ClientSession() as session, session.get(url) as response:
                if response.status == 200:
                    json = await response.json()
                    return ClientData(json["bestDifficulty"], json["workersCount"])

                raise PublicPoolServerAddressError(
                    f"Lookup of '{self._address}' failed: {response.status}"
                )
        except ClientError as err:
            raise PublicPoolServerConnectionError(
                f"Failed to fetch workers: {self._get_error_message(err)}"
            ) from err

    def _get_error_message(self, error: BaseException) -> str:
        """Get error message of an exception."""
        if not str(error):
            # Fallback to error type in case of an empty error message.
            return repr(error)

        return str(error)
