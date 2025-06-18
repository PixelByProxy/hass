"""Public Pool Client for the Miner Pool Stats integration."""

from datetime import datetime, timedelta
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from homeassistant.const import CONF_ADDRESS, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import as_utc, now

from .hash import HashRate, HashRateUnit
from .pool import (
    PoolAddressData,
    PoolAddressWorkerData,
    PoolClient,
    PoolConnectionError,
)

_LOGGER = logging.getLogger(__name__)

LOOKUP_TIMEOUT: float = 10
DATA_UPDATE_TIMEOUT: float = 10
DATA_UPDATE_RETRIES: int = 3


class PublicPoolClient(PoolClient):
    """Public Pool Client API."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialize the client instance."""
        super().__init__(hass, config_data)
        self._url = config_data[CONF_URL]
        self._address = config_data[CONF_ADDRESS]

    async def async_initialize(self) -> None:
        """Perform async initialization of client instance."""
        await self.async_get_data()

    async def async_is_online(self) -> bool:
        """Check if the server is online, supporting both Java and Bedrock Edition servers."""
        try:
            await self.async_get_data()
        except PoolConnectionError as error:
            _LOGGER.debug(
                "Connection check failed: %s",
                self._get_error_message(error),
            )
            return False

        return True

    async def async_get_data(self) -> PoolAddressData:
        """Get updated data from the pool."""

        url = f"{self._url.rstrip('/')}/api/client/{self._address}"
        _LOGGER.debug("Fetching workers from %s", url)

        try:
            async with ClientSession() as session, session.get(url) as response:
                if response.status == 200:
                    json = await response.json()

                    # create a dictionary of workers by name
                    # if the worker exists, combine the data
                    workers: dict[str, PoolAddressWorkerData] = {}
                    for workerJson in json["workers"]:
                        last_seen = datetime.fromisoformat(workerJson["lastSeen"])
                        current_time = as_utc(now())
                        is_online = current_time - last_seen < timedelta(minutes=30)

                        worker = PoolAddressWorkerData(
                            name=workerJson["name"],
                            best_difficulty=float(workerJson["bestDifficulty"]),
                            hash_rate=float(workerJson["hashRate"]),
                            is_online=is_online,
                        )

                        # get the maximum stored for the best difficulty
                        state_best_difficulty = await self._get_max_best_difficulty(
                            self._config_data, worker.name
                        )
                        worker.best_difficulty = self._get_max_float(
                            worker.best_difficulty, state_best_difficulty
                        )

                        if worker.name in workers:
                            workers[worker.name].hash_rate = self._combine_float_values(
                                workers[worker.name].hash_rate, worker.hash_rate
                            )
                            workers[worker.name].best_difficulty = self._get_max_float(
                                workers[worker.name].best_difficulty,
                                worker.best_difficulty,
                            )
                            workers[worker.name].is_online = (
                                workers[worker.name].is_online or worker.is_online
                            )
                        else:
                            workers[worker.name] = worker

                        # convert hash rate to TH/s
                        if workers[worker.name].hash_rate is not None:
                            hash_rate_float = workers[worker.name].hash_rate or 0.0
                            workers[worker.name].hash_rate = (
                                HashRate.from_number(hash_rate_float)
                                .to_unit(HashRateUnit.TH)
                                .value
                            )

                    # if there are no workers, log a warning
                    if not workers:
                        _LOGGER.warning(
                            "No workers found for address %s", self._address
                        )

                    try:
                        best_difficulty = float(json["bestDifficulty"])
                    except KeyError:
                        best_difficulty = 0.0

                    return PoolAddressData(
                        best_difficulty,
                        int(json["workersCount"]),
                        list(workers.values()),
                    )

                raise PoolConnectionError(
                    f"Lookup of '{self._address}' failed: Status code {response.status}"
                )
        except ClientError as error:
            raise PoolConnectionError(
                f"Lookup of '{self._address}' failed: {self._get_error_message(error)}"
            ) from error
