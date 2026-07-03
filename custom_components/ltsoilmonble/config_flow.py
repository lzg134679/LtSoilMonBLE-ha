from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.core import callback
import voluptuous as vol

from .const import DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)


class LtSoilMonBLEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """LtSoilMonBLE配置流程"""

    VERSION = 1

    def __init__(self) -> None:
        """初始化配置流程"""
        self._discovered_devices: list[BluetoothServiceInfoBleak] = []

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> LtSoilMonBLEOptionsFlow:
        """获取选项流程"""
        return LtSoilMonBLEOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """用户配置步骤"""
        return await self.async_step_device_selection()

    async def async_step_device_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """设备选择步骤"""
        if user_input is not None:
            address = user_input["device"]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            self._discovered_devices = [
                device
                for device in async_discovered_service_info(self.hass)
                if SERVICE_UUID in device.service_data
            ]

            service_info = None
            for device in self._discovered_devices:
                if device.address == address:
                    service_info = device
                    break

            name = service_info.name if service_info else f"LtSoilMonBLE {address[-5:]}"

            return self.async_create_entry(
                title=name,
                data={"address": address, "name": name},
            )

        configured_addresses = {
            entry.data.get("address")
            for entry in self.hass.config_entries.async_entries(DOMAIN)
        }

        self._discovered_devices = [
            device
            for device in async_discovered_service_info(self.hass)
            if SERVICE_UUID in device.service_data
            and device.address not in configured_addresses
        ]

        if not self._discovered_devices:
            return self.async_show_form(
                step_id="device_selection",
                data_schema=vol.Schema({}),
                errors={"base": "no_devices_found"},
                description_placeholders={
                    "hint": "请确保LtSoilMonBLE设备已开机并在蓝牙范围内，或检查设备是否已添加"
                },
            )

        devices_schema = vol.Schema(
            {
                vol.Required("device"): vol.In(
                    {
                        device.address: f"{device.name or '未知设备'} ({device.address})"
                        for device in self._discovered_devices
                    }
                )
            }
        )

        return self.async_show_form(
            step_id="device_selection",
            data_schema=devices_schema,
            description_placeholders={
                "count": len(self._discovered_devices),
            },
        )

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> config_entries.FlowResult:
        """蓝牙发现步骤"""
        _LOGGER.info("蓝牙发现设备: %s (%s)", discovery_info.name, discovery_info.address)

        address = discovery_info.address
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        name = discovery_info.name or f"LtSoilMonBLE {address[-5:]}"

        self.context["title_placeholders"] = {
            "name": name,
        }

        return self.async_create_entry(
            title=name,
            data={"address": address, "name": name},
        )


class LtSoilMonBLEOptionsFlow(config_entries.OptionsFlow):
    """LtSoilMonBLE选项流程"""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """初始化选项流程"""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """选项初始化步骤"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "name",
                    default=self.config_entry.data.get("name"),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )