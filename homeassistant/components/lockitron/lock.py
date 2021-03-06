"""Lockitron lock platform."""
import logging

import requests
import voluptuous as vol

from homeassistant.components.lock import PLATFORM_SCHEMA, LockEntity
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_ID, HTTP_OK
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "lockitron"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_ACCESS_TOKEN): cv.string, vol.Required(CONF_ID): cv.string}
)
BASE_URL = "https://api.lockitron.com"


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Lockitron platform."""
    access_token = config.get(CONF_ACCESS_TOKEN)
    device_id = config.get(CONF_ID)
    response = requests.get(
        f"{BASE_URL}/v2/locks/{device_id}?access_token={access_token}", timeout=5
    )
    if response.status_code == HTTP_OK:
        add_entities([Lockitron(response.json()["state"], access_token, device_id)])
    else:
        _LOGGER.error("Error retrieving lock status during init: %s", response.text)


class Lockitron(LockEntity):
    """Representation of a Lockitron lock."""

    LOCK_STATE = "lock"
    UNLOCK_STATE = "unlock"

    def __init__(self, state, access_token, device_id):
        """Initialize the lock."""
        self._state = state
        self.access_token = access_token
        self.device_id = device_id

    @property
    def name(self):
        """Return the name of the device."""
        return DOMAIN

    @property
    def is_locked(self):
        """Return True if the lock is currently locked, else False."""
        return self._state == Lockitron.LOCK_STATE

    def lock(self, **kwargs):
        """Lock the device."""
        self._state = self.do_change_request(Lockitron.LOCK_STATE)

    def unlock(self, **kwargs):
        """Unlock the device."""
        self._state = self.do_change_request(Lockitron.UNLOCK_STATE)

    def update(self):
        """Update the internal state of the device."""
        response = requests.get(
            f"{BASE_URL}/v2/locks/{self.device_id}?access_token={self.access_token}",
            timeout=5,
        )
        if response.status_code == HTTP_OK:
            self._state = response.json()["state"]
        else:
            _LOGGER.error("Error retrieving lock status: %s", response.text)

    def do_change_request(self, requested_state):
        """Execute the change request and pull out the new state."""
        response = requests.put(
            f"{BASE_URL}/v2/locks/{self.device_id}?access_token={self.access_token}&state={requested_state}",
            timeout=5,
        )
        if response.status_code == HTTP_OK:
            return response.json()["state"]

        _LOGGER.error(
            "Error setting lock state: %s\n%s", requested_state, response.text
        )
        return self._state
