"""API for the Miner Pool Stats integration."""

from abc import abstractmethod
from dataclasses import dataclass
from functools import partial
from typing import Any

from homeassistant.components.recorder import get_instance, history
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_FRIENDLY_NAME,
    CONF_TYPE,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant

from .const import KEY_BEST_DIFFICULTY, CryptoCoin


class PoolConnectionError(Exception):
    """Raised when data can not be fetched from the server."""


@dataclass
class PoolInitData:
    """Representation of Pool initialization data."""

    pool_name: str
    coin_name: str
    address: str


@dataclass
class PoolAddressWorkerData:
    """Representation of Pool address worker data."""

    name: str
    best_difficulty: float | None
    hash_rate: float | None
    is_online: bool


@dataclass
class PoolAddressData:
    """Representation of Pool address data."""

    total_paid: float | None
    current_balance: float | None
    best_difficulty: float | None
    worker_count: int
    worker_list: list[PoolAddressWorkerData]


class PoolClient:
    """Client for interacting with the pool."""

    def __init__(self, hass: HomeAssistant, config_data: dict[str, Any]) -> None:
        """Initialize the client instance."""
        self._hass = hass
        self._config_data = config_data

    async def async_initialize(self) -> PoolInitData:
        """Perform async initialization of client instance."""
        await self.async_get_data()
        return PoolInitData(
            self._config_data[CONF_FRIENDLY_NAME],
            CryptoCoin(self._config_data[CONF_TYPE]).name,
            self._config_data[CONF_ADDRESS],
        )

    @abstractmethod
    async def async_get_data(self) -> PoolAddressData:
        """Fetch data from the pool."""

    async def _get_max_best_difficulty(
        self, config_data: dict[str, Any], worker_name: str
    ) -> float:
        """Get the maximum value for the difficulty sensor."""

        entity_id = f"{SENSOR_DOMAIN}.{config_data[CONF_UNIQUE_ID]}_{worker_name}_{KEY_BEST_DIFFICULTY}"

        val = await get_instance(self._hass).async_add_executor_job(
            partial(
                history.get_last_state_changes,
                self._hass,
                1,
                entity_id=entity_id,
            )
        )

        if val is not None:
            states = val.get(entity_id)
            if states is not None and len(states) > 0:
                for state in states:
                    if state.state is not None and self.is_float(state.state):
                        return float(state.state)

        return 0.0

    def _get_max_float(
        self, value1: float | None, value2: float | None
    ) -> float | None:
        """Get the maximum of two float values."""
        if value1 is None and value2 is None:
            return None
        if value1 is None:
            return value2
        if value2 is None:
            return value1
        return max(value1, value2)

    def _combine_float_values(
        self, value1: float | None, value2: float | None
    ) -> float | None:
        """Combine two float values."""
        if value1 is None and value2 is None:
            return None
        if value1 is None:
            return value2
        if value2 is None:
            return value1
        return value1 + value2

    def is_float(self, string_value: str) -> bool:
        """Check if a string can be converted to a float."""
        try:
            float(string_value)
        except ValueError:
            return False
        else:
            return True

    def _get_error_message(self, error: BaseException) -> str:
        """Get error message of an exception."""
        if not str(error):
            # Fallback to error type in case of an empty error message.
            return repr(error)

        return str(error)
