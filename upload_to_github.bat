@echo off
chcp 65001 > nul
title 魔力桌面助手 - 一键上传到GitHub

echo.
echo ==========================================
echo          魔力桌面助手
echo        一键上传到GitHub脚本
echo ==========================================
echo.

REM 检查是否已安装Git
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未检测到Git，请先安装Git！
    echo 下载地址：https://git-scm.com/
    pause
    exit /b 1
)

echo ✅ Git已安装

REM 检查是否已初始化Git仓库
if not exist ".git" (
    echo.
    echo 📁 初始化Git仓库...
    git init
    if errorlevel 1 (
        echo ❌ Git初始化失败！
        pause
        exit /b 1
    )
    echo ✅ Git仓库初始化成功
)

REM 设置用户信息（如果未设置）
for /f "tokens=*" %%i in ('git config --global user.name 2^>nul') do set git_user=%%i
for /f "tokens=*" %%i in ('git config --global user.email 2^>nul') do set git_email=%%i

if "%git_user%"=="" (
    echo.
    echo ⚙️  请设置Git用户名：
    set /p git_user=请输入您的GitHub用户名（如：moli-xia）: 
    git config --global user.name "%git_user%"
)

if "%git_email%"=="" (
    echo.
    echo ⚙️  请设置Git邮箱：
    set /p git_email=请输入您的GitHub邮箱: 
    git config --global user.email "%git_email%"
)

echo.
echo 👤 当前Git用户: %git_user%
echo 📧 当前Git邮箱: %git_email%

REM 检查GitHub仓库名
echo.
echo 📝 请确认GitHub仓库信息：
echo 推荐仓库名: magic-desktop-assistant
echo 您的GitHub用户名: moli-xia
echo.
set /p repo_name=请输入仓库名（直接回车使用推荐名称）: 
if "%repo_name%"=="" set repo_name=magic-desktop-assistant

echo.
echo 📋 即将上传到仓库: https://github.com/moli-xia/%repo_name%
echo.
set /p confirm=确认上传？(y/n): 
if /i not "%confirm%"=="y" (
    echo 取消上传
    pause
    exit /b 0
)

REM 创建.gitignore文件
echo.
echo 📝 创建.gitignore文件...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo share/python-wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo MANIFEST
echo.
echo # PyInstaller
echo *.manifest
echo *.spec
echo.
echo # 环境变量
echo .env
echo .venv
echo env/
echo venv/
echo ENV/
echo env.bak/
echo venv.bak/
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo *~
echo.
echo # 临时文件
echo *.tmp
echo *.log
echo *.cache
echo.
echo # 应用程序特定文件
echo wallpapers/
echo temp/
echo config/
echo *.ini
) > .gitignore

echo ✅ .gitignore文件创建成功

REM 添加所有文件
echo.
echo 📁 添加文件到Git...
git add .
if errorlevel 1 (
    echo ❌ 添加文件失败！
    pause
    exit /b 1
)
echo ✅ 文件添加成功

REM 提交更改
echo.
echo 💾 提交更改...
git commit -m "feat: 魔力桌面助手 v2.0 - 首次提交

- ✨ 智能壁纸更换和屏保功能
- 📅 完整的日历提醒系统
- 📰 每日资讯推送
- 🔧 系统托盘运行
- 📦 支持打包为exe文件
- 🎨 现代化UI设计"

if errorlevel 1 (
    echo ❌ 提交失败！
    pause
    exit /b 1
)
echo ✅ 提交成功

REM 设置主分支名为main
echo.
echo 🌿 设置主分支...
git branch -M main
echo ✅ 主分支设置完成

REM 添加远程仓库
echo.
echo 🔗 添加远程仓库...
git remote remove origin 2>nul
git remote add origin https://github.com/moli-xia/%repo_name%.git
if errorlevel 1 (
    echo ❌ 添加远程仓库失败！
    echo 请确保仓库名正确，且您有访问权限
    pause
    exit /b 1
)
echo ✅ 远程仓库添加成功

REM 推送到GitHub
echo.
echo 🚀 推送到GitHub...
echo 如果这是第一次推送，可能需要您登录GitHub
echo.
git push -u origin main
if errorlevel 1 (
    echo.
    echo ❌ 推送失败！可能的原因：
    echo 1. 远程仓库不存在，请先在GitHub创建仓库
    echo 2. 没有推送权限，请检查GitHub登录状态
    echo 3. 网络连接问题
    echo.
    echo 💡 解决方案：
    echo 1. 访问 https://github.com/new 创建新仓库
    echo 2. 仓库名填写: %repo_name%
    echo 3. 选择Public（公开）或Private（私有）
    echo 4. 不要勾选"Add a README file"
    echo 5. 创建完成后重新运行此脚本
    pause
    exit /b 1
)

echo.
echo ==========================================
echo              ✅ 上传成功！
echo ==========================================
echo.
echo 🎉 魔力桌面助手已成功上传到GitHub！
echo.
echo 📂 仓库地址: https://github.com/moli-xia/%repo_name%
echo 🌐 访问地址: https://github.com/moli-xia/%repo_name%
echo.
echo 🔄 后续更新代码时，只需运行：
echo    git add .
echo    git commit -m "更新说明"
echo    git push
echo.
echo 或者直接再次运行本脚本进行快速更新
echo.
pause
