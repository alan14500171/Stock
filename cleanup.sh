#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}项目文件清理工具${NC}"
echo "======================"

# 确认是否继续
echo -e "${YELLOW}警告: 此脚本将删除项目中的冗余文件${NC}"
read -p "是否继续? [y/N]: " CONTINUE
if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 0
fi

# 后端清理
echo -e "\n${YELLOW}清理后端文件...${NC}"

# 删除后端临时脚本和冗余Docker文件
BACKEND_FILES_TO_REMOVE=(
    "backend/fix_db_config.py"
    "backend/modify_main_config.py"
    "backend/db_repair.sh"
    "backend/db-fix.sh"
    "backend/check_db.py"
    "backend/cookies.txt"
    "backend/api_response.json"
    "backend/DEPLOYMENT_TROUBLESHOOTING.md"
    "backend/README_SYNOLOGY.md"
)

for file in "${BACKEND_FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo -e "删除文件: ${RED}$file${NC}"
        rm "$file"
    fi
done

# 清理scripts目录中的冗余脚本
echo -e "\n${YELLOW}清理后端scripts目录中的冗余脚本...${NC}"

# 要保留的核心脚本（这些是必要的管理和维护脚本）
SCRIPTS_TO_KEEP=(
    "create_database.py"
    "reset_admin_password.py"
    "init_rbac.py"
    "create_rbac_tables.py"
)

# 创建临时目录保存要保留的脚本
mkdir -p backend/scripts_temp
for script in "${SCRIPTS_TO_KEEP[@]}"; do
    if [ -f "backend/scripts/$script" ]; then
        echo -e "保留脚本: ${GREEN}backend/scripts/$script${NC}"
        cp "backend/scripts/$script" "backend/scripts_temp/"
    fi
done

# 移动README.md如果存在
if [ -f "backend/scripts/README.md" ]; then
    cp "backend/scripts/README.md" "backend/scripts_temp/"
fi

# 删除整个scripts目录并重命名临时目录
rm -rf backend/scripts
mv backend/scripts_temp backend/scripts
echo -e "${GREEN}✓ 已清理scripts目录，仅保留核心管理脚本${NC}"

# 前端清理
echo -e "\n${YELLOW}清理前端文件...${NC}"

# 删除前端临时脚本和冗余Docker文件
FRONTEND_FILES_TO_REMOVE=(
    # 调试和修复脚本
    "frontend/debug-spa.sh"
    "frontend/inject-api-url.sh"
    "frontend/quick-fix.sh"
    "frontend/build-for-nas.sh"
    "frontend/fix-nas-deploy.sh"
    "frontend/minimal-deploy.sh"
    "frontend/pre-deploy.sh"
    "frontend/synology-deploy.sh"
    "frontend/synology-quick-deploy.sh"
    "frontend/run-vite.js"
    "frontend/nas-deploy-simple.sh"
    "frontend/nas-one-step.sh"
    "frontend/deploy.sh"
    "frontend/start.sh"
    
    # 文档文件
    "frontend/README_SYNOLOGY.md"
    "frontend/README.synology.md"
    "frontend/nas-guide.md"
    "frontend/NAS-DEPLOY-GUIDE.md"
    "frontend/TROUBLESHOOTING.md"
    "frontend/DEPLOYMENT.md"
    
    # 冗余Docker配置
    "frontend/Dockerfile.ultra-simple"
    "frontend/Dockerfile.simple"
    "frontend/Dockerfile.nginx"
    "frontend/Dockerfile.synology"
    "frontend/simplified-dockerfile"
    "frontend/docker-compose.simple.yml"
    "frontend/docker-compose.nginx.yml"
    "frontend/docker-compose.synology.yml"
    "frontend/docker-compose.ultra-simple.yml"
    "frontend/docker-compose.improved.yml"
    "frontend/nginx-quick-fix.conf"
    "frontend/nginx-simple.conf"
)

for file in "${FRONTEND_FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo -e "删除文件: ${RED}$file${NC}"
        rm "$file"
    fi
done

# 删除根目录多余文件
echo -e "\n${YELLOW}清理根目录文件...${NC}"

ROOT_FILES_TO_REMOVE=(
    "add_profit_stats_permission.py"
    "check_all_permissions.py"
    "check_permissions.py"
    "check_port.py"
    "cookies.txt"
    "database.sql"
    "db_connection_report.md"
)

for file in "${ROOT_FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        echo -e "删除文件: ${RED}$file${NC}"
        rm "$file"
    fi
done

# 更新主docker-compose.yml文件
echo -e "\n${YELLOW}更新主docker-compose.yml文件...${NC}"
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: ./docker/Dockerfile
    restart: unless-stopped
    ports:
      - "9099:9099"
    volumes:
      - ./backend:/app
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
      - TZ=Asia/Shanghai
    network_mode: "host"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9099/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    mem_limit: 1G

  frontend:
    build:
      context: ./frontend
      dockerfile: ./docker/Dockerfile
    restart: unless-stopped
    ports:
      - "9009:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./frontend/docker/nginx.conf:/etc/nginx/conf.d/default.conf
    environment:
      - TZ=Asia/Shanghai
    depends_on:
      - backend
    network_mode: "host"
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    mem_limit: 512M

  db:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=stock
      - MYSQL_USER=stockuser
      - MYSQL_PASSWORD=stockpassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backend/docker/mysql.cnf:/etc/mysql/conf.d/mysql.cnf
    mem_limit: 512M

volumes:
  mysql_data:
EOF

# 更新.gitignore
echo -e "\n${YELLOW}更新.gitignore文件...${NC}"
cat >> .gitignore << 'EOF'

# 日志文件
logs/
*.log

# 环境文件
.env
.env.*
!.env.example

# 虚拟环境
.venv/
.venv_py312/

# 构建文件
frontend/dist/
frontend/node_modules/

# IDE文件
.vscode/
.idea/
.DS_Store
EOF

echo -e "\n${GREEN}清理完成!${NC}"
echo -e "${YELLOW}项目结构已优化，所有Docker相关文件已移至docker文件夹${NC}"
echo -e "使用以下命令重新部署:"
echo -e "${BLUE}docker-compose up -d --build${NC}" 