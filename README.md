# Inim Alarm for Home Assistant

Custom Component/Integration for controlling Inim alarm through [Home Assistant](https://www.home-assistant.io/)

## Installation

### HACS

TODO

### Manual Installation

You can manually install as a custom component on your Home Assistant installation.

Follow these steps:

* In Home Assistant's config directory, you need to create a `custom_components` and copy all the content of the `custom_components/inim` folder.

* Open your `config/configuration.yaml` file and be sure to add - at the least - the following lines:
    ```yaml
    inim:
    password: !secret inim_alarm_password
    username: !secret inim_alarm_username
    client_id: "123456"
    device_id: "789012"
    ```
    for further detail look at `config/configuration.yam` present in this repository.

* Restart Home Assistant

## Configuration

TODO

# Disclaimer

This project has no relation with the Inim company.

This integration is using python module PyInim which is an unofficial module for achieving interoperability with Inim APIs.

Author is in no way affiliated with Inim.

All the api requests used within the pyinim library are available and published on the internet (examples linked above) and the pyinim module is purely just a wrapper around those https requests.

Author does not guarantee functionality of this integration and is not responsible for any damage.

All product names, trademarks and registered trademarks in this repository, are property of their respective owners.