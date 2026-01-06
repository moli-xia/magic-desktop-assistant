# 魔力桌面助手 v2.1

一个功能丰富的桌面工具，集成了壁纸管理、屏保功能、信息推送和智能日历提醒系统。

## 🎯 主要功能

### 🟣 悬浮球（桌面快捷入口）
- **动态发光悬浮球**：可拖拽到任意位置，靠近屏幕边缘自动吸附并变为条形
- **右键功能菜单**：快速显示/隐藏主窗口、切换皮肤、退出程序
- **滚轮点击 AI 对话**：一键打开 AI 智能对话窗口
- **多款皮肤**：未来光球 / 霓虹脉冲 / 经典蓝 / 简约白

### 💻 壁纸与屏保
- **智能壁纸更换**：自动下载并设置高质量桌面壁纸
- **屏保模式**：定时切换精美图片作为屏保
- **图片管理**：本地图片缓存和管理系统

### 📅 日历提醒系统
- **智能提醒**：支持设置不同时间的提醒事项
- **重复选项**：每天、每周、每月、每年重复提醒
- **颜色标记**：为不同提醒设置个性化颜色
- **年份范围**：支持1975-2075年的广泛年份选择
- **桌面通知**：到时间弹出美观的桌面提醒窗口
- **详情查看**：通知窗口支持查看和编辑提醒详情

### 📰 信息推送
- **每日资讯**：新闻、天气、热搜等信息推送
- **API集成**：支持多种第三方API服务
- **定时推送**：可配置的信息推送时间

### 🔧 系统功能
- **系统托盘**：最小化到系统托盘运行
- **单实例运行**：防止重复启动，重复运行会激活已有窗口
- **开机启动**：支持设置开机自动启动，智能清理无效启动项
- **数据持久化**：所有设置和提醒数据自动保存
- **配置备份**：支持配置导出和导入，防止数据丢失

### 界面预览
![](demo.png)

## 🚀 快速开始

### 环境要求
- Windows 10/11
- Python 3.8+ （如果从源码运行）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
python main.py
```

### 使用提示（关闭/托盘/退出）
- 点击主窗口右上角关闭按钮后，程序会**隐藏到系统托盘**（任务栏不再显示图标）。
- 需要彻底退出时：在**托盘图标右键**或**悬浮球右键**选择“退出程序”。

## 📦 打包为可执行文件

项目支持跨平台打包，可以将程序打包为适用于不同操作系统的独立应用程序。

### 支持的平台

| 平台 | 操作系统版本 | 输出格式 | 构建脚本 |
|------|-------------|----------|----------|
| **Windows** | Windows 10/11 | `.exe` 可执行文件 | `build_exe.py` |
| **Linux** | Ubuntu 18.04+, CentOS 7+ | 可执行文件 + `.desktop` | `build_linux.py` |
| **麒麟Linux** | 银河麒麟V10+, 中标麒麟7.0+ | 优化的可执行文件 | `build_kylin.py` |
| **macOS** | macOS 10.14+ (Mojave及以上) | `.app` 应用程序包 + DMG | `build_macos.py` |

### 快速打包

#### 方法1：自动化构建（推荐）
```bash
# 运行跨平台构建脚本
python3 build_all_platforms.py
```

#### 方法2：单独构建特定平台
```bash
# Windows版本
python build_exe.py

# Linux版本  
python3 build_linux.py

# 麒麟Linux版本
python3 build_kylin.py

# macOS版本
python3 build_macos.py
```

### 环境准备

#### Windows环境
```powershell
# 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 运行构建
python build_exe.py
```

#### Linux环境
```bash
# 安装系统依赖
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install python3-tk python3-dev build-essential libgtk-3-0

# CentOS/RHEL:
sudo yum install python3-tkinter python3-devel gcc gtk3-devel

# 安装Python依赖
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

# 运行构建
python3 build_linux.py
```

#### macOS环境
```bash
# 安装Xcode命令行工具（如果没有）
xcode-select --install

# 安装Python依赖
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

# 运行构建
python3 build_macos.py
```

### 打包输出

#### Windows版本
```
dist/
├── 魔力桌面助手.exe          # 主程序
├── 启动魔力桌面助手.bat       # 启动脚本
└── 使用说明.txt              # 使用说明
```

#### Linux版本
```
dist/
├── magic-desktop-assistant/          # 应用目录
│   └── magic-desktop-assistant       # 可执行文件
├── start_magic_desktop.sh           # 启动脚本
├── 魔力桌面助手.desktop               # 桌面集成文件
└── Linux使用说明.txt                 # 使用说明
```

#### macOS版本
```
dist/
├── 魔力桌面助手.app/                  # 应用程序包
├── 魔力桌面助手_v2.0.dmg              # DMG安装包（可选）
├── 启动魔力桌面助手.sh                # Shell启动脚本
└── macOS使用说明.txt                 # 使用说明
```

## 📋 项目结构

```
magic-desktop-assistant/
├── main.py                     # 主程序入口（含悬浮球/托盘/AI对话等）
├── wallpaper_widget.py         # 壁纸模块
├── screensaver_manager.py      # 屏保后台逻辑
├── screensaver_widget.py       # 屏保UI/预览
├── daily_news.py               # 每日资讯模块
├── weather_service.py          # 天气服务
├── integrated_features.py      # 集成功能模块
├── alapi_services.py           # ALAPI服务封装
├── alapi_widgets.py            # 信息推送等小组件
├── calendar_reminder.py        # 日历提醒模块
├── reminder_notification.py    # 提醒通知弹窗
├── app_icon.ico                # 应用图标
├── requirements.txt            # 依赖列表
├── build_exe.py                # Windows打包脚本
├── build_linux.py              # Linux打包脚本
├── build_kylin.py              # 麒麟Linux打包脚本
├── build_macos.py              # macOS打包脚本
├── build_all_platforms.py      # 跨平台打包入口
├── LICENSE
└── README.md
```

## 💡 功能特色

### 日历提醒亮点
- **直观界面**：清晰的月历视图，一目了然
- **灵活重复**：支持多种重复模式，满足不同需求
- **视觉提示**：有提醒的日期显示红色圆点标记
- **智能通知**：美观的桌面通知窗口，支持重复类型显示
- **快速导航**：年份和月份下拉选择，快速跳转任意日期

### 技术特性
- **现代UI**：基于ttkbootstrap的现代化界面设计
- **线程安全**：后台任务不影响界面响应
- **异常处理**：完善的错误处理和恢复机制
- **模块化设计**：清晰的代码结构，易于维护和扩展

## 🎨 界面预览

### 主界面
- 壁纸设置区域
- 屏保配置选项
- 信息推送设置
- 日历提醒入口

### 日历界面
- 月历视图显示
- 年份月份下拉选择
- 提醒事项列表
- 添加/编辑提醒功能

### 提醒通知
- 美观的弹窗设计
- 重复类型显示
- 查看详情按钮
- 确认操作按钮

## ⚙️ 配置说明

### API配置
程序支持多种API服务，可在设置中配置相应的Token：
- 天气API
- 新闻API
- 其他第三方服务

### 数据存储
- 配置文件自动保存在用户目录
- 提醒数据使用JSON格式存储
- 支持数据导入导出

### 配置备份功能
- **导出配置**：将所有设置和提醒数据导出为JSON文件
- **导入配置**：从JSON文件恢复所有配置和数据
- **文件命名**：使用日期时间格式，如`魔力桌面助手配置_20250925_162200.json`
- **完整备份**：包含壁纸设置、API配置、日历提醒等所有数据
- **安全导入**：导入前确认提示，避免意外覆盖数据

### 开机启动功能
- **智能设置**：自动检测并设置开机启动项
- **路径兼容**：正确处理包含空格和中文的路径
- **无效清理**：自动清理注册表中的无效启动项
- **权限处理**：智能处理权限不足的情况
- **文件验证**：确保启动文件存在且可访问

#### 设置开机启动
1. 打开魔力桌面助手
2. 点击菜单栏 **"设置"** → **"开机启动"** 复选框
3. 程序会自动清理无效启动项并设置正确的启动路径

#### 故障排除
- **权限问题**：右键以管理员身份运行程序
- **杀毒软件**：部分杀毒软件可能阻止修改启动项
- **文件移动**：移动程序后需重新设置开机启动

## 🔄 版本历史

### v2.1
- ✨ 新增桌面悬浮球：拖拽、吸附变条形、右键功能菜单
- 🎨 新增多款悬浮球皮肤并支持右键切换
- 🧠 新增滚轮点击打开 AI 智能对话窗口
- 🔧 优化关闭逻辑：关闭主窗口隐藏到托盘，保留右下角托盘图标

### v2.0
- ✨ 新增完整的日历提醒系统
- 🎨 优化界面设计和用户体验
- 📅 支持年份月份下拉选择
- 🔄 增加"每年"重复选项
- 🎯 改进提醒通知窗口
- 💾 **新增配置导入导出功能**
- 🔒 支持完整的数据备份和恢复
- 🚀 **修复开机启动功能**：智能清理无效启动项，支持路径兼容
- 🐛 修复多项用户反馈的问题
- 📦 支持跨平台打包（Windows/Linux/macOS/麒麟Linux）

### v1.x
- 基础壁纸和屏保功能
- 信息推送系统
- 系统托盘支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境搭建
1. Fork本仓库
2. 创建开发分支
3. 安装依赖：`pip install -r requirements.txt`
4. 进行开发和测试
5. 提交Pull Request

### 代码规范
- 使用中文注释和文档字符串
- 遵循PEP 8代码风格
- 添加适当的错误处理
- 编写单元测试（如适用）

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) - 现代化的tkinter主题
- [Pillow](https://github.com/python-pillow/Pillow) - Python图像处理库
- [requests](https://github.com/psf/requests) - HTTP库
- [pystray](https://github.com/moses-palmer/pystray) - 系统托盘库
- [PyInstaller](https://github.com/pyinstaller/pyinstaller) - Python应用打包工具

## 📞 支持

如果您在使用过程中遇到问题，请：
1. 查看使用说明文档
2. 在GitHub上提交Issue
3. 检查是否有相关的解决方案

---

**感谢使用魔力桌面助手！** 🎉

如果这个项目对您有帮助，请给我们一个⭐️
