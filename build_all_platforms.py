#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔力桌面助手 - 跨平台自动化打包脚本
自动检测平台并选择相应的构建方式
支持: Windows, Linux, 麒麟Linux, macOS
"""

import os
import sys
import subprocess
import platform
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

def detect_platform():
    """检测当前运行平台"""
    system = platform.system().lower()
    
    platform_info = {
        "system": system,
        "is_windows": system == "windows",
        "is_linux": system == "linux", 
        "is_macos": system == "darwin",
        "is_kylin": False,
        "architecture": platform.machine(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    
    # 检测是否为麒麟系统
    if platform_info["is_linux"]:
        kylin_files = [
            "/etc/kylin-release",
            "/etc/neokylin-release",
        ]
        
        for kylin_file in kylin_files:
            if os.path.exists(kylin_file):
                platform_info["is_kylin"] = True
                break
        
        # 检查lsb_release输出
        if not platform_info["is_kylin"]:
            try:
                result = subprocess.run("lsb_release -a", shell=True, capture_output=True, text=True)
                if "kylin" in result.stdout.lower() or "麒麟" in result.stdout:
                    platform_info["is_kylin"] = True
            except:
                pass
    
    return platform_info

def show_platform_info(platform_info):
    """显示平台信息"""
    print_colored("="*60, "cyan")
    print_colored("         魔力桌面助手 - 跨平台自动化打包工具", "purple")
    print_colored("="*60, "cyan")
    
    print_colored("\n🔍 平台检测结果:", "blue")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform_info['architecture']}")
    print(f"Python版本: {platform_info['python_version']}")
    
    if platform_info["is_windows"]:
        print_colored("🪟 检测到Windows系统", "green")
    elif platform_info["is_kylin"]:
        print_colored("🐉 检测到麒麟Linux系统", "green")
    elif platform_info["is_linux"]:
        print_colored("🐧 检测到Linux系统", "green")
    elif platform_info["is_macos"]:
        print_colored("🍎 检测到macOS系统", "green")
    else:
        print_colored("❓ 未知操作系统", "yellow")

def check_build_scripts():
    """检查构建脚本是否存在"""
    required_scripts = {
        "windows": "build_exe.py",
        "linux": "build_linux.py", 
        "kylin": "build_kylin.py",
        "macos": "build_macos.py",
    }
    
    missing_scripts = []
    
    for platform_name, script_name in required_scripts.items():
        if not os.path.exists(script_name):
            missing_scripts.append(f"{platform_name}: {script_name}")
        else:
            print_colored(f"✅ 找到{platform_name}构建脚本: {script_name}", "green")
    
    if missing_scripts:
        print_colored("\n❌ 缺少以下构建脚本:", "red")
        for missing in missing_scripts:
            print_colored(f"   - {missing}", "red")
        return False
    
    return True

def run_build_script(script_name, platform_name):
    """运行指定的构建脚本"""
    print_colored(f"\n🚀 开始构建{platform_name}版本...", "blue")
    print_colored(f"执行脚本: {script_name}", "cyan")
    
    try:
        # 使用当前Python解释器执行脚本
        result = subprocess.run([sys.executable, script_name], capture_output=False)
        
        if result.returncode == 0:
            print_colored(f"✅ {platform_name}版本构建成功！", "green")
            return True
        else:
            print_colored(f"❌ {platform_name}版本构建失败！", "red")
            return False
            
    except Exception as e:
        print_colored(f"❌ 执行{platform_name}构建脚本时出错: {str(e)}", "red")
        return False

def show_menu(platform_info):
    """显示构建菜单"""
    print_colored("\n📋 可用的构建选项:", "blue")
    
    options = []
    
    if platform_info["is_windows"]:
        options.append(("1", "构建Windows版本 (.exe)", "build_exe.py", "Windows"))
        print_colored("   1. 构建Windows版本 (.exe) [推荐]", "green")
    else:
        options.append(("1", "构建Windows版本 (.exe)", "build_exe.py", "Windows"))
        print_colored("   1. 构建Windows版本 (.exe) [跨平台]", "white")
    
    if platform_info["is_linux"] and not platform_info["is_kylin"]:
        options.append(("2", "构建Linux版本", "build_linux.py", "Linux"))
        print_colored("   2. 构建Linux版本 [推荐]", "green")
    else:
        options.append(("2", "构建Linux版本", "build_linux.py", "Linux"))
        print_colored("   2. 构建Linux版本 [跨平台]", "white")
    
    if platform_info["is_kylin"]:
        options.append(("3", "构建麒麟Linux版本", "build_kylin.py", "麒麟Linux"))
        print_colored("   3. 构建麒麟Linux版本 [推荐]", "green")
    else:
        options.append(("3", "构建麒麟Linux版本", "build_kylin.py", "麒麟Linux"))
        print_colored("   3. 构建麒麟Linux版本 [跨平台]", "white")
    
    if platform_info["is_macos"]:
        options.append(("4", "构建macOS版本 (.app)", "build_macos.py", "macOS"))
        print_colored("   4. 构建macOS版本 (.app) [推荐]", "green")
    else:
        options.append(("4", "构建macOS版本 (.app)", "build_macos.py", "macOS"))
        print_colored("   4. 构建macOS版本 (.app) [跨平台]", "white")
    
    options.append(("5", "构建当前平台版本", "auto", "auto"))
    print_colored("   5. 构建当前平台版本 [自动选择]", "cyan")
    
    options.append(("6", "构建所有平台版本", "all", "all"))
    print_colored("   6. 构建所有平台版本 [需要时间]", "yellow")
    
    options.append(("0", "退出", "exit", "exit"))
    print_colored("   0. 退出", "white")
    
    return options

def get_recommended_script(platform_info):
    """获取当前平台推荐的构建脚本"""
    if platform_info["is_windows"]:
        return "build_exe.py", "Windows"
    elif platform_info["is_kylin"]:
        return "build_kylin.py", "麒麟Linux"
    elif platform_info["is_linux"]:
        return "build_linux.py", "Linux"
    elif platform_info["is_macos"]:
        return "build_macos.py", "macOS"
    else:
        return "build_exe.py", "Windows"  # 默认

def build_all_platforms():
    """构建所有平台版本"""
    all_scripts = [
        ("build_exe.py", "Windows"),
        ("build_linux.py", "Linux"),
        ("build_kylin.py", "麒麟Linux"),
        ("build_macos.py", "macOS"),
    ]
    
    print_colored("\n🔨 开始构建所有平台版本...", "yellow")
    
    results = []
    
    for script, platform_name in all_scripts:
        if os.path.exists(script):
            print_colored(f"\n{'='*40}", "cyan")
            success = run_build_script(script, platform_name)
            results.append((platform_name, success))
        else:
            print_colored(f"⚠️  跳过{platform_name}版本：缺少构建脚本 {script}", "yellow")
            results.append((platform_name, False))
    
    # 显示构建结果摘要
    print_colored(f"\n{'='*50}", "cyan")
    print_colored("🏁 所有平台构建完成！", "purple")
    print_colored(f"{'='*50}", "cyan")
    
    success_count = 0
    for platform_name, success in results:
        if success:
            print_colored(f"✅ {platform_name}: 构建成功", "green")
            success_count += 1
        else:
            print_colored(f"❌ {platform_name}: 构建失败", "red")
    
    print_colored(f"\n📊 构建统计: {success_count}/{len(results)} 个平台构建成功", "cyan")

def main():
    """主函数"""
    try:
        # 检测平台
        platform_info = detect_platform()
        show_platform_info(platform_info)
        
        # 检查构建脚本
        print_colored("\n🔍 检查构建脚本...", "blue")
        if not check_build_scripts():
            print_colored("\n❌ 请确保所有必要的构建脚本都存在", "red")
            return False
        
        # 交互式菜单
        while True:
            options = show_menu(platform_info)
            
            try:
                choice = input("\n请选择构建选项 (0-6): ").strip()
            except KeyboardInterrupt:
                print_colored("\n\n👋 构建已取消", "yellow")
                return False
            
            if choice == "0":
                print_colored("\n👋 再见！", "cyan")
                return True
            
            elif choice == "5":  # 自动选择当前平台
                script, platform_name = get_recommended_script(platform_info)
                if os.path.exists(script):
                    success = run_build_script(script, platform_name)
                    if success:
                        print_colored(f"\n🎉 {platform_name}版本构建完成！", "green")
                    else:
                        print_colored(f"\n💥 {platform_name}版本构建失败！", "red")
                else:
                    print_colored(f"\n❌ 构建脚本不存在: {script}", "red")
                
                input("\n按Enter键返回菜单...")
                continue
            
            elif choice == "6":  # 构建所有平台
                build_all_platforms()
                input("\n按Enter键返回菜单...")
                continue
            
            else:
                # 查找选择的选项
                selected_option = None
                for option in options:
                    if option[0] == choice:
                        selected_option = option
                        break
                
                if selected_option and selected_option[2] != "auto" and selected_option[2] != "all" and selected_option[2] != "exit":
                    script = selected_option[2]
                    platform_name = selected_option[3]
                    
                    if os.path.exists(script):
                        success = run_build_script(script, platform_name)
                        if success:
                            print_colored(f"\n🎉 {platform_name}版本构建完成！", "green")
                        else:
                            print_colored(f"\n💥 {platform_name}版本构建失败！", "red")
                    else:
                        print_colored(f"\n❌ 构建脚本不存在: {script}", "red")
                    
                    input("\n按Enter键返回菜单...")
                    continue
                else:
                    print_colored("❌ 无效的选择，请重新输入", "red")
                    continue
        
    except Exception as e:
        print_colored(f"\n❌ 程序执行出错: {str(e)}", "red")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print_colored("\n构建过程异常结束", "red")
        sys.exit(1)
    else:
        sys.exit(0)
