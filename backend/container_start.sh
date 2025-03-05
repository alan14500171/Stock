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

echo -e "${YELLOW}数据库连接信息:${NC}"
echo -e "主机: ${DB_HOST}"
echo -e "端口: ${DB_PORT}"
echo -e "用户: ${DB_USER}"
echo -e "数据库: ${DB_NAME}"
echo ""

# 显示网络信息
echo -e "${YELLOW}网络诊断信息:${NC}"
ip addr show
echo ""
echo -e "${YELLOW}网络路由:${NC}"
ip route
echo ""
echo -e "${YELLOW}尝试 ping 数据库主机:${NC}"
ping -c 3 ${DB_HOST} || echo -e "${RED}无法 ping 通数据库主机${NC}"
echo ""

# 等待数据库可用
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo -e "${YELLOW}尝试连接数据库 (${DB_HOST}:${DB_PORT}) 使用用户 ${DB_USER}...${NC}"
    
    if mysqladmin ping -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" --silent &> /dev/null; then
        echo -e "${GREEN}数据库连接成功!${NC}"
        break
    else
        # 显示详细的错误信息
        echo -e "${RED}连接失败，错误信息:${NC}"
        mysqladmin ping -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" 2>&1 || true
    fi
    
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo -e "${YELLOW}等待数据库连接... ($RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 2
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}错误: 无法连接到数据库 $DB_HOST:$DB_PORT${NC}"
        echo -e "${YELLOW}请检查数据库配置和网络连接${NC}"
        echo -e "${YELLOW}尝试使用 telnet 测试端口连接:${NC}"
        apt-get update && apt-get install -y telnet &> /dev/null
        telnet $DB_HOST $DB_PORT || echo -e "${RED}telnet 连接失败${NC}"
        exit 1
    fi
done

# 检查数据库是否存在
echo -e "${YELLOW}检查数据库 '$DB_NAME' 是否存在...${NC}"

# 尝试列出所有数据库
echo -e "${YELLOW}尝试列出所有数据库:${NC}"
DATABASES=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SHOW DATABASES;" 2>/dev/null)
if [ $? -ne 0 ]; then
    echo -e "${RED}无法列出数据库，可能是权限问题${NC}"
    echo -e "${YELLOW}尝试直接连接MySQL服务器:${NC}"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SELECT VERSION();" || echo -e "${RED}无法连接到MySQL服务器${NC}"
else
    echo "$DATABASES"
    
    # 检查数据库是否存在（不区分大小写）
    ACTUAL_DB_NAME=""
    while read -r line; do
        if [ -n "$line" ] && [ "$line" != "Database" ]; then
            if [ "${line,,}" = "${DB_NAME,,}" ]; then
                ACTUAL_DB_NAME="$line"
                break
            fi
        fi
    done <<< "$DATABASES"
    
    if [ -n "$ACTUAL_DB_NAME" ]; then
        echo -e "${GREEN}找到数据库: '$ACTUAL_DB_NAME'${NC}"
        
        # 如果实际数据库名称与配置中的不一致，提示用户
        if [ "$ACTUAL_DB_NAME" != "$DB_NAME" ]; then
            echo -e "${YELLOW}警告: 数据库名称大小写不一致${NC}"
            echo -e "配置中为: '$DB_NAME'"
            echo -e "实际为: '$ACTUAL_DB_NAME'"
            echo -e "${YELLOW}尝试使用实际数据库名称...${NC}"
            DB_NAME="$ACTUAL_DB_NAME"
        fi
    else
        echo -e "${RED}未找到数据库 '$DB_NAME'${NC}"
    fi
fi

# 尝试使用数据库
if ! mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "USE \`$DB_NAME\`;" &> /dev/null; then
    echo -e "${RED}错误: 无法使用数据库 '$DB_NAME'${NC}"
    echo -e "${YELLOW}可能的原因:${NC}"
    echo -e "1. 数据库 '$DB_NAME' 不存在"
    echo -e "2. 用户 '$DB_USER' 没有访问 '$DB_NAME' 的权限"
    echo -e "3. 数据库名称大小写不匹配"
    
    # 尝试创建数据库
    echo -e "${YELLOW}尝试创建数据库 '$DB_NAME':${NC}"
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" &> /dev/null; then
        echo -e "${GREEN}成功创建数据库 '$DB_NAME'${NC}"
    else
        echo -e "${RED}无法创建数据库，可能没有足够权限${NC}"
        echo -e "${YELLOW}请手动创建数据库或检查用户权限${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}成功连接到数据库 '$DB_NAME'${NC}"
    
    # 检查数据库中是否有表
    echo -e "${YELLOW}检查数据库中的表:${NC}"
    TABLES=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "USE \`$DB_NAME\`; SHOW TABLES;" 2>/dev/null)
    if [ -z "$TABLES" ] || [ $(echo "$TABLES" | wc -l) -le 1 ]; then
        echo -e "${YELLOW}数据库 '$DB_NAME' 中没有表或无法查看表${NC}"
    else
        echo -e "${GREEN}数据库 '$DB_NAME' 中有表:${NC}"
        echo "$TABLES"
    fi
fi

echo -e "${GREEN}数据库检查完成!${NC}"

# 检查用户权限
echo -e "${YELLOW}检查用户权限:${NC}"
GRANTS=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SHOW GRANTS FOR CURRENT_USER();" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$GRANTS"
    
    # 检查是否有对目标数据库的权限
    if echo "$GRANTS" | grep -i "ON \`$DB_NAME\`\." > /dev/null || echo "$GRANTS" | grep -i "ON \*\.\*" > /dev/null; then
        echo -e "${GREEN}用户 '$DB_USER' 有权限访问数据库 '$DB_NAME'${NC}"
    else
        echo -e "${YELLOW}警告: 用户 '$DB_USER' 可能没有足够的权限访问数据库 '$DB_NAME'${NC}"
    fi
else
    echo -e "${RED}无法获取用户权限信息${NC}"
fi

# 启动 Flask 应用
echo -e "${GREEN}启动 Flask 应用...${NC}"
cd /app
python main.py 