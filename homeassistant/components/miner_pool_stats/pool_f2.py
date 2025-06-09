"""f2Pool Client for the Miner Pool Stats integration."""

from datetime import datetime, timedelta
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from homeassistant.const import CONF_ADDRESS, CONF_API_KEY, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import as_utc, now

from .const import CryptoCoin
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

POOL_COIN_URI_PATHS = {
    CryptoCoin.BTC: "bitcoin",
    CryptoCoin.BCH: "bitcoin-cash",
    CryptoCoin.ALEO: "aleo",
    CryptoCoin.BELLS: "bells-mm",
    CryptoCoin.CFX: "conflux",
    CryptoCoin.CKB: "nervos",
    CryptoCoin.DASH: "dash",
    CryptoCoin.ELA: "elacoin",
    CryptoCoin.ETC: "ethereum-classic",
    CryptoCoin.EHHW: "ethw",
    CryptoCoin.FB: "fractal-bitcoin",
    CryptoCoin.IRON: "iron-fish",
    CryptoCoin.HTR: "hathor",
    CryptoCoin.JKC: "junkcoin",
    CryptoCoin.KDA: "kadena",
    CryptoCoin.KAS: "kaspa",
    CryptoCoin.LTC: "litecoin",
    CryptoCoin.LKY: "luckycoin",
    CryptoCoin.NEXA: "nexa",
    CryptoCoin.NMC: "nmccoin",
    CryptoCoin.PEP: "pepecoin",
    CryptoCoin.ZEC: "zcash",
    CryptoCoin.ZEN: "zen",
}


class F2PoolClient(PoolClient):
    """Public Pool Client API."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialize the client instance."""
        super().__init__(hass, config_data)
        self._address = config_data[CONF_ADDRESS]
        self._coin_type = config_data[CONF_TYPE]
        self._api_key = config_data[CONF_API_KEY]

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

        coin_path = POOL_COIN_URI_PATHS[self._coin_type]
        url = f"https://api.f2pool.com/{coin_path}/{self._address}"
        _LOGGER.debug("Fetching workers from %s", url)

        headers = {"F2P-API-SECRET": self._api_key, "Content-Type": "application/json"}

        try:
            async with (
                ClientSession() as session,
                session.get(url, headers=headers) as response,
            ):
                if response.status == 200:
                    json = await response.json()

                    # create a dictionary of workers by name
                    # if the worker exists, combine the data
                    workers: dict[str, PoolAddressWorkerData] = {}
                    for worker_arr in json["workers"]:
                        last_seen = datetime.fromisoformat(worker_arr[6])
                        current_time = as_utc(now())
                        is_online = current_time - last_seen < timedelta(minutes=30)

                        worker = PoolAddressWorkerData(
                            name=worker_arr[0],
                            best_difficulty=0.0,
                            hash_rate=float(worker_arr[1]),
                            is_online=is_online,
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
                        int(json["worker_length"]),
                        list(workers.values()),
                    )

                raise PoolConnectionError(
                    f"Lookup of '{self._address}' failed: Status code {response.status}"
                )
        except ClientError as error:
            raise PoolConnectionError(
                f"Lookup of '{self._address}' failed: {self._get_error_message(error)}"
            ) from error
