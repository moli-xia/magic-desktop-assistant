#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
魔力桌面助手 - macOS平台自动化打包脚本
将项目打包为macOS平台的.app应用程序包
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

def check_macos_requirements():
    """检查macOS构建环境"""
    print_colored("\n🔍 检查macOS构建环境...", "yellow")
    
    # 检查操作系统
    if not sys.platform == 'darwin':
        print_colored("⚠️  警告: 当前不在macOS环境中，可能无法正确构建macOS版本", "yellow")
        print_colored("建议在macOS系统中进行构建以获得最佳兼容性", "yellow")
    
    # 显示系统信息
    try:
        macos_version = platform.mac_ver()[0]
        print(f"macOS版本: {macos_version}")
        print(f"架构: {platform.machine()}")
        print(f"处理器: {platform.processor()}")
        
        # 检查macOS版本
        if macos_version:
            version_parts = macos_version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            
            if major < 10 or (major == 10 and minor < 14):
                print_colored("⚠️  警告: macOS版本过低，建议10.14(Mojave)或更高版本", "yellow")
            else:
                print_colored(f"✅ macOS版本符合要求: {macos_version}", "green")
                
    except Exception as e:
        print_colored(f"⚠️  无法获取macOS版本信息: {e}", "yellow")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print_colored("❌ Python版本过低，需要3.8或更高版本", "red")
        return False
    
    # 检查必要文件
    required_files = ["main.py", "app_icon.ico", "requirements.txt", "魔力桌面助手_macos.spec"]
    for file in required_files:
        if not os.path.exists(file):
            print_colored(f"❌ 缺少必要文件: {file}", "red")
            return False
        else:
            print_colored(f"✅ 找到文件: {file}", "green")
    
    # 检查Xcode命令行工具
    print_colored("\n🔧 检查开发工具...", "blue")
    try:
        result = subprocess.run("xcode-select -p", shell=True, capture_output=True)
        if result.returncode == 0:
            print_colored("✅ Xcode命令行工具已安装", "green")
        else:
            print_colored("⚠️  Xcode命令行工具未安装，某些功能可能受限", "yellow")
            print_colored("可运行: xcode-select --install 进行安装", "cyan")
    except:
        print_colored("? 无法检查Xcode命令行工具状态", "yellow")
    
    # 检查Homebrew（可选）
    try:
        result = subprocess.run("brew --version", shell=True, capture_output=True)
        if result.returncode == 0:
            print_colored("✅ Homebrew已安装", "green")
        else:
            print_colored("⚠️  Homebrew未安装，建议安装以便管理依赖", "yellow")
    except:
        print_colored("? 无法检查Homebrew状态", "yellow")
    
    return True

def install_macos_dependencies():
    """安装macOS依赖包"""
    print_colored("\n📦 安装macOS依赖...", "yellow")
    
    # 升级pip
    if not run_command("python3 -m pip install --upgrade pip", "升级pip"):
        print_colored("⚠️  pip升级失败，继续尝试安装依赖", "yellow")
    
    # 安装requirements.txt中的依赖
    if not run_command("python3 -m pip install -r requirements.txt", "安装项目依赖"):
        return False
    
    # 安装PyInstaller
    if not run_command("python3 -m pip install pyinstaller", "安装PyInstaller"):
        return False
    
    # 安装macOS特定的依赖
    macos_deps = [
        "pyobjc-core",      # macOS系统集成
        "pyobjc-framework-Cocoa",  # Cocoa框架
        "pyobjc-framework-Quartz", # 图形处理
    ]
    
    print_colored("\n🍎 安装macOS特定依赖...", "blue")
    for dep in macos_deps:
        if not run_command(f"python3 -m pip install {dep}", f"安装{dep}"):
            print_colored(f"⚠️  {dep} 安装失败，继续安装其他依赖", "yellow")
        
    return True

def clean_macos_build_dirs():
    """清理macOS构建目录"""
    print_colored("\n🧹 清理macOS构建目录...", "yellow")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print_colored(f"✅ 已删除目录: {dir_name}", "green")
            except Exception as e:
                print_colored(f"⚠️  删除目录失败 {dir_name}: {str(e)}", "yellow")

def build_macos_executable():
    """构建macOS应用程序包"""
    print_colored("\n🔨 开始构建macOS应用程序包...", "yellow")
    
    # 使用macOS专用的spec文件
    spec_file = "魔力桌面助手_macos.spec"
    
    build_command = f"python3 -m pyinstaller {spec_file}"
    
    print_colored("构建命令:", "cyan")
    print(build_command)
    print_colored("\n⏳ 正在构建，请稍候...", "yellow")
    
    return run_command(build_command, "构建macOS应用程序包")

def create_macos_dmg():
    """创建macOS DMG安装包（可选）"""
    print_colored("\n💿 尝试创建DMG安装包...", "yellow")
    
    app_path = "dist/魔力桌面助手.app"
    dmg_path = "dist/魔力桌面助手_v2.0.dmg"
    
    if not os.path.exists(app_path):
        print_colored("⚠️  .app文件不存在，跳过DMG创建", "yellow")
        return False
    
    # 创建临时挂载点
    temp_dmg = "dist/temp.dmg"
    mount_point = "dist/temp_mount"
    
    try:
        # 创建临时DMG
        dmg_size = "200m"  # 调整大小根据需要
        create_cmd = f"hdiutil create -size {dmg_size} -fs HFS+ -volname '魔力桌面助手' '{temp_dmg}'"
        
        if not run_command(create_cmd, "创建临时DMG"):
            return False
        
        # 挂载DMG
        mount_cmd = f"hdiutil attach '{temp_dmg}' -mountpoint '{mount_point}'"
        if not run_command(mount_cmd, "挂载临时DMG"):
            return False
        
        # 复制应用到DMG
        copy_cmd = f"cp -R '{app_path}' '{mount_point}/'"
        if not run_command(copy_cmd, "复制应用到DMG"):
            run_command(f"hdiutil detach '{mount_point}'", "卸载DMG")
            return False
        
        # 创建应用程序文件夹的符号链接
        link_cmd = f"ln -s /Applications '{mount_point}/Applications'"
        run_command(link_cmd, "创建Applications链接")
        
        # 卸载DMG
        detach_cmd = f"hdiutil detach '{mount_point}'"
        if not run_command(detach_cmd, "卸载DMG"):
            print_colored("⚠️  DMG卸载失败，但继续创建最终DMG", "yellow")
        
        # 转换为只读压缩DMG
        convert_cmd = f"hdiutil convert '{temp_dmg}' -format UDZO -o '{dmg_path}'"
        if run_command(convert_cmd, "创建最终DMG"):
            print_colored(f"✅ DMG安装包创建成功: {dmg_path}", "green")
            # 清理临时文件
            if os.path.exists(temp_dmg):
                os.remove(temp_dmg)
            return True
        else:
            return False
            
    except Exception as e:
        print_colored(f"❌ 创建DMG时出错: {str(e)}", "red")
        # 清理临时文件
        try:
            if os.path.exists(mount_point):
                run_command(f"hdiutil detach '{mount_point}'", "清理挂载点")
            if os.path.exists(temp_dmg):
                os.remove(temp_dmg)
        except:
            pass
        return False

def create_macos_launcher():
    """创建macOS启动脚本"""
    print_colored("\n📝 创建macOS启动脚本...", "yellow")
    
    # Shell启动脚本
    shell_script = '''#!/bin/bash
# 魔力桌面助手 macOS 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR/魔力桌面助手.app"

echo "==========================================="
echo "        魔力桌面助手 v2.0 macOS版"
echo "      专为macOS系统优化设计"
echo "==========================================="
echo ""
echo "🚀 正在启动魔力桌面助手..."
echo ""

if [ -d "$APP_PATH" ]; then
    open "$APP_PATH"
    echo "✅ 应用程序已启动"
else
    echo "❌ 找不到应用程序包: $APP_PATH"
    echo "请确保应用程序包存在"
    read -p "按Enter键退出..."
fi
'''
    
    # AppleScript启动脚本
    applescript = '''tell application "Finder"
    set appPath to (container of (path to me) as string) & "魔力桌面助手.app"
    
    try
        open application file appPath
        display notification "魔力桌面助手已启动" with title "启动成功"
    on error
        display alert "启动失败" message "无法找到魔力桌面助手应用程序" as critical
    end try
end tell'''
    
    try:
        # 创建shell启动脚本
        with open("dist/启动魔力桌面助手.sh", "w", encoding="utf-8") as f:
            f.write(shell_script)
        
        # 给shell脚本添加执行权限
        os.chmod("dist/启动魔力桌面助手.sh", 0o755)
        print_colored("✅ macOS启动脚本创建成功", "green")
        
        # 创建AppleScript文件
        with open("dist/启动魔力桌面助手.applescript", "w", encoding="utf-8") as f:
            f.write(applescript)
        print_colored("✅ AppleScript启动脚本创建成功", "green")
        
        return True
    except Exception as e:
        print_colored(f"❌ 创建macOS启动脚本失败: {str(e)}", "red")
        return False

def create_macos_instructions():
    """创建macOS使用说明文件"""
    print_colored("\n📖 创建macOS使用说明...", "yellow")
    
    instructions = '''魔力桌面助手 v2.0 - macOS版使用说明
===========================================

🎯 软件介绍
魔力桌面助手是一款功能丰富的桌面工具，专为macOS系统优化，集成了：
- 智能壁纸更换和屏保功能
- 完整的日历提醒系统  
- 每日资讯推送
- 菜单栏运行
- macOS深度集成

🚀 快速开始

方法1: 直接运行应用程序
1. 双击"魔力桌面助手.app"启动
2. 应用程序会出现在Dock中

方法2: 使用启动脚本
1. 双击"启动魔力桌面助手.sh"
2. 或者双击"启动魔力桌面助手.applescript"

方法3: 安装到应用程序文件夹
1. 将"魔力桌面助手.app"拖拽到"应用程序"文件夹
2. 在Launchpad中找到应用程序启动

🔧 系统要求
- macOS 10.14 (Mojave) 或更高版本
- 支持Intel和Apple Silicon (M1/M2)芯片
- 至少500MB可用磁盘空间
- 网络连接（用于获取资讯和壁纸）

📦 首次运行设置

1. 安全设置
   如果遇到"无法打开，因为它来自身份不明的开发者"：
   - 右键点击应用程序，选择"打开"
   - 或在"系统偏好设置" > "安全性与隐私"中允许
   - 也可以运行: sudo spctl --master-disable（不推荐）

2. 权限设置
   应用程序可能需要以下权限：
   - 通知权限（用于提醒功能）
   - 网络权限（用于下载壁纸和资讯）
   - 文件访问权限（用于壁纸管理）

💡 主要功能

📅 日历提醒
- 支持添加各种提醒事项
- 多种重复模式：每天、每周、每月、每年
- 集成macOS通知中心
- 支持iCloud日历同步

🖼️ 壁纸管理
- 自动下载高质量壁纸
- 定时更换桌面背景
- 支持Retina显示屏
- 适配Dark Mode/Light Mode

📰 信息推送
- 每日新闻资讯
- 天气信息
- 热搜话题
- 通过通知中心推送

🔧 系统功能
- 在菜单栏显示图标
- 支持快捷键操作
- 单实例运行保护
- 登录时自动启动

🆘 常见问题

Q: 应用程序无法启动？
A: 1. 检查macOS版本是否符合要求（10.14+）
   2. 右键选择"打开"绕过安全检查
   3. 在"安全性与隐私"中允许应用运行
   4. 检查Gatekeeper设置

Q: 提醒功能不工作？
A: 1. 在"系统偏好设置" > "通知"中启用应用通知
   2. 确保"勿扰模式"已关闭
   3. 检查通知中心设置

Q: 壁纸无法下载？
A: 1. 检查网络连接
   2. 确认防火墙设置允许应用联网
   3. 可能需要配置代理

Q: 菜单栏图标不显示？
A: 1. 检查菜单栏是否自动隐藏
   2. 重启应用程序
   3. 检查"系统偏好设置" > "Dock与菜单栏"设置

Q: 在Apple Silicon Mac上运行？
A: 应用程序支持原生Apple Silicon，如果遇到问题：
   1. 确保下载了正确的版本
   2. 重置应用程序权限
   3. 尝试Rosetta 2兼容模式

🍎 macOS特殊功能

1. Spotlight集成
   - 应用程序会出现在Spotlight搜索中
   - 支持中文和英文搜索

2. 手势支持
   - 支持触控板手势操作
   - Force Touch快捷操作

3. Dark Mode适配
   - 自动适配系统外观模式
   - 壁纸会根据模式调整

4. 多屏幕支持
   - 支持多显示器壁纸管理
   - 适配不同分辨率

📱 同步功能
- 支持iCloud备份提醒数据
- 可与iOS设备同步（未来版本）

🔒 隐私安全
- 本地数据存储，不上传个人信息
- 遵循苹果隐私指导原则
- 网络请求仅用于获取公开资讯

📞 技术支持
如遇问题请访问项目主页：
https://github.com/moli-xia/magic-desktop-assistant

macOS专项支持：
- Apple开发者论坛
- macOS应用商店用户反馈

版本：v2.0 macOS专版
更新日期：2024年
macOS系统深度集成版本
'''
    
    try:
        with open("dist/macOS使用说明.txt", "w", encoding="utf-8") as f:
            f.write(instructions)
        print_colored("✅ macOS使用说明创建成功", "green")
        return True
    except Exception as e:
        print_colored(f"❌ 创建macOS使用说明失败: {str(e)}", "red")
        return False

def verify_macos_build():
    """验证macOS构建结果"""
    print_colored("\n🔍 验证macOS构建结果...", "yellow")
    
    app_path = "dist/魔力桌面助手.app"
    if not os.path.exists(app_path):
        print_colored("❌ macOS应用程序包未生成", "red")
        return False
    
    print_colored(f"✅ macOS应用程序包已生成", "green")
    print_colored(f"📁 应用路径: {app_path}", "cyan")
    
    # 检查应用程序包结构
    try:
        contents_path = os.path.join(app_path, "Contents")
        if os.path.exists(contents_path):
            print_colored("✅ 应用程序包结构正确", "green")
            
            # 检查Info.plist
            plist_path = os.path.join(contents_path, "Info.plist")
            if os.path.exists(plist_path):
                print_colored("✅ Info.plist文件存在", "green")
            
            # 检查可执行文件
            macos_path = os.path.join(contents_path, "MacOS")
            if os.path.exists(macos_path):
                executables = os.listdir(macos_path)
                if executables:
                    print_colored(f"✅ 可执行文件: {executables[0]}", "green")
                    
                    # 检查文件权限
                    exe_path = os.path.join(macos_path, executables[0])
                    if os.access(exe_path, os.X_OK):
                        print_colored("✅ 可执行文件具有执行权限", "green")
                    else:
                        print_colored("⚠️  可执行文件缺少执行权限", "yellow")
        else:
            print_colored("⚠️  应用程序包结构异常", "yellow")
            
    except Exception as e:
        print_colored(f"⚠️  检查应用程序包时出错: {str(e)}", "yellow")
    
    # 计算应用程序包大小
    try:
        result = subprocess.run(f"du -sh '{app_path}'", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            size = result.stdout.split()[0]
            print_colored(f"📊 应用程序包大小: {size}", "cyan")
    except:
        pass
    
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
    print_colored("     魔力桌面助手 - macOS平台自动化打包工具", "purple")
    print_colored("="*55, "cyan")
    
    start_time = time.time()
    
    try:
        # 检查环境
        if not check_macos_requirements():
            print_colored("\n❌ 环境检查失败，请解决上述问题后重试", "red")
            return False
        
        # 安装依赖
        if not install_macos_dependencies():
            print_colored("\n❌ 依赖安装失败", "red")
            return False
        
        # 清理构建目录
        clean_macos_build_dirs()
        
        # 构建应用程序包
        if not build_macos_executable():
            print_colored("\n❌ 构建失败", "red")
            return False
        
        # 创建额外文件
        create_macos_launcher()
        create_macos_instructions()
        
        # 尝试创建DMG（可选）
        create_macos_dmg()
        
        # 验证结果
        if not verify_macos_build():
            return False
        
        # 构建成功
        end_time = time.time()
        duration = end_time - start_time
        
        print_colored("\n" + "="*55, "green")
        print_colored("        🎉 macOS构建成功完成！", "green")
        print_colored("="*55, "green")
        print_colored(f"⏱️  总耗时: {duration:.1f} 秒", "cyan")
        print_colored(f"📁 输出目录: dist/", "cyan")
        print_colored(f"🚀 应用程序包: dist/魔力桌面助手.app", "cyan")
        print_colored(f"📋 启动脚本: dist/启动魔力桌面助手.sh", "cyan")
        print_colored(f"🍎 AppleScript: dist/启动魔力桌面助手.applescript", "cyan")
        print_colored(f"📖 使用说明: dist/macOS使用说明.txt", "cyan")
        
        # 检查DMG是否创建成功
        dmg_path = "dist/魔力桌面助手_v2.0.dmg"
        if os.path.exists(dmg_path):
            print_colored(f"💿 DMG安装包: {dmg_path}", "cyan")
        
        print_colored("\n💡 接下来你可以:", "yellow")
        print_colored("   1. 双击运行: 魔力桌面助手.app", "white")
        print_colored("   2. 拖拽到应用程序文件夹安装", "white")
        print_colored("   3. 分发DMG安装包给其他macOS用户", "white")
        print_colored("   4. 提交到Mac App Store审核", "white")
        
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
