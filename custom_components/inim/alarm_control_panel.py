"""Support for INIM Alarm Control Panels."""

# see homeassistant/components/agent_dvr/alarm_control_panel.py

from __future__ import annotations
import logging
from typing import Callable, Optional, Mapping
from datetime import timedelta
from aiohttp import ClientError

import voluptuous as vol

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntityFeature,
    PLATFORM_SCHEMA
)
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
)
# from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
# from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from pyinim_nidble.inim_cloud import InimCloud
from .const import DOMAIN, CONF_CLIENT_ID, CONF_DEVICE_ID, CONF_SCENARIOS

_LOGGER = logging.getLogger(__name__)
# time between update data from API
SCAN_INTERVAL = timedelta(minutes=2)

CONST_ALARM_CONTROL_PANEL_NAME = "Alarm Panel"

SCENARIOS_SCHEMA = vol.Schema(
    {
        # vol.Optional(STATE_ALARM_ARMED_AWAY, default=0): cv.positive_int,
        vol.Optional(STATE_ALARM_ARMED_AWAY): cv.positive_int,
        vol.Optional(STATE_ALARM_DISARMED): cv.positive_int,
        vol.Optional(STATE_ALARM_ARMED_NIGHT): cv.positive_int,
        vol.Optional(STATE_ALARM_ARMED_HOME): cv.positive_int,
    }
)

DEFAULT_SCENARIOS_SCHEMA = {
    STATE_ALARM_ARMED_AWAY: 0,
    STATE_ALARM_DISARMED: 1,
    STATE_ALARM_ARMED_NIGHT: 2,
    STATE_ALARM_ARMED_HOME: 3,
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_SCENARIOS, default=DEFAULT_SCENARIOS_SCHEMA): SCENARIOS_SCHEMA,
    }
)

# async def async_setup_platform(
def setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    inim = InimCloud(
        async_get_clientsession(hass),
        name='Inim',
        username=config[CONF_USERNAME],
        password=config[CONF_PASSWORD],
        client_id=config[CONF_CLIENT_ID]
    )
    alarm_control_panels = [
        InimAlarmControlPanel(
            inim,
            config[CONF_DEVICE_ID],
            config[CONF_SCENARIOS],
            'alarm_control_panel',
            '0.0.1'
        )
    ]
    async_add_entities(alarm_control_panels, update_before_add=True)

class InimAlarmControlPanel(Entity):
    """Representation of an Inim Alarm Control Panel."""

    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_HOME
    )
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, inim: InimCloud, device_id: str, scenarios: Mapping[str, int], unique_id: str, version: str):
        """Initialize the alarm control panel."""
        self._client = inim
        self._device_id = device_id
        self._scenarios = scenarios

        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=f"{self._client.name} {CONST_ALARM_CONTROL_PANEL_NAME}",
            manufacturer="Inim",
            model=CONST_ALARM_CONTROL_PANEL_NAME,
            sw_version=version,
        )

    async def async_update(self) -> None:
        """Update the state of the device."""
        try:
            await self._client.get_request_poll(self._device_id)
            _, _, resp = await self._client.get_devices_extended(self._device_id)
            scenario = resp.Data[self._device_id].ActiveScenario
            self._attr_available = True
            _LOGGER.info(f"INIM alarm panel got updated with scenario: {scenario}")

            if scenario == self._scenarios[STATE_ALARM_ARMED_AWAY]:
                self._attr_state = STATE_ALARM_ARMED_AWAY
                return
            if scenario == self._scenarios[STATE_ALARM_DISARMED]:
                self._attr_state = STATE_ALARM_DISARMED
                return
            if scenario == self._scenarios[STATE_ALARM_ARMED_NIGHT]:
                self._attr_state = STATE_ALARM_ARMED_NIGHT
                return
            if scenario == self._scenarios[STATE_ALARM_ARMED_HOME]:
                self._attr_state = STATE_ALARM_ARMED_HOME

        except (ClientError):
            self._attr_available = False
            _LOGGER.exception(f"Error retrieving data from INIM services: {ClientError}")

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._client.get_activate_scenario(self._device_id, self._scenarios[STATE_ALARM_DISARMED])
        self._attr_state = STATE_ALARM_DISARMED
        # self.state = STATE_ALARM_DISARMED
        # self.async_write_ha_state()
        # await self.async_update_ha_state()
        await self.async_device_update()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command. Uses custom mode."""
        await self._client.get_activate_scenario(self._device_id, self._scenarios[STATE_ALARM_ARMED_AWAY])
        self._attr_state = STATE_ALARM_ARMED_AWAY
        await self.async_device_update()


    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command. Uses custom mode."""
        await self._client.get_activate_scenario(self._device_id, self._scenarios[STATE_ALARM_ARMED_HOME])
        self._attr_state = STATE_ALARM_ARMED_HOME
        await self.async_device_update()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command. Uses custom mode."""
        await self._client.get_activate_scenario(self._device_id, self._scenarios[STATE_ALARM_ARMED_NIGHT])
        self._attr_state = STATE_ALARM_ARMED_NIGHT
        await self.async_device_update()
