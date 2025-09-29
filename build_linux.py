#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔力桌面助手 - Linux平台自动化打包脚本
将项目打包为Linux平台的独立可执行文件
"""

import os
import sys
import subprocess
import shutil
import time
import platform
from pathlib import Path

def print_colored(text, color="white"):
    """打印彩色文本"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m", 
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def run_command(command, description="执行命令"):
    """执行系统命令并显示输出"""
    print_colored(f"\n📋 {description}...", "blue")
    print_colored(f"命令: {command}", "cyan")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print_colored(f"✅ {description}成功！", "green")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print_colored(f"❌ {description}失败！", "red")
            if result.stderr.strip():
                print_colored(f"错误信息: {result.stderr}", "red")
            return False
            
    except Exception as e:
        print_colored(f"❌ 执行命令时出错: {str(e)}", "red")
        return False

def check_linux_requirements():
    """检查Linux构建环境"""
    print_colored("\n🔍 检查Linux构建环境...", "yellow")
    
    # 检查操作系统
    if not sys.platform.startswith('linux'):
        print_colored("⚠️  警告: 当前不在Linux环境中，可能无法正确构建Linux版本", "yellow")
    
    # 显示系统信息
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"发行版: {platform.platform()}")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print_colored("❌ Python版本过低，需要3.8或更高版本", "red")
        return False
    
    # 检查必要文件
    required_files = ["main.py", "app_icon.ico", "requirements.txt", "魔力桌面助手_linux.spec"]
    for file in required_files:
        if not os.path.exists(file):
            print_colored(f"❌ 缺少必要文件: {file}", "red")
            return False
        else:
            print_colored(f"✅ 找到文件: {file}", "green")
    
    # 检查系统依赖
    system_deps = [
        ("python3-tk", "tkinter GUI 支持"),
        ("python3-dev", "Python 开发头文件"),
        ("build-essential", "编译工具链"),
    ]
    
    print_colored("\n🔧 检查系统依赖...", "blue")
    for dep, desc in system_deps:
        # 检查是否安装（简单检查，可能不完全准确）
        try:
            result = subprocess.run(f"dpkg -l | grep {dep}", shell=True, capture_output=True)
            if result.returncode == 0:
                print_colored(f"✅ {dep} ({desc})", "green")
            else:
                print_colored(f"⚠️  {dep} ({desc}) - 可能未安装", "yellow")
        except:
            print_colored(f"? {dep} ({desc}) - 无法检查", "yellow")
    
    return True

def install_linux_dependencies():
    """安装Linux依赖包"""
    print_colored("\n📦 安装Linux依赖...", "yellow")
    
    # 升级pip
    if not run_command("python3 -m pip install --upgrade pip", "升级pip"):
        print_colored("⚠️  pip升级失败，继续尝试安装依赖", "yellow")
    
    # 安装requirements.txt中的依赖
    if not run_command("python3 -m pip install -r requirements.txt", "安装项目依赖"):
        return False
    
    # 安装PyInstaller
    if not run_command("python3 -m pip install pyinstaller", "安装PyInstaller"):
        return False
    
    # 安装Linux特定的依赖
    linux_deps = [
        "python3-tk",  # tkinter支持
    ]
    
    print_colored("\n🔧 尝试安装系统依赖(需要sudo权限)...", "blue")
    for dep in linux_deps:
        print_colored(f"如果下面的命令失败，请手动安装: sudo apt-get install {dep}", "yellow")
        run_command(f"sudo apt-get update && sudo apt-get install -y {dep}", f"安装{dep}")
        
    return True

def clean_linux_build_dirs():
    """清理Linux构建目录"""
    print_colored("\n🧹 清理Linux构建目录...", "yellow")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print_colored(f"✅ 已删除目录: {dir_name}", "green")
            except Exception as e:
                print_colored(f"⚠️  删除目录失败 {dir_name}: {str(e)}", "yellow")

def build_linux_executable():
    """构建Linux可执行文件"""
    print_colored("\n🔨 开始构建Linux可执行文件...", "yellow")
    
    # 使用自定义的spec文件
    spec_file = "魔力桌面助手_linux.spec"
    
    build_command = f"python3 -m pyinstaller {spec_file}"
    
    print_colored("构建命令:", "cyan")
    print(build_command)
    print_colored("\n⏳ 正在构建，请稍候...", "yellow")
    
    return run_command(build_command, "构建Linux可执行文件")

def create_linux_launcher():
    """创建Linux启动脚本"""
    print_colored("\n📝 创建Linux启动脚本...", "yellow")
    
    # 创建.desktop文件
    desktop_content = '''[Desktop Entry]
Version=1.0
Type=Application
Name=魔力桌面助手
Name[en]=Magic Desktop Assistant
Comment=功能丰富的桌面工具
Comment[en]=Feature-rich desktop tool
Exec=%s/magic-desktop-assistant
Icon=%s/app_icon.ico
Terminal=false
Categories=Utility;
StartupNotify=true
''' % (os.path.abspath("dist"), os.path.abspath("dist"))
    
    # Shell启动脚本
    shell_script = '''#!/bin/bash
# 魔力桌面助手启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/magic-desktop-assistant/magic-desktop-assistant"

echo "===========================================" 
echo "          魔力桌面助手 v2.0"
echo "        功能丰富的桌面工具"
echo "==========================================="
echo ""
echo "🚀 正在启动魔力桌面助手..."
echo ""

if [ -f "$EXECUTABLE" ]; then
    cd "$SCRIPT_DIR/magic-desktop-assistant"
    ./magic-desktop-assistant
    echo "✅ 程序已启动"
else
    echo "❌ 找不到可执行文件: $EXECUTABLE"
    echo "请确保文件存在并具有执行权限"
    read -p "按Enter键退出..."
fi
'''
    
    try:
        # 创建.desktop文件
        with open("dist/魔力桌面助手.desktop", "w", encoding="utf-8") as f:
            f.write(desktop_content)
        print_colored("✅ .desktop文件创建成功", "green")
        
        # 创建shell启动脚本
        with open("dist/start_magic_desktop.sh", "w", encoding="utf-8") as f:
            f.write(shell_script)
        
        # 给shell脚本添加执行权限
        os.chmod("dist/start_magic_desktop.sh", 0o755)
        print_colored("✅ 启动脚本创建成功", "green")
        
        return True
    except Exception as e:
        print_colored(f"❌ 创建启动脚本失败: {str(e)}", "red")
        return False

def create_linux_instructions():
    """创建Linux使用说明文件"""
    print_colored("\n📖 创建Linux使用说明...", "yellow")
    
    instructions = '''魔力桌面助手 v2.0 - Linux版使用说明
===========================================

🎯 软件介绍
魔力桌面助手是一款功能丰富的桌面工具，集成了：
- 智能壁纸更换和屏保功能
- 完整的日历提醒系统  
- 每日资讯推送
- 系统托盘运行

🚀 快速开始

方法1: 使用启动脚本
1. 双击"start_magic_desktop.sh"
2. 或在终端中运行: ./start_magic_desktop.sh

方法2: 直接运行
1. 进入magic-desktop-assistant目录
2. 运行: ./magic-desktop-assistant

方法3: 桌面集成
1. 复制"魔力桌面助手.desktop"到 ~/.local/share/applications/
2. 在应用菜单中找到"魔力桌面助手"启动

🔧 系统要求
- Linux 发行版 (Ubuntu 18.04+, CentOS 7+, 等)
- Python 3.8+ (构建时需要，运行时不需要)
- X11 或 Wayland 桌面环境
- 至少500MB可用磁盘空间
- 网络连接（用于获取资讯和壁纸）

📦 依赖安装
如果程序无法启动，可能需要安装以下系统依赖:

Ubuntu/Debian:
sudo apt-get update
sudo apt-get install python3-tk libgtk-3-0 libgdk-pixbuf2.0-0

CentOS/RHEL:
sudo yum install tkinter gtk3 gdk-pixbuf2

Fedora:
sudo dnf install python3-tkinter gtk3 gdk-pixbuf2

💡 主要功能

📅 日历提醒
- 支持添加各种提醒事项
- 多种重复模式：每天、每周、每月、每年
- 到时间会弹出桌面通知

🖼️ 壁纸管理
- 自动下载高质量壁纸
- 定时更换桌面背景
- 本地图片缓存管理

📰 信息推送
- 每日新闻资讯
- 天气信息
- 热搜话题

🔧 系统功能
- 最小化到系统托盘
- 单实例运行保护

🆘 常见问题

Q: 程序无法启动？
A: 1. 检查是否安装了python3-tk: sudo apt-get install python3-tk
   2. 确保文件有执行权限: chmod +x magic-desktop-assistant
   3. 检查桌面环境是否支持

Q: 提醒功能不工作？
A: 1. 检查系统通知设置是否开启
   2. 确保程序在后台运行（系统托盘）
   3. 某些Linux发行版可能需要额外配置通知权限

Q: 壁纸无法下载？
A: 1. 检查网络连接
   2. 确认防火墙设置
   3. 可能需要配置代理

Q: 系统托盘图标不显示？
A: 1. 确保桌面环境支持系统托盘
   2. GNOME用户可能需要安装扩展: TopIcons Plus
   3. KDE/XFCE通常默认支持

📞 技术支持
如遇问题请访问项目主页：
https://github.com/moli-xia/magic-desktop-assistant

版本：v2.0 Linux
更新日期：2024年
'''
    
    try:
        with open("dist/Linux使用说明.txt", "w", encoding="utf-8") as f:
            f.write(instructions)
        print_colored("✅ Linux使用说明创建成功", "green")
        return True
    except Exception as e:
        print_colored(f"❌ 创建Linux使用说明失败: {str(e)}", "red")
        return False

def verify_linux_build():
    """验证Linux构建结果"""
    print_colored("\n🔍 验证Linux构建结果...", "yellow")
    
    exe_path = "dist/magic-desktop-assistant/magic-desktop-assistant"
    if not os.path.exists(exe_path):
        print_colored("❌ Linux可执行文件未生成", "red")
        return False
    
    file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
    print_colored(f"✅ Linux可执行文件已生成", "green")
    print_colored(f"📁 文件位置: {exe_path}", "cyan")
    print_colored(f"📊 文件大小: {file_size:.1f} MB", "cyan")
    
    # 检查文件权限
    if os.access(exe_path, os.X_OK):
        print_colored("✅ 文件具有执行权限", "green")
    else:
        print_colored("⚠️  文件缺少执行权限，正在修复...", "yellow")
        try:
            os.chmod(exe_path, 0o755)
            print_colored("✅ 执行权限已添加", "green")
        except Exception as e:
            print_colored(f"❌ 添加执行权限失败: {str(e)}", "red")
    
    # 列出dist目录内容
    print_colored("\n📂 dist目录内容:", "blue")
    try:
        for item in os.listdir("dist"):
            item_path = os.path.join("dist", item)
            if os.path.isfile(item_path):
                size = os.path.getsize(item_path) / 1024  # KB
                print(f"  📄 {item} ({size:.1f} KB)")
            else:
                print(f"  📁 {item}/")
    except Exception as e:
        print_colored(f"⚠️  无法列出dist目录: {str(e)}", "yellow")
    
    return True

def main():
    """主函数"""
    print_colored("="*50, "cyan")
    print_colored("     魔力桌面助手 - Linux平台自动化打包工具", "purple")
    print_colored("="*50, "cyan")
    
    start_time = time.time()
    
    try:
        # 检查环境
        if not check_linux_requirements():
            print_colored("\n❌ 环境检查失败，请解决上述问题后重试", "red")
            return False
        
        # 安装依赖
        if not install_linux_dependencies():
            print_colored("\n❌ 依赖安装失败", "red")
            return False
        
        # 清理构建目录
        clean_linux_build_dirs()
        
        # 构建可执行文件
        if not build_linux_executable():
            print_colored("\n❌ 构建失败", "red")
            return False
        
        # 创建额外文件
        create_linux_launcher()
        create_linux_instructions()
        
        # 验证结果
        if not verify_linux_build():
            return False
        
        # 构建成功
        end_time = time.time()
        duration = end_time - start_time
        
        print_colored("\n" + "="*50, "green")
        print_colored("          🎉 Linux构建成功完成！", "green")
        print_colored("="*50, "green")
        print_colored(f"⏱️  总耗时: {duration:.1f} 秒", "cyan")
        print_colored(f"📁 输出目录: dist/", "cyan")
        print_colored(f"🚀 可执行文件: dist/magic-desktop-assistant/magic-desktop-assistant", "cyan")
        print_colored(f"📋 启动脚本: dist/start_magic_desktop.sh", "cyan")
        print_colored(f"🖥️  桌面文件: dist/魔力桌面助手.desktop", "cyan")
        print_colored(f"📖 使用说明: dist/Linux使用说明.txt", "cyan")
        
        print_colored("\n💡 接下来你可以:", "yellow")
        print_colored("   1. 运行: ./dist/start_magic_desktop.sh", "white")
        print_colored("   2. 或进入dist/magic-desktop-assistant/运行程序", "white")
        print_colored("   3. 复制整个dist/目录分发给其他Linux用户", "white")
        print_colored("   4. 安装.desktop文件到应用菜单", "white")
        
        return True
        
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  用户中断构建过程", "yellow")
        return False
    except Exception as e:
        print_colored(f"\n❌ 构建过程中出现错误: {str(e)}", "red")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print_colored("\n构建失败，请检查错误信息并重试", "red")
        sys.exit(1)
    else:
        print_colored("\n按Enter键退出...", "cyan")
        try:
            input()
        except:
            pass
        sys.exit(0)
