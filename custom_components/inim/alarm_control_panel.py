"""Support for INIM Alarm Control Panels."""

from collections.abc import Mapping
from functools import cached_property
import logging

# from aiohttp import ClientError
from pyinim.inim_cloud import InimCloud

# from config.inim_alarm.custom_components.inim.types import InimResult #TODO fix broken import
from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import CONF_DEVICE_ID, CONF_PANELS, CONF_SCENARIOS, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONST_MANUFACTURER = "Inim"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Alarm Control Panel."""
    # This gets the DataUpdateCoordinator from hass.data as specified in your __init__.py
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    inim_cloud_api = hass.data[DOMAIN][config_entry.entry_id].inim_cloud_api

    panels = config_entry.data[CONF_PANELS]
    device_id = config_entry.data[CONF_DEVICE_ID]

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    # await coordinator.async_config_entry_first_refresh()
    # devices: InimResult = coordinator.data
    _LOGGER.warning(
        "INIM alarm panel was created/updated for the following panels: %s", panels
    )
    alarm_control_panels = [
        InimAlarmControlPanelEntity(
            coordinator,
            inim_cloud_api,
            device_id,
            panel_conf,
            "0.0.1",
        )
        for panel_conf in panels
    ]

    # Create the alarm control panel
    async_add_entities(alarm_control_panels, update_before_add=True)


class InimAlarmControlPanelEntity(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of an Inim Alarm Control Panel."""

    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_VACATION
    )
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,  # TODO: provide proper Generic type ie: # coordinator: DataUpdateCoordinator[InimResult],
        inim: InimCloud,
        device_id: str,
        panel,  # TODO add type
        # scenarios: Mapping[str, int],
        # unique_id: str,
        version: str,
    ):
        """Initialize the alarm control panel."""

        super().__init__(coordinator)  # , context=zone.ZoneId)

        panel_name = panel["panel_name"]
        self._client = inim
        self._device_id = device_id
        self._scenarios = panel[CONF_SCENARIOS]
        self._attr_unique_id = panel["unique_id"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=panel_name,
            manufacturer=CONST_MANUFACTURER,
            model=panel_name,
            sw_version=version,
        )

    @cached_property
    def code_arm_required(self) -> bool:
        """Whether the code is required for arm actions."""
        # https://github.com/home-assistant/core/blob/dev/homeassistant/components/alarm_control_panel/__init__.py#L184C1-L188C1
        # https://github.com/home-assistant/core/issues/118668
        return False  # self._attr_code_arm_required

    @property
    def state(self) -> StateType:
        """Return the state of the entity."""
        try:
            scenario = self.coordinator.data.Data[self._device_id].ActiveScenario
            _LOGGER.info(f"INIM alarm panel was updated with scenario: {scenario}")  # noqa: G004

            if scenario == self._scenarios[STATE_ALARM_ARMED_AWAY]:
                return STATE_ALARM_ARMED_AWAY

            if scenario == self._scenarios[STATE_ALARM_DISARMED]:
                return STATE_ALARM_DISARMED

            if scenario == self._scenarios[STATE_ALARM_ARMED_NIGHT]:
                return STATE_ALARM_ARMED_NIGHT

            if scenario == self._scenarios[STATE_ALARM_ARMED_HOME]:
                return STATE_ALARM_ARMED_HOME

        except Exception:
            _LOGGER.exception(
                f"Error retrieving data from INIM services: {Exception}"  # noqa: G004
            )

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._async_arm(STATE_ALARM_DISARMED)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._async_arm(STATE_ALARM_ARMED_AWAY)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self._async_arm(STATE_ALARM_ARMED_HOME)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        await self._async_arm(STATE_ALARM_ARMED_NIGHT)

    async def _async_arm(self, state: str):
        await self._client.get_activate_scenario(
            self._device_id, self._scenarios[state]
        )
        _LOGGER.info(
            f"INIM alarm panel is going to be updated with: {state}/{self._scenarios[state]}"  # noqa: G004
        )
