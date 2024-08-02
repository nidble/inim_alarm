"""Nintendo Wishlist integration."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import logging

from pyinim.inim_cloud import InimCloud

# import voluptuous as vol
from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

# import homeassistant.helpers.config_validation as cv
# from homeassistant.helpers.discovery import async_load_platform
# from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_CLIENT_ID, CONF_DEVICE_ID, DOMAIN
from .types import InimResult

_LOGGER = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# A list of the different platforms we wish to setup.
# Add or remove from this list based on your specific need
# of entity platform types.
# ----------------------------------------------------------------------------
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.ALARM_CONTROL_PANEL,
]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: DataUpdateCoordinator
    inim_cloud_api: InimCloud
    cancel_update_listener: Callable


async def async_setup_entry(
    hass: core.HomeAssistant, config_entry: ConfigEntry
) -> bool:
    """Set up Example Integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # ----------------------------------------------------------------------------
    # Initialise the coordinator that manages data updates from your api.
    # This is defined in coordinator.py
    # ----------------------------------------------------------------------------
    # coordinator = ExampleCoordinator(hass, config_entry)
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]
    client_id = config_entry.data[CONF_CLIENT_ID]
    device_id = config_entry.data[CONF_DEVICE_ID]
    scan_interval = timedelta(seconds=config_entry.data[CONF_SCAN_INTERVAL])

    inim_cloud_api = InimCloud(
        async_get_clientsession(hass),
        name="Inim",
        username=username,
        password=password,
        client_id=client_id,
    )

    async def async_fetch_inim() -> InimResult:
        await inim_cloud_api.get_request_poll(device_id)
        _, _, res = await inim_cloud_api.get_devices_extended(device_id)
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

    # ----------------------------------------------------------------------------
    # Perform an initial data load from api.
    # async_config_entry_first_refresh() is special in that it does not log errors
    # if it fails.
    # ----------------------------------------------------------------------------
    await coordinator.async_config_entry_first_refresh()
    # or
    # await coordinator.async_refresh()

    # ----------------------------------------------------------------------------
    # Test to see if api initialised correctly, else raise ConfigNotReady to make
    # HA retry setup.
    # Change this to match how your api will know if connected or successful
    # update.
    # ----------------------------------------------------------------------------
    if not coordinator.data:
        raise ConfigEntryNotReady

    # ----------------------------------------------------------------------------
    # Initialise a listener for config flow options changes.
    # This will be removed automatically if the integraiton is unloaded.
    # See config_flow for defining an options setting that shows up as configure
    # on the integration.
    # If you do not want any config flow options, no need to have listener.
    # ----------------------------------------------------------------------------
    cancel_update_listener = config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    # ----------------------------------------------------------------------------
    # Add the coordinator and update listener to hass data to make
    # accessible throughout your integration
    # Note: this will change on HA2024.6 to save on the config entry.
    # ----------------------------------------------------------------------------
    # hass.data[DOMAIN][config_entry.entry_id] = RuntimeData(
    #     coordinator, cancel_update_listener
    # )
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = RuntimeData(
        coordinator, inim_cloud_api, cancel_update_listener
    )

    # ----------------------------------------------------------------------------
    # Setup platforms (based on the list of entity types in PLATFORMS defined above)
    # This calls the async_setup method in each of your entity type files.
    # ----------------------------------------------------------------------------
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    # ----------------------------------------------------------------------------
    # Setup global services
    # This can be done here but included in a seperate file for ease of reading.
    # See also switch.py for entity services examples
    # ----------------------------------------------------------------------------
    # TODO: ExampleServicesSetup(hass, config_entry)

    # Return true to denote a successful setup.
    return True


# async def deprecated_async_setup(hass: core.HomeAssistant, config: ConfigType) -> bool:
#     """Set up the platform.

#     @NOTE: `config` is the full dict from `configuration.yaml`.

#     :returns: A boolean to indicate that initialization was successful.
#     """
#     conf = config[DOMAIN]
#     scan_interval = conf[CONF_SCAN_INTERVAL]
#     device_id = conf[CONF_DEVICE_ID]

#     inim = InimCloud(
#         async_get_clientsession(hass),
#         name="Inim",
#         username=conf[CONF_USERNAME],
#         password=conf[CONF_PASSWORD],
#         client_id=conf[CONF_CLIENT_ID],
#     )

#     async def async_fetch_inim() -> InimResult:
#         await inim.get_request_poll(device_id)
#         _, _, res = await inim.get_devices_extended(device_id)
#         return res

#     coordinator = DataUpdateCoordinator(
#         hass,
#         _LOGGER,
#         # Name of the data. For logging purposes.
#         name=DOMAIN,
#         update_method=async_fetch_inim,
#         # Polling interval. Will only be polled if there are subscribers.
#         update_interval=scan_interval,
#     )

#     # Fetch initial data so we have data when entities subscribe
#     await coordinator.async_refresh()

#     hass.data[DOMAIN] = {
#         "conf": conf,
#         "coordinator": coordinator,
#         "inim_cloud_api": inim,
#     }

#     # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
#     #     INIM_API: inim,
#     #     INIM_DEVICES: inim.devices(),
#     #     INIM_DEVICES_COORDINATOR: devices_coordinator,
#     #     INIM_NOTIFICATIONS_COORDINATOR: notifications_coordinator,
#     # }

#     hass.async_create_task(
#         async_load_platform(hass, "alarm_control_panel", DOMAIN, {}, conf)
#     )
#     hass.async_create_task(async_load_platform(hass, "binary_sensor", DOMAIN, {}, conf))

#     return True


async def _async_update_listener(hass: core.HomeAssistant, config_entry: ConfigEntry):
    """Handle config options update.

    Reload the integration when the options change.
    Called from our listener created above.
    """
    await hass.config_entries.async_reload(config_entry.entry_id)


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
