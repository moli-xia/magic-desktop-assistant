# 构建说明

## 打包为可执行文件

使用PyInstaller将项目打包为exe文件：

### 1. 安装PyInstaller
```bash
pip install pyinstaller
```

### 2. 执行打包命令
```bash
pyinstaller --onefile --windowed --name=魔力桌面助手 --icon=app_icon.ico --add-data=app_icon.ico;. main.py
```

### 3. 命令参数说明
- `--onefile`: 打包成单个文件
- `--windowed`: Windows下隐藏控制台窗口  
- `--name`: 指定exe文件名
- `--icon`: 设置应用图标
- `--add-data`: 添加资源文件到打包中

### 4. 生成文件
打包完成后，可执行文件位于 `dist/魔力桌面助手.exe`

## 依赖管理

更新依赖列表：
```bash
pip freeze > requirements.txt
```

安装项目依赖：
```bash
pip install -r requirements.txt
```
