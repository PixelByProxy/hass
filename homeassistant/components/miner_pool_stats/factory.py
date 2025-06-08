"""Factory for creating PoolClient instances based on the pool source."""

from typing import Any

from homeassistant.const import CONF_SOURCE
from homeassistant.core import HomeAssistant

from .const import (
    POOL_SOURCE_F2_POOL_KEY,
    POOL_SOURCE_PUBLIC_POOL_KEY,
    POOL_SOURCE_SOLO_POOL_KEY,
)
from .pool import PoolClient
from .pool_f2 import F2PoolClient
from .pool_public import PublicPoolClient
from .pool_solo import SoloPoolClient


class PoolFactory:
    """Factory for creating PoolClient instances."""

    @staticmethod
    def get(hass: HomeAssistant, config_data: dict[str, Any]) -> PoolClient:
        """Get a PoolClient instance based on the pool source."""

        source = config_data[CONF_SOURCE]

        if source == POOL_SOURCE_PUBLIC_POOL_KEY:
            return PublicPoolClient(hass, config_data)
        if source == POOL_SOURCE_F2_POOL_KEY:
            return F2PoolClient(hass, config_data)
        if source == POOL_SOURCE_SOLO_POOL_KEY:
            return SoloPoolClient(hass, config_data)

        raise ValueError(f"Unsupported pool source: {source}")
