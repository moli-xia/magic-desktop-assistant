#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo
echo "=========================================="
echo "         魔力桌面助手"
echo "       一键上传到GitHub脚本"
echo "=========================================="
echo

# 检查是否已安装Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ 错误：未检测到Git，请先安装Git！${NC}"
    echo "Ubuntu/Debian: sudo apt install git"
    echo "CentOS/RHEL: sudo yum install git"
    echo "macOS: brew install git"
    exit 1
fi

echo -e "${GREEN}✅ Git已安装${NC}"

# 检查是否已初始化Git仓库
if [ ! -d ".git" ]; then
    echo
    echo -e "${BLUE}📁 初始化Git仓库...${NC}"
    git init
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Git初始化失败！${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Git仓库初始化成功${NC}"
fi

# 设置用户信息（如果未设置）
git_user=$(git config --global user.name 2>/dev/null)
git_email=$(git config --global user.email 2>/dev/null)

if [ -z "$git_user" ]; then
    echo
    echo -e "${YELLOW}⚙️  请设置Git用户名：${NC}"
    read -p "请输入您的GitHub用户名（如：moli-xia）: " git_user
    git config --global user.name "$git_user"
fi

if [ -z "$git_email" ]; then
    echo
    echo -e "${YELLOW}⚙️  请设置Git邮箱：${NC}"
    read -p "请输入您的GitHub邮箱: " git_email
    git config --global user.email "$git_email"
fi

echo
echo -e "${BLUE}👤 当前Git用户: $git_user${NC}"
echo -e "${BLUE}📧 当前Git邮箱: $git_email${NC}"

# 检查GitHub仓库名
echo
echo -e "${YELLOW}📝 请确认GitHub仓库信息：${NC}"
echo "推荐仓库名: magic-desktop-assistant"
echo "您的GitHub用户名: moli-xia"
echo
read -p "请输入仓库名（直接回车使用推荐名称）: " repo_name
if [ -z "$repo_name" ]; then
    repo_name="magic-desktop-assistant"
fi

echo
echo -e "${BLUE}📋 即将上传到仓库: https://github.com/moli-xia/$repo_name${NC}"
echo
read -p "确认上传？(y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "取消上传"
    exit 0
fi

# 创建.gitignore文件
echo
echo -e "${BLUE}📝 创建.gitignore文件...${NC}"
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# 环境变量
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 临时文件
*.tmp
*.log
*.cache

# 应用程序特定文件
wallpapers/
temp/
config/
*.ini
EOF

echo -e "${GREEN}✅ .gitignore文件创建成功${NC}"

# 添加所有文件
echo
echo -e "${BLUE}📁 添加文件到Git...${NC}"
git add .
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 添加文件失败！${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 文件添加成功${NC}"

# 提交更改
echo
echo -e "${BLUE}💾 提交更改...${NC}"
git commit -m "feat: 魔力桌面助手 v2.0 - 首次提交

- ✨ 智能壁纸更换和屏保功能
- 📅 完整的日历提醒系统
- 📰 每日资讯推送
- 🔧 系统托盘运行
- 📦 支持打包为exe文件
- 🎨 现代化UI设计"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 提交失败！${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 提交成功${NC}"

# 设置主分支名为main
echo
echo -e "${BLUE}🌿 设置主分支...${NC}"
git branch -M main
echo -e "${GREEN}✅ 主分支设置完成${NC}"

# 添加远程仓库
echo
echo -e "${BLUE}🔗 添加远程仓库...${NC}"
git remote remove origin 2>/dev/null
git remote add origin https://github.com/moli-xia/$repo_name.git
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 添加远程仓库失败！${NC}"
    echo "请确保仓库名正确，且您有访问权限"
    exit 1
fi
echo -e "${GREEN}✅ 远程仓库添加成功${NC}"

# 推送到GitHub
echo
echo -e "${BLUE}🚀 推送到GitHub...${NC}"
echo "如果这是第一次推送，可能需要您登录GitHub"
echo
git push -u origin main
if [ $? -ne 0 ]; then
    echo
    echo -e "${RED}❌ 推送失败！可能的原因：${NC}"
    echo "1. 远程仓库不存在，请先在GitHub创建仓库"
    echo "2. 没有推送权限，请检查GitHub登录状态"
    echo "3. 网络连接问题"
    echo
    echo -e "${YELLOW}💡 解决方案：${NC}"
    echo "1. 访问 https://github.com/new 创建新仓库"
    echo "2. 仓库名填写: $repo_name"
    echo "3. 选择Public（公开）或Private（私有）"
    echo "4. 不要勾选\"Add a README file\""
    echo "5. 创建完成后重新运行此脚本"
    exit 1
fi

echo
echo "=========================================="
echo -e "${GREEN}             ✅ 上传成功！${NC}"
echo "=========================================="
echo
echo -e "${GREEN}🎉 魔力桌面助手已成功上传到GitHub！${NC}"
echo
echo -e "${BLUE}📂 仓库地址: https://github.com/moli-xia/$repo_name${NC}"
echo -e "${BLUE}🌐 访问地址: https://github.com/moli-xia/$repo_name${NC}"
echo
echo -e "${YELLOW}🔄 后续更新代码时，只需运行：${NC}"
echo "   git add ."
echo "   git commit -m \"更新说明\""
echo "   git push"
echo
echo "或者直接再次运行本脚本进行快速更新"
echo
