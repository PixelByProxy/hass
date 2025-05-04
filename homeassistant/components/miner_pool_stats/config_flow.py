"""Config flow for the Miner Pool Stats integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_URL
from homeassistant.core import HomeAssistant

from .api import PublicPoolServer, PublicPoolServerConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): str,
        vol.Required(CONF_ADDRESS): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    url = data[CONF_URL]
    address = data[CONF_ADDRESS]

    pool = PublicPoolServer(hass, url, address)
    await pool.async_get_data()

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


class PoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Miner Pool Stats."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL]
            address = user_input[CONF_ADDRESS]

            # Abort config flow if service is already configured.
            self._async_abort_entries_match({CONF_URL: url, CONF_ADDRESS: address})

            try:
                info = await validate_input(self.hass, user_input)
            except PublicPoolServerConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
