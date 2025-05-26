"""Base entity for the Miner Pool Stats integration."""

from homeassistant.const import CONF_ADDRESS, CONF_FRIENDLY_NAME
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, WALLET_ADDRESS, WORKER
from .coordinator import PoolConfigEntry, PoolCoordinator


class PoolAddressDeviceEntity(CoordinatorEntity[PoolCoordinator]):
    """Representation of a Pool Address base entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolCoordinator,
        config_entry: PoolConfigEntry,
    ) -> None:
        """Initialize base entity."""
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer=config_entry.data[CONF_FRIENDLY_NAME],
            model=WALLET_ADDRESS,
            name=config_entry.data[CONF_ADDRESS],
        )


class PoolAddressWorkerDeviceEntity(CoordinatorEntity[PoolCoordinator]):
    """Representation of a Pool Address Worker base entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PoolCoordinator,
        config_entry: PoolConfigEntry,
        worker_name: str,
    ) -> None:
        """Initialize base entity."""
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}-{worker_name}")},
            manufacturer=config_entry.data[CONF_FRIENDLY_NAME],
            model=WORKER,
            name=worker_name,
        )
