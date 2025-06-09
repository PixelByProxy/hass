"""Sool Pool Client for the Miner Pool Stats integration."""

import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from homeassistant.const import CONF_ADDRESS, CONF_TYPE
from homeassistant.core import HomeAssistant

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


class SoloPoolClient(PoolClient):
    """Public Pool Client API."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialize the client instance."""
        super().__init__(hass, config_data)
        self._address = config_data[CONF_ADDRESS]
        self._coin_type = config_data[CONF_TYPE]

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

        url = f"https://{self._coin_type}.solopool.org/api/accounts/{self._address}"
        _LOGGER.debug("Fetching workers from %s", url)

        try:
            async with ClientSession() as session, session.get(url) as response:
                if response.status == 200:
                    json = await response.json()

                    # create a dictionary of workers by name
                    # if the worker exists, combine the data
                    workers: dict[str, PoolAddressWorkerData] = {}
                    for worker_name in json["workers"]:
                        worker = PoolAddressWorkerData(
                            name=worker_name,
                            best_difficulty=0.0,
                            hash_rate=float(json["workers"][worker_name]["hr"]),
                            is_online=not bool(json["workers"][worker_name]["offline"]),
                        )

                        if worker.name in workers:
                            workers[worker.name].hash_rate += worker.hash_rate
                            workers[worker.name].is_online = (
                                workers[worker.name].is_online or worker.is_online
                            )
                        else:
                            workers[worker.name] = worker

                        # convert hash rate to TH/s
                        workers[worker.name].hash_rate = (
                            HashRate.from_number(workers[worker.name].hash_rate)
                            .to_unit(HashRateUnit.TH)
                            .value
                        )

                    # if there are no workers, log a warning
                    if not workers:
                        _LOGGER.warning(
                            "No workers found for address %s", self._address
                        )

                    return PoolAddressData(
                        0.0,
                        int(json["workersTotal"]),
                        list(workers.values()),
                    )

                raise PoolConnectionError(
                    f"Lookup of '{self._address}' failed: Status code {response.status}"
                )
        except ClientError as error:
            raise PoolConnectionError(
                f"Lookup of '{self._address}' failed: {self._get_error_message(error)}"
            ) from error
