"""The Pool Server sensor platform."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import CONF_UNIQUE_ID, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .api import PoolAddressData, PoolAddressWorkerData
from .const import (
    KEY_BEST_DIFFICULTY,
    KEY_HASH_RATE,
    KEY_WORKER_COUNT,
    UNIT_DIFFICULTY,
    UNIT_HASH_RATE,
    UNIT_WORKER_COUNT,
)
from .coordinator import PoolConfigEntry, PoolCoordinator
from .entity import PoolAddressDeviceEntity, PoolAddressWorkerDeviceEntity

# Coordinator is used to centralize the data updates.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PoolAddressSensorEntityDescription(SensorEntityDescription):
    """Class describing Pool Address sensor entities."""

    value_fn: Callable[[PoolAddressData], StateType]


@dataclass(frozen=True, kw_only=True)
class PoolAddressWorkerEntityDescription(SensorEntityDescription):
    """Class describing Pool Address Worker sensor entities."""

    value_fn: Callable[[PoolAddressWorkerData], StateType]


ADDRESS_SENSOR_DESCRIPTIONS = [
    PoolAddressSensorEntityDescription(
        key=KEY_WORKER_COUNT,
        translation_key=KEY_WORKER_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_WORKER_COUNT,
        value_fn=lambda data: data.worker_count,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PoolAddressSensorEntityDescription(
        key=KEY_BEST_DIFFICULTY,
        translation_key=KEY_BEST_DIFFICULTY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_DIFFICULTY,
        value_fn=lambda data: data.best_difficulty,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]

WORKER_SENSOR_DESCRIPTIONS = [
    PoolAddressWorkerEntityDescription(
        key=KEY_BEST_DIFFICULTY,
        translation_key=KEY_BEST_DIFFICULTY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_DIFFICULTY,
        value_fn=lambda worker: worker.best_difficulty,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PoolAddressWorkerEntityDescription(
        key=KEY_HASH_RATE,
        translation_key=KEY_HASH_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_HASH_RATE,
        value_fn=lambda worker: worker.hash_rate,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: PoolConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Miner Pool sensor platform."""
    coordinator = config_entry.runtime_data

    sensors: list[SensorEntity] = []

    sensors.extend(
        [
            PoolAddressSensorEntity(coordinator, description, config_entry)
            for description in ADDRESS_SENSOR_DESCRIPTIONS
        ]
    )

    sensors.extend(
        [
            PoolAddressWorkerSensorEntity(
                coordinator, description, config_entry, worker
            )
            for worker in coordinator.data.worker_list
            for description in WORKER_SENSOR_DESCRIPTIONS
        ]
    )

    async_add_entities(sensors)


class PoolAddressSensorEntity(PoolAddressDeviceEntity, SensorEntity):
    """Representation of a Pool Address sensor."""

    entity_description: PoolAddressSensorEntityDescription

    def __init__(
        self,
        coordinator: PoolCoordinator,
        description: PoolAddressSensorEntityDescription,
        config_entry: PoolConfigEntry,
    ) -> None:
        """Initialize the Pool Address sensor."""
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}"
        self._attr_translation_key = description.translation_key
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{config_entry.data[CONF_UNIQUE_ID]}_{description.key}"
        )
        self._update_properties()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_properties()
        self.async_write_ha_state()

    @callback
    def _update_properties(self) -> None:
        """Update sensor properties."""
        self._attr_native_value = self.entity_description.value_fn(
            self.coordinator.data
        )


class PoolAddressWorkerSensorEntity(PoolAddressWorkerDeviceEntity, SensorEntity):
    """Representation of a Pool Address Worker sensor."""

    entity_description: PoolAddressWorkerEntityDescription

    def __init__(
        self,
        coordinator: PoolCoordinator,
        description: PoolAddressWorkerEntityDescription,
        config_entry: PoolConfigEntry,
        worker: PoolAddressWorkerData,
    ) -> None:
        """Initialize the Pool Address Worker sensor."""
        super().__init__(coordinator, config_entry, worker.name)
        self.entity_description = description
        self.worker = worker
        self._attr_unique_id = (
            f"{config_entry.entry_id}-{worker.name}-{description.key}"
        )
        self._attr_translation_key = description.translation_key
        self.entity_id = f"{SENSOR_DOMAIN}.{config_entry.data[CONF_UNIQUE_ID]}_{worker.name}_{description.key}"
        self._update_properties()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_properties()
        self.async_write_ha_state()

    @callback
    def _update_properties(self) -> None:
        """Update sensor properties."""
        self._attr_native_value = self.entity_description.value_fn(self.worker)
