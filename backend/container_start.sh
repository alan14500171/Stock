#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}启动股票管理系统后端服务...${NC}"

# 检查配置文件是否存在
if [ ! -f "/app/config/db_config.py" ]; then
    echo -e "${RED}错误: 数据库配置文件不存在!${NC}"
    echo -e "${YELLOW}请复制 config/db_config.example.py 到 config/db_config.py 并修改配置${NC}"
    exit 1
fi

# 从配置文件中提取数据库连接信息
DB_HOST=$(grep -o "'host': '[^']*'" /app/config/db_config.py | grep -o "'[^']*'" | grep -o "[^']*" | tail -1)
DB_PORT=$(grep -o "'port': [0-9]*" /app/config/db_config.py | grep -o "[0-9]*" | tail -1)
DB_USER=$(grep -o "'user': '[^']*'" /app/config/db_config.py | grep -o "'[^']*'" | grep -o "[^']*" | tail -1)
DB_PASS=$(grep -o "'password': '[^']*'" /app/config/db_config.py | grep -o "'[^']*'" | grep -o "[^']*" | tail -1)
DB_NAME=$(grep -o "'db': '[^']*'" /app/config/db_config.py | grep -o "'[^']*'" | grep -o "[^']*" | tail -1)

echo -e "${YELLOW}检查数据库连接 (${DB_HOST}:${DB_PORT})...${NC}"

# 等待数据库可用
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if mysqladmin ping -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" --silent &> /dev/null; then
        echo -e "${GREEN}数据库连接成功!${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo -e "${YELLOW}等待数据库连接... ($RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 2
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}错误: 无法连接到数据库 $DB_HOST:$DB_PORT${NC}"
        echo -e "${YELLOW}请检查数据库配置和网络连接${NC}"
        exit 1
    fi
done

# 检查数据库是否存在
if ! mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "USE $DB_NAME;" &> /dev/null; then
    echo -e "${RED}错误: 数据库 '$DB_NAME' 不存在${NC}"
    echo -e "${YELLOW}请确保数据库已创建${NC}"
    exit 1
fi

echo -e "${GREEN}数据库 '$DB_NAME' 连接成功!${NC}"

# 启动 Flask 应用
echo -e "${GREEN}启动 Flask 应用...${NC}"
cd /app
python main.py 