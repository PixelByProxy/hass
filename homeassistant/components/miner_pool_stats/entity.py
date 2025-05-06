"""Base entity for the Minecraft Server integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolConfigEntry, PoolCoordinator

MANUFACTURER = "Public Pool"


class ClientEntity(CoordinatorEntity[PoolCoordinator]):
    """Representation of a Minecraft Server base entity."""

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
            manufacturer=MANUFACTURER,
            model=MANUFACTURER,
            name=coordinator.name,
        )


class PoolAddressWorkerDeviceEntity(CoordinatorEntity[PoolCoordinator]):
    """Representation of a Minecraft Server base entity."""

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
            manufacturer=MANUFACTURER,
            model=MANUFACTURER,
            name=worker_name,
        )
