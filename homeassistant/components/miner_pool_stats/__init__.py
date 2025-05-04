"""The Miner Pool Stats integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import PoolConfigEntry, PoolCoordinator

# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: PoolConfigEntry) -> bool:
    """Set up Miner Pool Stats from a config entry."""

    # Create coordinator instance and store it.
    coordinator = PoolCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PoolConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
