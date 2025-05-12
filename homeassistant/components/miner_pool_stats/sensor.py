"""The Minecraft Server sensor platform."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .api import ClientData, WorkerData
from .coordinator import PoolConfigEntry, PoolCoordinator
from .entity import ClientEntity, PoolAddressWorkerDeviceEntity

KEY_WORKER_COUNT = "worker_count"
KEY_BEST_DIFFICULTY = "best_difficulty"
KEY_HASH_RATE = "hash_rate"
KEY_START_TIME = "start_time"
KEY_LAST_SEEN = "last_seen"

UNIT_WORKER_COUNT = "workers"
UNIT_HASH_RATE = "TH/s"
UNIT_DIFFICULTY = "difficulty"

# Coordinator is used to centralize the data updates.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PoolSensorEntityDescription(SensorEntityDescription):
    """Class describing Minecraft Server sensor entities."""

    value_fn: Callable[[ClientData], StateType]
    attributes_fn: Callable[[ClientData], dict[str, Any]] | None


@dataclass(frozen=True, kw_only=True)
class PoolAddressWorkerEntityDescription(SensorEntityDescription):
    """Class describing Minecraft Server sensor entities."""

    value_fn: Callable[[WorkerData], StateType]


SENSOR_DESCRIPTIONS = [
    PoolSensorEntityDescription(
        key=KEY_WORKER_COUNT,
        translation_key=KEY_WORKER_COUNT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_WORKER_COUNT,
        value_fn=lambda data: data.worker_count,
        attributes_fn=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PoolSensorEntityDescription(
        key=KEY_BEST_DIFFICULTY,
        translation_key=KEY_BEST_DIFFICULTY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UNIT_DIFFICULTY,
        value_fn=lambda data: data.best_difficulty,
        attributes_fn=None,
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
    """Set up the Minecraft Server sensor platform."""
    coordinator = config_entry.runtime_data

    sensors: list[SensorEntity] = []

    sensors.extend(
        [
            PoolClientSensorEntity(coordinator, description, config_entry)
            for description in SENSOR_DESCRIPTIONS
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


class PoolClientSensorEntity(ClientEntity, SensorEntity):
    """Representation of a Minecraft Server sensor base entity."""

    _attr_has_entity_name = True
    entity_description: PoolSensorEntityDescription

    def __init__(
        self,
        coordinator: PoolCoordinator,
        description: PoolSensorEntityDescription,
        config_entry: PoolConfigEntry,
    ) -> None:
        """Initialize sensor base entity."""
        super().__init__(coordinator, config_entry)
        self.entity_description = description
        self._attr_unique_id = f"{config_entry.entry_id}-{description.key}"
        self._attr_translation_key = description.translation_key
        self.entity_id = f"{SENSOR_DOMAIN}.{config_entry.title}_{description.key}"
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

        if func := self.entity_description.attributes_fn:
            self._attr_extra_state_attributes = func(self.coordinator.data)


class PoolAddressWorkerSensorEntity(PoolAddressWorkerDeviceEntity, SensorEntity):
    """Representation of a Minecraft Server sensor base entity."""

    _attr_has_entity_name = True
    entity_description: PoolAddressWorkerEntityDescription

    def __init__(
        self,
        coordinator: PoolCoordinator,
        description: PoolAddressWorkerEntityDescription,
        config_entry: PoolConfigEntry,
        worker: WorkerData,
    ) -> None:
        """Initialize sensor base entity."""
        super().__init__(coordinator, config_entry, worker.name)
        self.entity_description = description
        self.worker = worker
        self._attr_unique_id = (
            f"{config_entry.entry_id}-{worker.name}-{description.key}"
        )
        self._attr_translation_key = description.translation_key
        self.entity_id = (
            f"{SENSOR_DOMAIN}.{config_entry.title}_{worker.name}_{description.key}"
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
        self._attr_native_value = self.entity_description.value_fn(self.worker)
