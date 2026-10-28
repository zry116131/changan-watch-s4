# Xiaomi Watch S4 适配方案

## 目标与边界

本项目最终目标是国行蓝牙版 S4，466 × 466 圆屏，Vela JS 快应用（RPK）。初期讨论曾使用 S3 名称，不能据此推断 S3 已验证。Android APK 不能作为本项目的手表应用安装包。

保留简单交互：整屏左右滑动切页、一个刷新按钮。表冠在横向切页版本中实机无反应，因此已移除相关适配；不提供表冠可用的承诺。

## 显示与交互

- `designWidth` 为 466，外层 `stack` 和 `swiper` 均为 466 × 466。
- 每页 `sheet` 完整占满屏幕，以 `align-items:center` 和 `justify-content:center` 居中。
- 内容容器宽 390、高 380；主要数据行宽 350，避免文字落入圆屏边缘。
- 三页采用官方 `swiper`，`loop=false`、`indicator=false`、220ms 动画。
- 使用 `change` 事件同步页码；程序化返回使用 `swipeTo`，非首页先返回前页。
- 不用固定坐标偏移模拟翻页，不同时叠加纵向滚动与横向切页。
- 启动图标为 192 × 192 PNG，圆形内容、透明四角。插画参照 2022 款第一代 UNI-V 的完整侧面比例。

实机已确认左右滑动正常。湿手操作、系统返回手势的所有边界场景未做专项测试，不能将刷新按钮描述成实体按键控制。

## 数据与网络

手表通过 `system.fetch` 请求配对设备可访问的网关。HA 长期令牌只存于网关；手表只携带网关读取密钥。网关只能读取配置中列出的最多 14 类实体，输出适合手表显示的字符串。

进入应用或手动刷新时请求；无后台轮询。手表超时为 15 秒，网关缓存为 30 秒，单个 HA 实体请求超时为 5 秒。返回数据包含车辆源时间和 HA 读取时间，界面采用车辆源时间；请求成功不代表车辆刚刚上报。

内网联调可以使用 HTTP；跨网必须配置 HTTPS 并验证配对设备访问路径。不包含公网部署、自动启动或断网离线钥匙能力。

## 安装与排障

1. 在小米运动健康中完成 S4 配对，使用 AstroBox 连接该设备。
2. 选择“安装快应用”，选中构建后的 RPK，检查预览后安装。
3. 等待安装队列明确显示成功，再在手表打开“长安车况”。
4. 更新前退出手表应用、回到表盘，并让手表靠近配对设备。

若提示未收到安装结果，不能视为安装成功。先确认手表连接，必要时重启 AstroBox，再重试安装；不要因此删除运动健康数据或恢复手表出厂设置。

“待配置 HA 连接”表示无配置包正常启动；401 通常需要核对网关密钥；502 表示网关无法完成 HA 读取；连接超时需检查配对设备到网关的网络。不可用实体显示“—”。

## 验证记录与截图限制

2026-10-28 的实测组合：S4 固件 3.201.79、K Pad、小米运动健康 3.59.2、AstroBox 2.2.0。已验证联网、真实车况读取和居中布局；0.2.2 左右滑动由使用者确认，0.2.3 删除表冠层后安装成功。

曾尝试使用 AstroBox Shell++ 插件获取截图，插件提示缺少表端配套快应用。当时的资源列表未列出 S4，未安装其他型号的配套 Lua 表盘，因此没有可公开的手表实机截图。兼容性随上游更新，以其当前列表为准。

## 参考

- [Vela swiper](https://iot.mi.com/vela/quickapp/zh/components/container/swiper.html)
- [Vela fetch](https://iot.mi.com/vela/quickapp/zh/features/network/fetch.html)
- [Vela 开发工具](https://iot.mi.com/vela/quickapp/zh/guide/start/use-ide.html)
- [AstroBox 资源使用](https://abox.run/docs/usage/resource)
- [Shell++ 资源清单](https://github.com/IKUN-CXKPRO/astrobox-resource-com-shell-liangyi/blob/main/manifest_v2.json)
