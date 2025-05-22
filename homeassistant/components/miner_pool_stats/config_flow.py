"""Config flow for the Miner Pool Stats integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS, CONF_SOURCE, CONF_TYPE, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import PublicPoolServer, PublicPoolServerConnectionError
from .const import DOMAIN, POOL_SOURCE_DX_POOL, POOL_SOURCE_PUBLIC_POOL

_LOGGER = logging.getLogger(__name__)

STEP_POOL_SOURCE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE): SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value=POOL_SOURCE_PUBLIC_POOL,
                        label=POOL_SOURCE_PUBLIC_POOL,
                    ),
                    SelectOptionDict(
                        value=POOL_SOURCE_DX_POOL,
                        label=POOL_SOURCE_DX_POOL,
                    ),
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
    }
)

STEP_PUBLIC_POOL_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default="https://web.public-pool.io/"): str,
    }
)

STEP_DX_POOL_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TYPE): SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value="LTC",
                        label="LTC",
                    ),
                    SelectOptionDict(
                        value="ALEO",
                        label="ALEO",
                    ),
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
    }
)

STEP_WALLET_DATA_SCHEMA = vol.Schema(
    {
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
    await pool.async_initialize()

    return {"title": address.lower()}


class PoolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Miner Pool Stats."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_POOL_SOURCE_SCHEMA,
                errors=errors,
            )

        self._data.update(user_input)

        if user_input[CONF_SOURCE] == POOL_SOURCE_PUBLIC_POOL:
            return await self.async_step_public_pool(user_input)

        if user_input[CONF_SOURCE] == POOL_SOURCE_DX_POOL:
            return await self.async_step_dx_pool(user_input)

        errors["base"] = "Invalid pool source"

        return self.async_show_form(
            step_id="user", data_schema=STEP_POOL_SOURCE_SCHEMA, errors=errors
        )

    async def async_step_public_pool(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the public pool step."""
        errors: dict[str, str] = {}

        # if the user input CONF_URL is None, show the form
        if user_input is None or user_input.get(CONF_URL) is None:
            return self.async_show_form(
                step_id="public_pool",
                data_schema=STEP_PUBLIC_POOL_DATA_SCHEMA,
                errors=errors,
            )

        self._data.update(user_input)

        return await self.async_step_wallet(user_input)

    async def async_step_dx_pool(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the dx pool step."""
        errors: dict[str, str] = {}

        # if the user input CONF_URL is None, show the form
        if user_input is None or user_input.get(CONF_TYPE) is None:
            return self.async_show_form(
                step_id="dx_pool",
                data_schema=STEP_DX_POOL_DATA_SCHEMA,
                errors=errors,
            )

        self._data.update(user_input)

        return await self.async_step_wallet(user_input)

    async def async_step_wallet(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the wallet step."""
        errors: dict[str, str] = {}

        # if the user input CONF_ADDRESS is None, show the form
        if user_input is None or user_input.get(CONF_ADDRESS) is None:
            return self.async_show_form(
                step_id="wallet",
                data_schema=STEP_WALLET_DATA_SCHEMA,
                errors=errors,
            )

        self._data.update(user_input)

        # abort config flow if service is already configured
        self._async_abort_entries_match(self._data)

        try:
            info = await validate_input(self.hass, self._data)
        except PublicPoolServerConnectionError:
            _LOGGER.exception("Connection exception")
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=self._data)

        return self.async_show_form(
            step_id="wallet", data_schema=STEP_WALLET_DATA_SCHEMA, errors=errors
        )
