# 🎨 桌面壁纸屏保工具 (WallpaperDownloader)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 一个简洁优雅的 Windows 桌面壁纸与屏保工具，支持自动下载高质量壁纸、屏保轮播，以及聚合信息推送（每日早报、一言、土味情话、舔狗日记、每日一文）。

---

## ✨ 亮点功能

- **壁纸自动更换**：默认开启，支持自定义更换间隔（分钟）。
- **屏保系统**：全屏显示，支持切换间隔与智能预加载。
- **信息推送聚合**：默认勾选所有服务，并默认开启自动推送；推送时间默认 `09:10`。
- **窗口与通知**：信息推送以聚合窗口展示；通知弹窗尽量减少干扰。
- **单实例运行**：重复启动会聚焦到已运行窗口。
- **开机自启**：可选开关。

---

## 🚀 快速开始

- **下载可执行文件**：前往 Releases 下载 `WallpaperDownloader.exe` 后双击运行。
- **源码运行**：

```bash
# 1) 克隆仓库
git clone https://github.com/<YOUR_GITHUB>/desk-wallpapers.git
cd desk-wallpapers

# 2) 创建虚拟环境并安装依赖
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt

# 3) 运行
python main.py
```

---

## 🖥️ 使用说明

- **壁纸**
  - 点击“更换壁纸”立即更换。
  - “自动更换”默认开启，可在“间隔(分钟)”输入更换间隔。
- **屏保**
  - 点击“启动屏保”。
  - 可设置“切换间隔(分钟)”与“空闲时间(分钟)”后自动进入。
- **信息推送**
  - 勾选服务（默认全选）。
  - “信息自动推送”默认开启，默认推送时间 `09:10`。
  - 到点后自动打开“信息推送”窗口，聚合展示所选服务内容。

---

## ⚙️ 配置与默认值

- `信息自动推送`：默认开启；时间默认 `09:10`。
- `服务勾选`：默认勾选每日早报、Hitokoto 一言、土味情话、舔狗日记、每日一文。
- `壁纸自动更换`：默认开启；默认间隔 30 分钟（示例界面值，可自行调整）。

> 提示：首次使用信息推送请在设置中填写 ALAPI Token。

---

## 🧰 打包构建 (PyInstaller)

推荐使用已提供的 `WallpaperDownloader.spec`：

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller WallpaperDownloader.spec
# 产物位于 dist/WallpaperDownloader/ 或 dist/WallpaperDownloader.exe
```

或使用命令行参数：

```bash
pyinstaller --onefile --windowed --icon=app_icon.ico --name=WallpaperDownloader main.py
```

> 说明：spec 已配置 `console=False` 与图标文件，保证窗口应用无控制台。

---

## 📦 目录结构

```
├── main.py                    # 主程序
├── alapi_services.py          # 信息推送聚合窗口
├── daily_news.py              # 每日早报窗口
├── integrated_features.py     # 综合功能（若有）
├── app_icon.ico               # 应用图标
├── WallpaperDownloader.spec   # PyInstaller 配置
├── requirements.txt           # 依赖列表
├── README.md                  # 文档
└── dist/                      # 构建输出
```

---

## 📝 变更摘要（本次）

- 默认开启“自动更换壁纸”。
- 默认勾选全部信息推送服务并开启“信息自动推送”。
- 默认推送时间设为 `09:10`。
- 信息推送采用聚合窗口，减少多余提示弹窗。
- 每日早报窗口居中显示。

---

## ❓ 常见问题

- **没有弹出信息推送？** 请确认系统未休眠、推送时间格式为 `HH:MM` 且已到达；也可将时间设置为当前时间后 1 分钟进行测试。
- **任务栏无图标？** 已在窗口与托盘设置多尺寸图标，若仍不显示，请确认 `app_icon.ico` 存在。

---

## 📄 许可证

MIT License © 2024 壁纸屏保下载器