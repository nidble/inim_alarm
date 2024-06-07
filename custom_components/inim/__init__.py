"""Nintendo Wishlist integration."""
import logging

from pyinim.inim_cloud import InimCloud
import voluptuous as vol

from homeassistant import core
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CLIENT_ID,
    CONF_DEVICE_ID,
    CONF_SCENARIOS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .types import InimResult

_LOGGER = logging.getLogger(__name__)
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

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(
            CONF_SCENARIOS, default=DEFAULT_SCENARIOS_SCHEMA
        ): SCENARIOS_SCHEMA,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            cv.time_period, cv.positive_timedelta
        ),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: PLATFORM_SCHEMA},
    # The full HA configurations gets passed to `async_setup` so we need to allow
    # extra keys.
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: core.HomeAssistant, config: ConfigType) -> bool:
    """Set up the platform.

    @NOTE: `config` is the full dict from `configuration.yaml`.

    :returns: A boolean to indicate that initialization was successful.
    """
    conf = config[DOMAIN]
    scan_interval = conf[CONF_SCAN_INTERVAL]
    device_id = conf[CONF_DEVICE_ID]

    inim = InimCloud(
        async_get_clientsession(hass),
        name="Inim",
        username=conf[CONF_USERNAME],
        password=conf[CONF_PASSWORD],
        client_id=conf[CONF_CLIENT_ID],
    )

    async def async_fetch_inim() -> InimResult:
        await inim.get_request_poll(device_id)
        _, _, res = await inim.get_devices_extended(device_id)
        return res

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name=DOMAIN,
        update_method=async_fetch_inim,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=scan_interval,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    hass.data[DOMAIN] = {
        "conf": conf,
        "coordinator": coordinator,
        "inim_cloud_api": inim,
    }

    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
    #     RING_API: ring,
    #     RING_DEVICES: ring.devices(),
    #     RING_DEVICES_COORDINATOR: devices_coordinator,
    #     RING_NOTIFICATIONS_COORDINATOR: notifications_coordinator,
    # }

    hass.async_create_task(
        async_load_platform(hass, "alarm_control_panel", DOMAIN, {}, conf)
    )
    hass.async_create_task(async_load_platform(hass, "binary_sensor", DOMAIN, {}, conf))

    return True


# class MyCoordinator(DataUpdateCoordinator):
#     """My custom coordinator."""

#     def __init__(self, hass, my_api):
#         """Initialize my coordinator."""
#         super().__init__(
#             hass,
#             _LOGGER,
#             # Name of the data. For logging purposes.
#             name="My sensor",
#             # Polling interval. Will only be polled if there are subscribers.
#             update_interval=timedelta(seconds=30),
#         )
#         self.my_api = my_api

#     async def _async_update_data(self):
#         """Fetch data from API endpoint.

#         This is the place to pre-process the data to lookup tables
#         so entities can quickly look up their data.
#         """
#         try:
#             # Note: asyncio.TimeoutError and aiohttp.ClientError are already
#             # handled by the data update coordinator.
#             async with async_timeout.timeout(10):
#                 # Grab active context variables to limit data required to be fetched from API
#                 # Note: using context is not required if there is no need or ability to limit
#                 # data retrieved from API.
#                 listening_idx = set(self.async_contexts())
#                 return await self.my_api.fetch_data(listening_idx)
#         except ApiAuthError as err:
#             # Raising ConfigEntryAuthFailed will cancel future updates
#             # and start a config flow with SOURCE_REAUTH (async_step_reauth)
#             raise ConfigEntryAuthFailed from err
#         except ApiError as err:
#             raise UpdateFailed(f"Error communicating with API: {err}")
