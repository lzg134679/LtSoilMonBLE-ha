from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.typing import StateType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """设置sensor平台（yaml方式，已废弃）"""
    _LOGGER.info("LtSoilMonBLE yaml方式已废弃，请通过集成页面添加设备")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置sensor平台（config_entry方式）"""
    address = entry.data["address"]
    name = entry.data["name"]
    config_entry_id = entry.entry_id

    devices = hass.data[DOMAIN]["devices"]

    if address not in devices:
        devices[address] = {
            "address": address,
            "name": name,
            "rssi": None,
            "raw_adc": None,
            "volt_adc": None,
            "moisture": None,
            "battery": None,
            "config_entry_id": config_entry_id,
        }
    else:
        devices[address]["config_entry_id"] = config_entry_id
        if devices[address]["name"] != name:
            devices[address]["name"] = name

    device = devices[address]

    entities = [
        LtSoilMonBLEMoistureSensor(hass, address, device),
        LtSoilMonBLEBatterySensor(hass, address, device),
        LtSoilMonBLERssiSensor(hass, address, device),
    ]
    async_add_entities(entities)


class LtSoilMonBLEBaseSensor(SensorEntity):
    """传感器基类"""

    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, address: str, device: dict[str, Any]) -> None:
        self._hass = hass
        self._address = address
        self._device = device
        self._attr_unique_id = f"ltsoilmonble_{address}_{self.sensor_type}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=device["name"],
            manufacturer="LtSoilMonBLE",
            model="Bluetooth Soil Moisture Sensor",
        )

    @property
    def sensor_type(self) -> str:
        raise NotImplementedError

    @property
    def device_data(self) -> dict[str, Any]:
        """获取最新的设备数据"""
        devices = self._hass.data.get(DOMAIN, {}).get("devices", {})
        return devices.get(self._address, self._device)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_update_{self._address}",
                self._async_update_state,
            )
        )

    @callback
    def _async_update_state(self) -> None:
        self.async_write_ha_state()


class LtSoilMonBLEMoistureSensor(LtSoilMonBLEBaseSensor):
    """土壤湿度传感器"""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:water-percent"

    @property
    def sensor_type(self) -> str:
        return "moisture"

    @property
    def name(self) -> str:
        return f"{self.device_data['name']} 湿度"

    @property
    def native_value(self) -> StateType:
        return self.device_data.get("moisture")


class LtSoilMonBLEBatterySensor(LtSoilMonBLEBaseSensor):
    """电池电量传感器"""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery"

    @property
    def sensor_type(self) -> str:
        return "battery"

    @property
    def name(self) -> str:
        return f"{self.device_data['name']} 电量"

    @property
    def native_value(self) -> StateType:
        return self.device_data.get("battery")


class LtSoilMonBLERssiSensor(LtSoilMonBLEBaseSensor):
    """蓝牙信号强度传感器"""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_icon = "mdi:signal"

    @property
    def sensor_type(self) -> str:
        return "rssi"

    @property
    def name(self) -> str:
        return f"{self.device_data['name']} RSSI"

    @property
    def native_value(self) -> StateType:
        return self.device_data.get("rssi")