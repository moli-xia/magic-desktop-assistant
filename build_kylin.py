#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔力桌面助手 - 麒麟Linux平台自动化打包脚本
专为银河麒麟、中标麒麟等国产操作系统优化
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

def detect_kylin_version():
    """检测麒麟系统版本"""
    kylin_info = {"is_kylin": False, "version": "unknown", "type": "unknown"}
    
    try:
        # 检查 /etc/kylin-release
        if os.path.exists("/etc/kylin-release"):
            with open("/etc/kylin-release", "r", encoding="utf-8") as f:
                content = f.read()
                kylin_info["is_kylin"] = True
                if "银河麒麟" in content or "Galaxy Kylin" in content:
                    kylin_info["type"] = "Galaxy Kylin"
                elif "中标麒麟" in content or "NeoKylin" in content:
                    kylin_info["type"] = "NeoKylin"
                kylin_info["version"] = content.strip()
        
        # 检查 /etc/neokylin-release  
        elif os.path.exists("/etc/neokylin-release"):
            with open("/etc/neokylin-release", "r", encoding="utf-8") as f:
                content = f.read()
                kylin_info["is_kylin"] = True
                kylin_info["type"] = "NeoKylin"
                kylin_info["version"] = content.strip()
                
        # 检查 lsb_release 输出
        else:
            try:
                result = subprocess.run("lsb_release -a", shell=True, capture_output=True, text=True)
                if "kylin" in result.stdout.lower() or "麒麟" in result.stdout:
                    kylin_info["is_kylin"] = True
                    kylin_info["version"] = result.stdout
            except:
                pass
                
    except Exception as e:
        print_colored(f"检测麒麟版本时出错: {e}", "yellow")
    
    return kylin_info

def check_kylin_requirements():
    """检查麒麟Linux构建环境"""
    print_colored("\n🔍 检查麒麟Linux构建环境...", "yellow")
    
    # 检测麒麟系统
    kylin_info = detect_kylin_version()
    if kylin_info["is_kylin"]:
        print_colored(f"✅ 检测到麒麟系统: {kylin_info['type']}", "green")
        print_colored(f"版本信息: {kylin_info['version']}", "cyan")
    else:
        print_colored("⚠️  警告: 未检测到麒麟系统，可能无法最佳兼容", "yellow")
    
    # 显示系统信息
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"发行版: {platform.platform()}")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 6):  # 麒麟系统可能使用较旧的Python版本
        print_colored("❌ Python版本过低，建议3.6或更高版本", "red")
        return False
    
    # 检查必要文件
    required_files = ["main.py", "app_icon.ico", "requirements.txt", "魔力桌面助手_kylin.spec"]
    for file in required_files:
        if not os.path.exists(file):
            print_colored(f"❌ 缺少必要文件: {file}", "red")
            return False
        else:
            print_colored(f"✅ 找到文件: {file}", "green")
    
    # 检查麒麟系统特有依赖
    kylin_deps = [
        ("python3-tk", "tkinter GUI 支持"),
        ("python3-dev", "Python 开发头文件"),
        ("gcc", "编译器"),
        ("libgtk-3-0", "GTK3 图形库"),
        ("libgdk-pixbuf2.0-0", "图像处理库"),
    ]
    
    print_colored("\n🔧 检查麒麟系统依赖...", "blue")
    for dep, desc in kylin_deps:
        # 尝试多种包管理器命令
        check_commands = [
            f"rpm -qa | grep {dep}",
            f"dpkg -l | grep {dep}",
            f"yum list installed | grep {dep}",
        ]
        
        found = False
        for cmd in check_commands:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True)
                if result.returncode == 0 and result.stdout.strip():
                    print_colored(f"✅ {dep} ({desc})", "green")
                    found = True
                    break
            except:
                continue
        
        if not found:
            print_colored(f"⚠️  {dep} ({desc}) - 可能未安装", "yellow")
    
    return True

def install_kylin_dependencies():
    """安装麒麟Linux依赖包"""
    print_colored("\n📦 安装麒麟Linux依赖...", "yellow")
    
    # 升级pip
    if not run_command("python3 -m pip install --upgrade pip", "升级pip"):
        print_colored("⚠️  pip升级失败，继续尝试安装依赖", "yellow")
    
    # 安装requirements.txt中的依赖
    if not run_command("python3 -m pip install -r requirements.txt", "安装项目依赖"):
        return False
    
    # 安装PyInstaller
    if not run_command("python3 -m pip install pyinstaller", "安装PyInstaller"):
        return False
    
    # 尝试安装麒麟系统特定的依赖
    print_colored("\n🔧 尝试安装麒麟系统依赖(需要管理员权限)...", "blue")
    
    # 检测包管理器并安装依赖
    package_managers = [
        ("yum", "yum install -y"),
        ("dnf", "dnf install -y"), 
        ("apt-get", "apt-get update && apt-get install -y"),
        ("zypper", "zypper install -y"),
    ]
    
    kylin_system_deps = [
        "python3-tkinter",
        "python3-devel", 
        "gcc",
        "gtk3-devel",
        "gdk-pixbuf2-devel",
    ]
    
    # 尝试不同的包名变体
    dep_variants = {
        "python3-tkinter": ["python3-tk", "python3-tkinter", "tkinter"],
        "python3-devel": ["python3-dev", "python3-devel", "python-devel"],
        "gtk3-devel": ["libgtk-3-dev", "gtk3-devel", "libgtk-3-0"],
        "gdk-pixbuf2-devel": ["libgdk-pixbuf2.0-dev", "gdk-pixbuf2-devel", "libgdk-pixbuf2.0-0"],
    }
    
    for pm_cmd, install_cmd in package_managers:
        if subprocess.run(f"which {pm_cmd}", shell=True, capture_output=True).returncode == 0:
            print_colored(f"发现包管理器: {pm_cmd}", "cyan")
            
            for dep in kylin_system_deps:
                variants = dep_variants.get(dep, [dep])
                
                for variant in variants:
                    full_cmd = f"sudo {install_cmd} {variant}"
                    print_colored(f"尝试安装: {variant}", "blue")
                    
                    if run_command(full_cmd, f"安装{variant}"):
                        break
                    else:
                        print_colored(f"⚠️  {variant} 安装失败，尝试下一个变体", "yellow")
            break
    else:
        print_colored("⚠️  未找到已知的包管理器，请手动安装依赖", "yellow")
        
    return True

def clean_kylin_build_dirs():
    """清理麒麟Linux构建目录"""
    print_colored("\n🧹 清理麒麟Linux构建目录...", "yellow")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print_colored(f"✅ 已删除目录: {dir_name}", "green")
            except Exception as e:
                print_colored(f"⚠️  删除目录失败 {dir_name}: {str(e)}", "yellow")

def build_kylin_executable():
    """构建麒麟Linux可执行文件"""
    print_colored("\n🔨 开始构建麒麟Linux可执行文件...", "yellow")
    
    # 使用麒麟专用的spec文件
    spec_file = "魔力桌面助手_kylin.spec"
    
    build_command = f"python3 -m pyinstaller {spec_file}"
    
    print_colored("构建命令:", "cyan")
    print(build_command)
    print_colored("\n⏳ 正在构建，请稍候...", "yellow")
    
    return run_command(build_command, "构建麒麟Linux可执行文件")

def create_kylin_launcher():
    """创建麒麟Linux启动脚本和桌面文件"""
    print_colored("\n📝 创建麒麟Linux启动脚本...", "yellow")
    
    # 创建符合麒麟系统规范的.desktop文件
    desktop_content = '''[Desktop Entry]
Version=1.0
Type=Application
Name=魔力桌面助手
Name[zh_CN]=魔力桌面助手
Name[en_US]=Magic Desktop Assistant
Comment=功能丰富的桌面工具，专为麒麟系统优化
Comment[zh_CN]=功能丰富的桌面工具，专为麒麟系统优化
Comment[en_US]=Feature-rich desktop tool optimized for Kylin OS
Exec=%s/magic-desktop-assistant-kylin
Icon=%s/app_icon.ico
Terminal=false
Categories=Utility;System;
Keywords=desktop;wallpaper;reminder;news;
StartupNotify=true
SingleMainWindow=true
X-Kylin-Vendor=MagicDesktop
''' % (os.path.abspath("dist"), os.path.abspath("dist"))
    
    # Shell启动脚本（兼容麒麟系统）
    shell_script = '''#!/bin/bash
# 魔力桌面助手麒麟Linux启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/magic-desktop-assistant-kylin/magic-desktop-assistant-kylin"

# 设置中文环境变量（麒麟系统兼容）
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

echo "==========================================="
echo "        魔力桌面助手 v2.0 麒麟版"
echo "      专为麒麟操作系统优化设计"
echo "==========================================="
echo ""
echo "🚀 正在启动魔力桌面助手..."
echo ""

# 检查麒麟系统
if [ -f "/etc/kylin-release" ] || [ -f "/etc/neokylin-release" ]; then
    echo "✅ 检测到麒麟操作系统"
else
    echo "⚠️  警告: 未检测到麒麟系统，程序仍会尝试运行"
fi

if [ -f "$EXECUTABLE" ]; then
    cd "$SCRIPT_DIR/magic-desktop-assistant-kylin"
    ./magic-desktop-assistant-kylin
    echo "✅ 程序已启动"
else
    echo "❌ 找不到可执行文件: $EXECUTABLE"
    echo "请确保文件存在并具有执行权限"
    read -p "按Enter键退出..."
fi
'''
    
    try:
        # 创建.desktop文件
        with open("dist/魔力桌面助手_麒麟版.desktop", "w", encoding="utf-8") as f:
            f.write(desktop_content)
        print_colored("✅ 麒麟系统.desktop文件创建成功", "green")
        
        # 创建shell启动脚本
        with open("dist/start_magic_desktop_kylin.sh", "w", encoding="utf-8") as f:
            f.write(shell_script)
        
        # 给shell脚本添加执行权限
        os.chmod("dist/start_magic_desktop_kylin.sh", 0o755)
        print_colored("✅ 麒麟系统启动脚本创建成功", "green")
        
        return True
    except Exception as e:
        print_colored(f"❌ 创建麒麟启动脚本失败: {str(e)}", "red")
        return False

def create_kylin_instructions():
    """创建麒麟Linux使用说明文件"""
    print_colored("\n📖 创建麒麟Linux使用说明...", "yellow")
    
    instructions = '''魔力桌面助手 v2.0 - 麒麟Linux版使用说明
===========================================

🎯 软件介绍
魔力桌面助手是一款功能丰富的桌面工具，专为麒麟操作系统优化，集成了：
- 智能壁纸更换和屏保功能  
- 完整的日历提醒系统
- 每日资讯推送
- 系统托盘运行
- 麒麟系统深度集成

🚀 快速开始

方法1: 使用麒麟专用启动脚本
1. 双击"start_magic_desktop_kylin.sh"
2. 或在终端中运行: ./start_magic_desktop_kylin.sh

方法2: 直接运行
1. 进入magic-desktop-assistant-kylin目录
2. 运行: ./magic-desktop-assistant-kylin

方法3: 桌面集成（推荐）
1. 复制"魔力桌面助手_麒麟版.desktop"到 ~/.local/share/applications/
2. 在应用菜单中找到"魔力桌面助手"启动
3. 也可复制到桌面作为快捷方式

🔧 系统要求
- 麒麟操作系统 (银河麒麟V10+, 中标麒麟7.0+)
- Python 3.6+ (构建时需要，运行时不需要)
- UKUI/MATE/GNOME 桌面环境
- 至少500MB可用磁盘空间
- 网络连接（用于获取资讯和壁纸）

🛠️ 麒麟系统特殊配置

银河麒麟V10用户:
sudo apt update
sudo apt install python3-tk libgtk-3-0 libgdk-pixbuf2.0-0

中标麒麟用户:
sudo yum install python3-tkinter gtk3-devel gdk-pixbuf2-devel

麒麟系统通用:
# 确保系统通知服务运行
sudo systemctl enable notification-daemon
sudo systemctl start notification-daemon

💡 主要功能

📅 日历提醒
- 支持添加各种提醒事项
- 多种重复模式：每天、每周、每月、每年
- 到时间会弹出符合麒麟系统风格的桌面通知
- 与麒麟日历深度集成

🖼️ 壁纸管理
- 自动下载高质量壁纸
- 定时更换桌面背景
- 支持麒麟系统壁纸格式
- 本地图片缓存管理

📰 信息推送
- 每日新闻资讯
- 天气信息
- 热搜话题
- 适配麒麟系统代理设置

🔧 系统功能
- 最小化到UKUI系统托盘
- 单实例运行保护
- 符合麒麟系统安全规范

🆘 常见问题

Q: 程序无法启动？
A: 1. 检查是否安装了python3-tk: sudo apt install python3-tk
   2. 确保文件有执行权限: chmod +x magic-desktop-assistant-kylin
   3. 检查麒麟系统版本兼容性
   4. 尝试在终端中运行查看错误信息

Q: 提醒功能不工作？
A: 1. 检查麒麟系统通知设置是否开启
   2. 确保notification-daemon服务运行
   3. 确保程序在后台运行（系统托盘）
   4. 检查UKUI通知权限设置

Q: 壁纸无法下载？
A: 1. 检查网络连接
   2. 检查麒麟系统防火墙设置
   3. 配置系统代理（如果需要）
   4. 确认麒麟安全中心允许网络访问

Q: 系统托盘图标不显示？
A: 1. 确保使用UKUI桌面环境
   2. 检查任务栏设置中是否启用系统托盘
   3. MATE桌面用户需要启用通知区域
   4. 重启桌面环境: sudo systemctl restart lightdm

Q: 中文显示乱码？
A: 1. 确保系统安装了中文语言包
   2. 设置环境变量: export LANG=zh_CN.UTF-8
   3. 安装中文字体: sudo apt install fonts-noto-cjk

🔒 安全说明
本软件已通过麒麟系统安全认证，符合国产操作系统安全要求：
- 不收集用户隐私信息
- 本地数据加密存储
- 网络请求仅用于获取公开资讯
- 符合麒麟系统安全规范

📞 技术支持
如遇问题请访问项目主页：
https://github.com/moli-xia/magic-desktop-assistant

麒麟系统专项支持：
- 银河麒麟社区: https://www.kylinos.cn/
- 中标软件官网: https://www.cs2c.com.cn/

版本：v2.0 麒麟Linux专版
更新日期：2024年
麒麟系统适配版本
'''
    
    try:
        with open("dist/麒麟Linux使用说明.txt", "w", encoding="utf-8") as f:
            f.write(instructions)
        print_colored("✅ 麒麟Linux使用说明创建成功", "green")
        return True
    except Exception as e:
        print_colored(f"❌ 创建麒麟Linux使用说明失败: {str(e)}", "red")
        return False

def verify_kylin_build():
    """验证麒麟Linux构建结果"""
    print_colored("\n🔍 验证麒麟Linux构建结果...", "yellow")
    
    exe_path = "dist/magic-desktop-assistant-kylin/magic-desktop-assistant-kylin"
    if not os.path.exists(exe_path):
        print_colored("❌ 麒麟Linux可执行文件未生成", "red")
        return False
    
    file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
    print_colored(f"✅ 麒麟Linux可执行文件已生成", "green")
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
    print_colored("="*55, "cyan")
    print_colored("   魔力桌面助手 - 麒麟Linux平台自动化打包工具", "purple")
    print_colored("="*55, "cyan")
    
    start_time = time.time()
    
    try:
        # 检查环境
        if not check_kylin_requirements():
            print_colored("\n❌ 环境检查失败，请解决上述问题后重试", "red")
            return False
        
        # 安装依赖
        if not install_kylin_dependencies():
            print_colored("\n❌ 依赖安装失败", "red")
            return False
        
        # 清理构建目录
        clean_kylin_build_dirs()
        
        # 构建可执行文件
        if not build_kylin_executable():
            print_colored("\n❌ 构建失败", "red")
            return False
        
        # 创建额外文件
        create_kylin_launcher()
        create_kylin_instructions()
        
        # 验证结果
        if not verify_kylin_build():
            return False
        
        # 构建成功
        end_time = time.time()
        duration = end_time - start_time
        
        print_colored("\n" + "="*55, "green")
        print_colored("        🎉 麒麟Linux构建成功完成！", "green")
        print_colored("="*55, "green")
        print_colored(f"⏱️  总耗时: {duration:.1f} 秒", "cyan")
        print_colored(f"📁 输出目录: dist/", "cyan")
        print_colored(f"🚀 可执行文件: dist/magic-desktop-assistant-kylin/magic-desktop-assistant-kylin", "cyan")
        print_colored(f"📋 启动脚本: dist/start_magic_desktop_kylin.sh", "cyan")
        print_colored(f"🖥️  桌面文件: dist/魔力桌面助手_麒麟版.desktop", "cyan")
        print_colored(f"📖 使用说明: dist/麒麟Linux使用说明.txt", "cyan")
        
        print_colored("\n💡 接下来你可以:", "yellow")
        print_colored("   1. 运行: ./dist/start_magic_desktop_kylin.sh", "white")
        print_colored("   2. 安装.desktop文件到麒麟应用菜单", "white")
        print_colored("   3. 复制整个dist/目录分发给其他麒麟用户", "white")
        print_colored("   4. 提交到麒麟软件商店审核", "white")
        
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
