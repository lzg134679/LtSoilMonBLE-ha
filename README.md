# LtSoilMonBLE

- LtSoilMonBLE 是为一款开源的基于蓝牙的土壤湿度传感器而做的Home Assistant自定义集成。它可以自动发现并连接蓝牙土壤湿度计，实时获取土壤湿度、电池电量和蓝牙信号强度等数据用以自动化控制
- 本人并非原作者，本项目已获得原作者授权，此ha集成项目仅作为学习和研究使用
- [硬件开源地址：立创开源平台](https://oshwhub.com/eda_ohrkjzmyz/project_zpojruch)
- [硬件作者的说明视频](https://www.bilibili.com/video/BV14sGm6yEar)

## 功能特性

- 📡 **自动发现**: 通过蓝牙自动发现 LtSoilMonBLE 设备
- 💧 **土壤湿度监测**: 实时获取土壤湿度百分比
- 🔋 **电池电量监测**: 实时监测设备电池电量
- 📶 **信号强度监测**: 监测蓝牙信号强度 (RSSI)
- ⚡ **本地推送**: 基于蓝牙广播的本地数据推送，无需云端

## 设备要求

- 支持 BLE (Bluetooth Low Energy) 的 Home Assistant 主机
- LtSoilMonBLE 蓝牙土壤湿度传感器设备
- 如果你的 Home Assistant 主机不支持蓝牙 BLE，你需要使用ESP32等支持蓝牙的设备作为中转站，具体操作详见[使用ESP32作为蓝牙中转](#使用esp32作为蓝牙中转)

## 安装方法

### 方法一：通过 HACS（推荐）

[![在 Home Assistant 中打开 HACS 添加仓库](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lzg134679&repository=LtSoilMonBLE-ha&category=integration)

或者手动添加：

1. 确保已安装 [HACS](https://hacs.xyz/)
2. 打开 HACS → 右上角三个点 → Custom repositories
3. 添加仓库地址：`https://github.com/lzg134679/LtSoilMonBLE-ha`，类别选择 `Integration`
4. 点击安装 LtSoilMonBLE 集成
5. 重启 Home Assistant

### 方法二：手动安装

1. 下载最新的 [发布版本](https://github.com/lzg134679/LtSoilMonBLE-ha/releases)
2. 将 `custom_components/ltsoilmonble` 文件夹复制到 Home Assistant 的 `config/custom_components/` 目录下
3. 重启 Home Assistant

## 配置方法

[![在 Home Assistant 中配置集成](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ltsoilmonble)

或者手动配置：

1. 在 Home Assistant 中，进入 **设置** → **设备与服务** → **添加集成**
2. 搜索 **LtSoilMonBLE** 并选择
3. 在弹出的列表中选择要添加的设备
4. 点击 **提交** 完成配置

## 实体说明

每个 LtSoilMonBLE 设备会创建以下实体：

| 实体类型 | 名称示例 | 说明 |
|---------|---------|------|
| 传感器 | `sensor.device_name_湿度` | 土壤湿度百分比 (0-100%) |
| 传感器 | `sensor.device_name_电量` | 电池电量百分比 (0-100%) |
| 传感器 | `sensor.device_name_rssi` | 蓝牙信号强度 (dBm) |

## 故障排除

### 设备无法被发现

1. 确保设备已开机并在 Home Assistant 主机的蓝牙范围内
2. 检查 Home Assistant 的蓝牙适配器是否正常工作
3. 在 Home Assistant 的蓝牙集成中确认蓝牙功能已启用

### 数据不更新

1. 确保设备与 Home Assistant 主机距离在蓝牙有效范围内
2. 检查设备电池是否充足
3. 重启 Home Assistant 后重新添加设备

## 使用ESP32作为蓝牙中转

如果你的 Home Assistant 主机离传感器较远或本身不支持蓝牙，可以使用 ESP32 开发板作为蓝牙代理中转站，将蓝牙信号转发到 Home Assistant

- 可使用的ESP32开发板型号：ESP32、ESP32-C3（单核不推荐，容易离线）、ESP32-S3（推荐）、其他更高性能的ESP32
- 在HA中安装 `ESPHome Device Builder` 应用

### 配置步骤（以 ESP32-S3 为例）

1. 在 `ESPHome Device Builder` 页面中点击右下角 `NEW DEVICE`
2. 按向导完成对应设备创建
3. 编辑设备配置，使用以下 YAML 配置（以下为基础配置，可以直接添加蓝牙相关配置到你目前已经在使用的其他ESP32-S3设备中）：

```yaml
esphome: 
  name: esp32s3-ble 
  friendly_name: "ESP32S3-BLE代理" 

esp32: 
  board: esp32-s3-devkitc-1 
  framework: 
    type: esp-idf 

# Enable logging 
logger: 

# Enable Home Assistant API 
api: 
  encryption: 
    key: "hZqPoPa/Ov7U6kvwubYD14FXFbJkNA8a+8aT6IQQn78=" 

ota: 
  - platform: esphome 
    password: "5c51d3c7a9628sr15q229df79a3qg57t" 

wifi: 
  ssid: !secret wifi_ssid 
  password: !secret wifi_password 

  # Enable fallback hotspot (captive portal) in case wifi connection fails 
  ap: 
    ssid: "Esp32S3-Ble" 
    password: "" 

captive_portal: 

esp32_ble_tracker: 
  scan_parameters: 
    active: True 
    interval: 320ms 
    window:   300ms 

bluetooth_proxy: 
  active: true

sensor:
  - platform: uptime
    name: "Uptime Sensor"
    update_interval: 60s
```

> **注意**：请将 `wifi_ssid` 和 `wifi_password` 替换为你的 Wi-Fi 信息，或通过 ESPHome 的 Secrets 管理。`api.encryption.key` 和 `ota.password` 建议替换为自己的密钥（安装向导会自动生成）

4. 点击 `Install`，选择合适的烧录方式将固件烧录到 ESP32-S3
5. 设备上线后，Home Assistant 会自动通过该蓝牙代理发现范围内的 LtSoilMonBLE 设备

## 许可证

本项目采用 [MIT License](LICENSE) 许可