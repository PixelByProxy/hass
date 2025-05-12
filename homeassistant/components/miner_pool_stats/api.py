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
    worker_list: list[WorkerData]


class PublicPoolServerConnectionError(Exception):
    """Raised when no data can be fetched from the server."""


class PublicPoolServerNotInitializedError(Exception):
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
        await self.async_get_data()

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
            raise PublicPoolServerNotInitializedError(
                f"Server instance with address '{self._address}' is not initialized"
            )

        url = f"{self._url.rstrip('/')}/api/client/{self._address}"
        _LOGGER.debug("Fetching workers from %s", url)

        try:
            async with ClientSession() as session, session.get(url) as response:
                if response.status == 200:
                    json = await response.json()

                    # create a dictionary of workers by name
                    # if the worker exists, combine the data
                    workers: dict[str, WorkerData] = {}
                    for workerJson in json["workers"]:
                        worker = WorkerData(
                            name=workerJson["name"],
                            best_difficulty=float(workerJson["bestDifficulty"]),
                            hash_rate=self._calc_tera_hash(
                                float(workerJson["hashRate"])
                            ),
                            start_time=datetime.fromisoformat(workerJson["startTime"]),
                            last_seen=datetime.fromisoformat(workerJson["lastSeen"]),
                        )
                        if worker.name in workers:
                            workers[worker.name].hash_rate += worker.hash_rate
                            workers[worker.name].best_difficulty = max(
                                workers[worker.name].best_difficulty,
                                worker.best_difficulty,
                            )
                            workers[worker.name].last_seen = max(
                                workers[worker.name].last_seen, worker.last_seen
                            )
                            workers[worker.name].start_time = min(
                                workers[worker.name].start_time, worker.start_time
                            )
                        else:
                            workers[worker.name] = worker

                    # if there are no workers, log a warning
                    if not workers:
                        _LOGGER.warning(
                            "No workers found for address %s", self._address
                        )

                    try:
                        best_difficulty = float(json["bestDifficulty"])
                    except KeyError:
                        best_difficulty = 0.0

                    return ClientData(
                        best_difficulty,
                        int(json["workersCount"]),
                        list(workers.values()),
                    )

                raise PublicPoolServerConnectionError(
                    f"Lookup of '{self._address}' failed: Status code {response.status}"
                )
        except ClientError as error:
            raise PublicPoolServerConnectionError(
                f"Lookup of '{self._address}' failed: {self._get_error_message(error)}"
            ) from error

    def _get_error_message(self, error: BaseException) -> str:
        """Get error message of an exception."""
        if not str(error):
            # Fallback to error type in case of an empty error message.
            return repr(error)

        return str(error)

    def _calc_tera_hash(self, hash_rate: float) -> float:
        """Convert hash rate to TH/s."""
        if hash_rate <= 0:
            return 0
        return round(hash_rate / 1_000_000_000_000, 1)
