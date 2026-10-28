# 配置与部署

## 1. 准备 Home Assistant

先安装并配置 [长安 UNI-V 集成](https://github.com/zry116131/home-assistant-changan-univ)，在 HA 开发者工具中核对车况实体属于同一辆车。

自行在 HA 用户资料中创建长期访问令牌。它继承创建账户的权限，**不是只读令牌**；本项目仅通过网关代码限制车况读取。令牌只保存在自己的网关机器，不要提交到 GitHub 或发到 Issue。

## 2. 生成本地配置

```sh
python3 tools/configure.py
```

依次输入 HA 地址、HA Token（不回显）、配对设备可以访问的网关地址，例如 `http://gateway.local:8765`。生成：

- `.local/gateway.json`：HA 地址、HA Token、随机网关读取密钥和实体映射；文件权限 600。
- `watch/src/common/connection.js`：网关地址与读取密钥；文件权限 600。

这两个文件均被 Git 忽略。脚本拒绝覆盖已有网关配置；需要修改时编辑文件，确保两端读取密钥一致。不要将 `localhost` 当作其他设备能够访问的地址。

## 3. 映射实体

在 `.local/gateway.json` 的 `entities` 中填写实际 ID。下例只是占位，**不能直接作为真实实体使用**：

```json
{
  "remaining_range": "sensor.your_vehicle_remaining_range",
  "fuel_percent": "sensor.your_vehicle_fuel_percent"
}
```

至少配置一项；未配置项显示“—”。支持以下 14 个键：

| 键 | 数据 | 预期 HA 状态 |
| --- | --- | --- |
| remaining_range | 剩余续航 | 数值 |
| fuel_percent | 剩余油量 | 百分比数值 |
| odometer | 总里程 | 数值 |
| fuel_consumption | 百公里油耗 | 数值 |
| cabin_temperature | 车内温度 | 数值 |
| battery_voltage | 电瓶电压 | 数值 |
| engine_running | 发动机 | on / off |
| air_conditioner | 空调 | on / off |
| tire_pressure_fl | 左前胎压 | 数值 |
| tire_pressure_fr | 右前胎压 | 数值 |
| tire_pressure_rl | 左后胎压 | 数值 |
| tire_pressure_rr | 右后胎压 | 数值 |
| vehicle_reported_at | 车辆源上报时间 | ISO 日期时间；无时区按 UTC+8 |
| authentication_required | 长安登录失效 | on / off |

只允许 `sensor.*` / `binary_sensor.*` ID。单位优先沿用 HA 的 `unit_of_measurement`；请确认油量实体确实以百分比表示。不要把“HA 最近更新时间”误映射为车辆真实上报时间。

## 4. 启动网关

```sh
python3 gateway/server.py --config .local/gateway.json --bind 0.0.0.0 --port 8765
```

默认不传 `--bind` 时只监听本机。确认防火墙和网络允许配对设备访问，先从配对设备打开网关的 `/health`；健康检查无需密钥，只返回服务标识，不代表 HA 读取一定成功。

网关提供 `GET /v1/status`，要求 `Authorization: Bearer <watch_key>`，只读取精确映射实体，不调用 HA 服务。网关机器和进程需要保持运行；仓库未提供系统服务配置。跨网使用 HTTPS 反向代理，不要把明文 HTTP 及密钥直接暴露到公网。

## 5. 构建与安装

```sh
cd watch
npm ci
npm run build
```

生成 `dist/cn.zry.changanstatus.debug.0.2.3.rpk`，通过 AstroBox 安装。此文件包含你生成的读取密钥，勿上传。

仅构建无配置包时，可以在尚未配置的工作副本中把 `watch/src/common/connection.example.js` 复制为 `connection.js`，再运行构建。不要覆盖正在使用的真实配置。Release 提供的就是这种无配置包，它没有表内配置入口。

安装成功后，检查三页布局、左右滑动、刷新、车辆上报时间和缺失值。编译成功不等于所有型号兼容；跨型号移植需要重新做实机验证。
