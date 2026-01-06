#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔力桌面助手 - 自动化打包脚本
将项目打包为独立的exe可执行文件
"""

import os
import sys
import subprocess
import shutil
import time
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
            errors='replace'
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

def check_requirements():
    """检查构建环境"""
    print_colored("\n🔍 检查构建环境...", "yellow")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print_colored("❌ Python版本过低，需要3.8或更高版本", "red")
        return False
    
    # 检查必要文件
    required_files = ["main.py", "app_icon.ico", "requirements.txt"]
    for file in required_files:
        if not os.path.exists(file):
            print_colored(f"❌ 缺少必要文件: {file}", "red")
            return False
        else:
            print_colored(f"✅ 找到文件: {file}", "green")
    
    return True

def install_dependencies():
    """安装依赖包"""
    print_colored("\n📦 安装项目依赖...", "yellow")
    
    # 安装requirements.txt中的依赖
    if not run_command("pip install -r requirements.txt", "安装项目依赖"):
        return False
    
    # 安装PyInstaller
    if not run_command("pip install pyinstaller", "安装PyInstaller"):
        return False
        
    return True

def clean_build_dirs():
    """清理构建目录"""
    print_colored("\n🧹 清理构建目录...", "yellow")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print_colored(f"✅ 已删除目录: {dir_name}", "green")
            except Exception as e:
                print_colored(f"⚠️  删除目录失败 {dir_name}: {str(e)}", "yellow")
    
    # 删除.spec文件
    for spec_file in Path(".").glob("*.spec"):
        try:
            spec_file.unlink()
            print_colored(f"✅ 已删除文件: {spec_file}", "green")
        except Exception as e:
            print_colored(f"⚠️  删除文件失败 {spec_file}: {str(e)}", "yellow")

def build_executable():
    """构建exe文件"""
    print_colored("\n🔨 开始构建exe文件...", "yellow")
    
    # PyInstaller命令
    build_command = [
        "pyinstaller",
        "--onefile",                    # 打包成单个文件
        "--windowed",                   # 隐藏控制台窗口
        "--name=魔力桌面助手",          # 设置exe文件名
        "--icon=app_icon.ico",          # 设置图标
        "--add-data=app_icon.ico;.",    # 添加图标文件到资源
        "--distpath=dist",              # 输出目录
        "--workpath=build",             # 工作目录
        "--specpath=.",                 # spec文件位置
        "main.py"                       # 主程序文件
    ]
    
    command_str = " ".join(build_command)
    
    print_colored("构建命令:", "cyan")
    print(command_str)
    print_colored("\n⏳ 正在构建，请稍候...", "yellow")
    
    return run_command(command_str, "构建exe文件")

def create_launcher_batch():
    """创建启动脚本"""
    print_colored("\n📝 创建启动脚本...", "yellow")
    
    batch_content = '''@echo off
chcp 65001 > nul
title 魔力桌面助手

echo.
echo ==========================================
echo          魔力桌面助手 v2.0
echo        功能丰富的桌面工具
echo ==========================================
echo.
echo 🚀 正在启动魔力桌面助手...
echo.

if exist "魔力桌面助手.exe" (
    start "" "魔力桌面助手.exe"
    echo ✅ 启动成功！
) else (
    echo ❌ 找不到魔力桌面助手.exe文件
    echo 请确保文件位于当前目录
    pause
)
'''
    
    try:
        with open("dist/启动魔力桌面助手.bat", "w", encoding="utf-8") as f:
            f.write(batch_content)
        print_colored("✅ 启动脚本创建成功", "green")
        return True
    except Exception as e:
        print_colored(f"❌ 创建启动脚本失败: {str(e)}", "red")
        return False

def create_usage_instructions():
    """创建使用说明文件"""
    print_colored("\n📖 创建使用说明...", "yellow")
    
    instructions = '''魔力桌面助手 v2.0 - 使用说明
===========================================

🎯 软件介绍
魔力桌面助手是一款功能丰富的桌面工具，集成了：
- 智能壁纸更换和屏保功能
- 完整的日历提醒系统  
- 每日资讯推送
- 系统托盘运行

🚀 快速开始
1. 双击"魔力桌面助手.exe"启动程序
2. 或者双击"启动魔力桌面助手.bat"
3. 首次运行会显示主界面，可根据需要配置各项功能

💡 主要功能

📅 日历提醒
- 支持添加各种提醒事项
- 多种重复模式：每天、每周、每月、每年
- 到时间会弹出美观的桌面通知

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
- 开机自启动选项
- 单实例运行保护

⚙️ 系统要求
- Windows 10/11
- 至少500MB可用磁盘空间
- 网络连接（用于获取资讯和壁纸）

🆘 常见问题

Q: 程序无法启动？
A: 1. 检查是否有杀毒软件拦截
   2. 右键"以管理员身份运行"
   3. 确保Windows版本支持

Q: 提醒功能不工作？
A: 1. 检查系统通知设置是否开启
   2. 确保程序在后台运行（系统托盘）

Q: 壁纸无法下载？
A: 1. 检查网络连接
   2. 确认防火墙设置
   3. 可能需要配置代理

📞 技术支持
如遇问题请访问项目主页：
https://github.com/moli-xia/magic-desktop-assistant

版本：v2.0
更新日期：2024年
'''
    
    try:
        with open("dist/使用说明.txt", "w", encoding="utf-8") as f:
            f.write(instructions)
        print_colored("✅ 使用说明创建成功", "green")
        return True
    except Exception as e:
        print_colored(f"❌ 创建使用说明失败: {str(e)}", "red")
        return False

def verify_build():
    """验证构建结果"""
    print_colored("\n🔍 验证构建结果...", "yellow")
    
    exe_path = "dist/魔力桌面助手.exe"
    if not os.path.exists(exe_path):
        print_colored("❌ exe文件未生成", "red")
        return False
    
    file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
    print_colored(f"✅ exe文件已生成", "green")
    print_colored(f"📁 文件位置: {exe_path}", "cyan")
    print_colored(f"📊 文件大小: {file_size:.1f} MB", "cyan")
    
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
    print_colored("       魔力桌面助手 - 自动化打包工具", "purple")
    print_colored("="*50, "cyan")
    
    start_time = time.time()
    
    try:
        # 检查环境
        if not check_requirements():
            print_colored("\n❌ 环境检查失败，请解决上述问题后重试", "red")
            return False
        
        # 安装依赖
        if not install_dependencies():
            print_colored("\n❌ 依赖安装失败", "red")
            return False
        
        # 清理构建目录
        clean_build_dirs()
        
        # 构建exe
        if not build_executable():
            print_colored("\n❌ 构建失败", "red")
            return False
        
        # 创建额外文件
        create_launcher_batch()
        create_usage_instructions()
        
        # 验证结果
        if not verify_build():
            return False
        
        # 构建成功
        end_time = time.time()
        duration = end_time - start_time
        
        print_colored("\n" + "="*50, "green")
        print_colored("          🎉 构建成功完成！", "green")
        print_colored("="*50, "green")
        print_colored(f"⏱️  总耗时: {duration:.1f} 秒", "cyan")
        print_colored(f"📁 输出目录: dist/", "cyan")
        print_colored(f"🚀 可执行文件: dist/魔力桌面助手.exe", "cyan")
        print_colored(f"📋 启动脚本: dist/启动魔力桌面助手.bat", "cyan")
        print_colored(f"📖 使用说明: dist/使用说明.txt", "cyan")
        
        print_colored("\n💡 接下来你可以:", "yellow")
        print_colored("   1. 进入 dist/ 目录", "white")
        print_colored("   2. 双击运行 魔力桌面助手.exe", "white")
        print_colored("   3. 或使用 启动魔力桌面助手.bat", "white")
        print_colored("   4. 分发整个 dist/ 目录给其他用户", "white")
        
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
        sys.exit(0)

