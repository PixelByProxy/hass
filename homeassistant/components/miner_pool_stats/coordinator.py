"""Coordinator for the Miner Pool Stats integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PoolAddressData, PublicPoolServer, PublicPoolServerConnectionError

type PoolConfigEntry = ConfigEntry[PoolCoordinator]

_LOGGER = logging.getLogger(__name__)

# Matches iotwatt data log interval
REQUEST_REFRESH_DEFAULT_COOLDOWN = 5


class PoolCoordinator(DataUpdateCoordinator[PoolAddressData]):
    """Coordinator for Pool."""

    _api: PublicPoolServer

    def __init__(self, hass: HomeAssistant, entry: PoolConfigEntry) -> None:
        """Initialize PoolCoordinator object."""
        self._data = None
        self._hass = hass
        self._entry = entry
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=30),
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=REQUEST_REFRESH_DEFAULT_COOLDOWN,
                immediate=True,
            ),
        )

    async def _async_setup(self) -> None:
        """Set up the Pool coordinator."""

        url = self._entry.data[CONF_URL]
        address = self._entry.data[CONF_ADDRESS]

        # create API instance
        self._api = PublicPoolServer(self._hass, url, address)

        # validate the connection
        try:
            return await self._api.async_initialize()
        except PublicPoolServerConnectionError as error:
            raise ConfigEntryNotReady(f"Unable to load pool data: {error}") from error

    async def _async_update_data(self) -> PoolAddressData:
        """Get updated data from the server."""
        try:
            return await self._api.async_get_data()
        except PublicPoolServerConnectionError as error:
            raise UpdateFailed(error) from error
