#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}MySQL数据库创建工具${NC}"
echo "======================"

# 提示用户输入数据库配置
echo -e "${YELLOW}请输入MySQL数据库信息:${NC}"
read -p "数据库主机地址 (默认: localhost): " DB_HOST
DB_HOST=${DB_HOST:-"localhost"}

read -p "数据库端口 (默认: 3306): " DB_PORT
DB_PORT=${DB_PORT:-"3306"}

read -p "数据库管理员用户名 (默认: root): " DB_ADMIN
DB_ADMIN=${DB_ADMIN:-"root"}

read -p "数据库管理员密码: " DB_ADMIN_PASS

read -p "要创建的数据库名称 (默认: stock): " DB_NAME
DB_NAME=${DB_NAME:-"stock"}

read -p "数据库应用用户名 (默认: stockuser): " DB_USER
DB_USER=${DB_USER:-"stockuser"}

read -p "数据库应用用户密码 (默认: stockpassword): " DB_PASS
DB_PASS=${DB_PASS:-"stockpassword"}

echo -e "\n${YELLOW}测试数据库连接...${NC}"
# 测试管理员用户连接
if ! mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "SELECT 1" &>/dev/null; then
    echo -e "${RED}错误: 无法连接到数据库服务器${NC}"
    echo -e "${YELLOW}请检查主机地址、端口、用户名和密码是否正确${NC}"
    exit 1
else
    echo -e "${GREEN}✓ 数据库连接成功${NC}"
fi

# 检查数据库是否存在
echo -e "\n${YELLOW}检查数据库${NC} ${BLUE}$DB_NAME${NC} ${YELLOW}是否存在...${NC}"
if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "SHOW DATABASES LIKE '$DB_NAME'" | grep -q "$DB_NAME"; then
    echo -e "${GREEN}✓ 数据库 $DB_NAME 已存在${NC}"
    
    read -p "是否要删除并重新创建数据库? [y/N]: " RECREATE
    if [[ "$RECREATE" == "y" || "$RECREATE" == "Y" ]]; then
        echo -e "${YELLOW}删除数据库 $DB_NAME...${NC}"
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "DROP DATABASE \`$DB_NAME\`"
        echo -e "${GREEN}✓ 数据库已删除${NC}"
        NEED_CREATE=true
    else
        NEED_CREATE=false
    fi
else
    echo -e "${YELLOW}数据库 $DB_NAME 不存在${NC}"
    NEED_CREATE=true
fi

# 创建数据库
if [ "$NEED_CREATE" = true ]; then
    echo -e "\n${YELLOW}创建数据库 $DB_NAME...${NC}"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 数据库 $DB_NAME 创建成功${NC}"
    else
        echo -e "${RED}✗ 数据库创建失败${NC}"
        exit 1
    fi
fi

# 检查用户是否存在
echo -e "\n${YELLOW}检查用户 $DB_USER 是否存在...${NC}"
USER_EXISTS=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "SELECT COUNT(*) FROM mysql.user WHERE user = '$DB_USER'" | grep -v "COUNT")

if [ "$USER_EXISTS" -gt 0 ]; then
    echo -e "${YELLOW}用户 $DB_USER 已存在${NC}"
    echo -e "${YELLOW}更新用户密码并授予权限...${NC}"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "ALTER USER '$DB_USER'@'%' IDENTIFIED BY '$DB_PASS'"
else
    echo -e "${YELLOW}创建用户 $DB_USER...${NC}"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "CREATE USER '$DB_USER'@'%' IDENTIFIED BY '$DB_PASS'"
fi

# 授予权限
echo -e "\n${YELLOW}授予用户 $DB_USER 对数据库 $DB_NAME 的权限...${NC}"
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'%'"
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_ADMIN" -p"$DB_ADMIN_PASS" -e "FLUSH PRIVILEGES"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 权限授予成功${NC}"
else
    echo -e "${RED}✗ 权限授予失败${NC}"
    exit 1
fi

# 验证用户权限
echo -e "\n${YELLOW}验证 $DB_USER 用户权限...${NC}"
if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SHOW DATABASES" | grep -q "$DB_NAME"; then
    echo -e "${GREEN}✓ 用户验证成功${NC}"
else
    echo -e "${RED}✗ 用户验证失败${NC}"
    echo -e "${YELLOW}请手动检查用户权限${NC}"
fi

# 更新db_config.py文件
echo -e "\n${YELLOW}是否要更新后端数据库配置文件? [y/N]:${NC}"
read -p "" UPDATE_CONFIG
if [[ "$UPDATE_CONFIG" == "y" || "$UPDATE_CONFIG" == "Y" ]]; then
    if [ -f "./config/db_config.py" ]; then
        # 备份配置文件
        cp ./config/db_config.py ./config/db_config.py.bak
        
        # 更新配置
        sed -i "s/'host':.*,/'host': '$DB_HOST',/g" ./config/db_config.py
        sed -i "s/'port':.*,/'port': $DB_PORT,/g" ./config/db_config.py
        sed -i "s/'user':.*,/'user': '$DB_USER',/g" ./config/db_config.py
        sed -i "s/'password':.*,/'password': '$DB_PASS',/g" ./config/db_config.py
        sed -i "s/'db':.*,/'db': '$DB_NAME',/g" ./config/db_config.py
        
        echo -e "${GREEN}✓ 数据库配置已更新${NC}"
    else
        echo -e "${RED}错误: 找不到配置文件 config/db_config.py${NC}"
        echo -e "${YELLOW}请确保在backend目录下运行此脚本${NC}"
    fi
fi

echo -e "\n${GREEN}数据库设置完成!${NC}"
echo -e "${YELLOW}请使用以下信息配置您的应用:${NC}"
echo -e "  数据库主机: ${BLUE}$DB_HOST${NC}"
echo -e "  数据库端口: ${BLUE}$DB_PORT${NC}"
echo -e "  数据库名称: ${BLUE}$DB_NAME${NC}"
echo -e "  数据库用户: ${BLUE}$DB_USER${NC}"
echo -e "  数据库密码: ${BLUE}$DB_PASS${NC}"

echo -e "\n${YELLOW}重要提示:${NC}"
echo -e "1. 重启后端服务以应用新配置:"
echo -e "   ${BLUE}docker-compose restart stock-backend${NC}"
echo -e "2. 查看后端日志确认连接成功:"
echo -e "   ${BLUE}docker-compose logs -f stock-backend${NC}" 