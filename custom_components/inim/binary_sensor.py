import logging

from homeassistant import core
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import slugify

from .const import CONF_DEVICE_ID, DOMAIN
from .types import Device, InimResult, Zone

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: core.HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Setups the sensor platform."""

    coordinator = hass.data[DOMAIN]["coordinator"]
    conf = hass.data[DOMAIN]["conf"]

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #

    await coordinator.async_config_entry_first_refresh()
    device_id = conf[CONF_DEVICE_ID]
    res: Device = coordinator.data.Data[device_id]

    async_add_entities(
        InimBinarySensorEntity(coordinator, zone, device_id) for zone in res.Zones
    )


# _InimCoordinatorT = TypeVar(
#     "_InimCoordinatorT",
#     bound=(RingDataCoordinator),
# )
# class InimBinarySensorEntity(CoordinatorEntity[_InimCoordinatorT], BinarySensorEntity):


class InimBinarySensorEntity(CoordinatorEntity, BinarySensorEntity):
    """Represents a Query for a switch game."""

    def __init__(  # noqa: D107
        self,
        coordinator: DataUpdateCoordinator[InimResult],
        zone: Zone,
        device_id: str,
    ):
        super().__init__(coordinator, context=zone.ZoneId)

        self._zone = zone
        self._device_id = device_id
        self.attrs = {}
        self._attr_extra_state_attributes = {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, zone.ZoneId)},
            manufacturer="Inim",
            model=Zone.Type,
            name=Zone.Name,
        )
        self._attr_unique_id = self.get_unique_id()

    # @property
    # def unit_of_measurement(self):
    #     """Return the unit of measurement of this entity, if any."""
    #     return "on sale"

    # @property
    # def icon(self):
    #     """Icon to use in the frontend."""
    #     return "mdi:nintendo-switch"

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        zones: list[Zone] = self.coordinator.data.Data[self._device_id].Zones
        for zone in zones:
            if zone.ZoneId == self._zone.ZoneId:
                return zone.Status == 2
        return False

    # @property
    # def entity_id(self) -> str:
    def get_unique_id(self) -> str:
        """Retrieve the sensor unique id."""
        slug = slugify(self._zone.Name)
        return f"binary_sensor.inim_{slug}_{self._zone.ZoneId}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._zone.Name

    # @property
    # def extra_state_attributes(self):
    #     return {"matches": self.matches}

    # tasmota
    # @core.callback
    # def on_off_state_updated(self, state: bool, **kwargs: Any) -> None:
    #     """Handle state updates."""
    #     self._on_off_state = state

    #     if self._delay_listener is not None:
    #         self._delay_listener()
    #         self._delay_listener = None

    #     off_delay = self._tasmota_entity.off_delay
    #     if self._on_off_state and off_delay is not None:
    #         self._delay_listener = evt.async_call_later(
    #             self.hass, off_delay, self.off_delay_listener
    #         )

    #     self.async_write_ha_state()
