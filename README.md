# 长安车况 · Xiaomi Watch S4

面向国行蓝牙版 Xiaomi Watch S4 的 Vela JS 快应用，将 Home Assistant 中的长安车况显示在手表上。实测车辆为 **2022 款第一代长安 UNI-V**。

<img src="assets/univ-2022-anime-icon-round.png" width="160" alt="第一代 UNI-V 侧面二次元圆形图标">

- 整屏左右滑动，查看续航油量、温度状态、四轮胎压三页。
- 圆屏居中布局、横向切页动画、手动刷新；不做表冠适配。
- 显示车辆上报时间；缺失数据显示“—”，请求失败时保留旧值并提示失败。
- 只读车况：没有解锁、启动、空调控制或数字车钥匙功能。

[下载安装包](https://github.com/zry116131/changan-watch-s4/releases/latest) · [手表适配方案](docs/watch-adaptation.md) · [配置与部署](docs/setup.md) · [发布与凭据边界](docs/security.md)

## 安装包与使用前提

Release 的 `changan-status-0.2.3-unconfigured.rpk` 是**无配置包**：不含服务器地址、HA Token、手表读取密钥或个人车况。可用来安装和检查三页布局，启动后提示“待配置 HA 连接”，不会显示真实数据。

接入自己的车辆需要先部署网关、配置实际 HA 实体，再构建自己的 RPK。目前没有表内配置界面。自行构建的 RPK 内含网关读取密钥，应保持私有。

```text
S4 快应用 → 配对安卓设备的联网通道 → 只读网关 → Home Assistant → 长安集成
```

手表使用 `system.fetch` 请求网关；本文的实测配对设备是 K Pad。网关需要持续运行且能访问 HA，配对设备需要能访问网关。**本方案不支持离开配对设备后独立联网，也不能代替车辆钥匙。**

HA 数据源使用已有的 [长安 UNI-V 集成](https://github.com/zry116131/home-assistant-changan-univ)。网关不会直接登录长安账号，也不会触发车辆刷新；先确保 HA 已能正常读取同一辆车的实体。

## 快速开始

环境：Python 3.9+、Node.js 和 npm。网关仅使用 Python 标准库；快应用构建固定使用 aiot-toolkit 2.0.5 / jsc 1.0.3，实际 Node 验证版本见发布说明。

```sh
git clone https://github.com/zry116131/changan-watch-s4.git
cd changan-watch-s4
python3 tools/configure.py
# 根据 docs/setup.md 编辑 .local/gateway.json 中的 entities
python3 gateway/server.py --config .local/gateway.json --bind 0.0.0.0 --port 8765
```

另开终端：

```sh
cd watch
npm ci
npm run build
```

将 `watch/dist/*.rpk` 传到配对设备，通过 AstroBox 的“安装快应用”安装。完整步骤及实体映射见 [配置与部署](docs/setup.md)。

## 验证范围

| 项目 | 状态 |
| --- | --- |
| 国行蓝牙版 S4，固件 3.201.79 | 已实机安装、读取真实 HA 车况 |
| K Pad / 小米运动健康 3.59.2 / AstroBox 2.2.0 | 实测组合 |
| 0.2.2 左右滑动与圆屏布局 | 使用者确认正常 |
| 0.2.3 简化版 | 已安装；沿用同一滑动组件，移除表冠适配，未另作完整交互回归 |
| 公开无配置 RPK | 从公开源码构建；未另行上表测试 |
| S3、S4 Sport、41mm、eSIM、其他手表 | 未验证，不承诺兼容 |
| 手表截图 | 尚未取得，不把模拟图当作实机截图 |

```sh
python3 -m unittest discover -s gateway -v
```

现有 6 项网关测试涵盖未知值、真实零值、单位、数据时间、登录失效、HTTP 鉴权及路由白名单。

## 项目结构

```text
watch/       Vela 快应用源码及构建依赖
gateway/     只读 HA 网关与测试
tools/       本地配置生成器
docs/        适配、部署、发布说明
assets/      圆形应用图标
```

代码以 MIT 许可发布。图标为 AI 生成的第一代 UNI-V 风格插画，参考来源见 [素材说明](assets/README.md)；车辆品牌、商标及第三方素材权利归各自权利人。本项目为个人项目，与小米、长安无官方关联。
