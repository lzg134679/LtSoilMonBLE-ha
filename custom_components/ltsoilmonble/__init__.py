from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfo,
    async_register_callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """设置 LtSoilMonBLE 集成（yaml方式，已废弃）"""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["devices"] = {}

    _LOGGER.info("LtSoilMonBLE 集成启动（yaml方式，已废弃，请通过集成页面添加设备）")

    _async_register_bluetooth_listener(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置 LtSoilMonBLE 集成（config_entry方式）"""
    hass.data.setdefault(DOMAIN, {})
    if "devices" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["devices"] = {}

    address = entry.data["address"]
    name = entry.data["name"]

    _LOGGER.info("LtSoilMonBLE 集成启动（config_entry方式），设备: %s (%s)", name, address)

    hass.data[DOMAIN][entry.entry_id] = {
        "address": address,
        "name": name,
    }

    if address not in hass.data[DOMAIN]["devices"]:
        hass.data[DOMAIN]["devices"][address] = {
            "address": address,
            "name": name,
            "rssi": None,
            "raw_adc": None,
            "volt_adc": None,
            "moisture": None,
            "battery": None,
            "config_entry_id": entry.entry_id,
        }
    else:
        hass.data[DOMAIN]["devices"][address]["config_entry_id"] = entry.entry_id
        hass.data[DOMAIN]["devices"][address]["name"] = name

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, address)},
        connections={(dr.CONNECTION_BLUETOOTH, address)},
        name=name,
        manufacturer="LtSoilMonBLE",
        model="Bluetooth Soil Moisture Sensor",
    )

    _async_register_bluetooth_listener(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_entry))

    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """更新配置条目"""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


def _async_register_bluetooth_listener(hass: HomeAssistant) -> None:
    """注册蓝牙监听器（singleton模式，只注册一次）"""
    if hass.data[DOMAIN].get("listener_registered"):
        return

    hass.data[DOMAIN]["listener_registered"] = True
    devices = hass.data[DOMAIN]["devices"]

    @callback
    def _get_config_entry_id_for_address(hass: HomeAssistant, address: str) -> str | None:
        """根据设备地址查找对应的config_entry_id"""
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.data.get("address") == address:
                return entry.entry_id
        return None

    @callback
    def _bluetooth_callback(
        service_info: BluetoothServiceInfo,
        change: BluetoothChange,
    ) -> None:
        """处理蓝牙设备数据更新"""
        address = service_info.address
        name = service_info.name or f"LtSoilMonBLE {address[-5:]}"

        if SERVICE_UUID not in service_info.service_data:
            return

        data = service_info.service_data[SERVICE_UUID]
        if len(data) < 6:
            _LOGGER.warning("设备 %s 的数据长度不足: %d", name, len(data))
            return

        raw_adc = int.from_bytes(data[0:2], "little", signed=True)
        volt_adc = int.from_bytes(data[2:4], "little", signed=True)
        moisture = data[4]
        battery = data[5]

        _LOGGER.debug(
            "设备 %s 数据: 湿度=%d%%, 电量=%d%%, 原始ADC=%d, 电压ADC=%d, RSSI=%d",
            name, moisture, battery, raw_adc, volt_adc, service_info.rssi
        )

        config_entry_id = _get_config_entry_id_for_address(hass, address)

        if address in devices:
            devices[address]["rssi"] = service_info.rssi
            devices[address]["raw_adc"] = raw_adc
            devices[address]["volt_adc"] = volt_adc
            devices[address]["moisture"] = moisture
            devices[address]["battery"] = battery
            devices[address]["name"] = name
            if config_entry_id:
                devices[address]["config_entry_id"] = config_entry_id

            async_dispatcher_send(hass, f"{DOMAIN}_update_{address}")
        elif config_entry_id:
            devices[address] = {
                "address": address,
                "name": name,
                "rssi": service_info.rssi,
                "raw_adc": raw_adc,
                "volt_adc": volt_adc,
                "moisture": moisture,
                "battery": battery,
                "config_entry_id": config_entry_id,
            }

            device_registry = dr.async_get(hass)
            device_registry.async_get_or_create(
                config_entry_id=config_entry_id,
                identifiers={(DOMAIN, address)},
                connections={(dr.CONNECTION_BLUETOOTH, address)},
                name=name,
                manufacturer="LtSoilMonBLE",
                model="Bluetooth Soil Moisture Sensor",
            )

            async_dispatcher_send(hass, f"{DOMAIN}_new_device", address)

    async_register_callback(
        hass,
        _bluetooth_callback,
        BluetoothCallbackMatcher(service_data_uuid=SERVICE_UUID),
        BluetoothScanningMode.ACTIVE,
    )