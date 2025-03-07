#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}股票交易系统后端启动脚本${NC}"
echo "============================"
echo -e "${YELLOW}环境检查中...${NC}"

# 检查日志目录
if [ ! -d "/app/logs" ]; then
    echo -e "${YELLOW}创建日志目录...${NC}"
    mkdir -p /app/logs
    chmod 777 /app/logs
    echo -e "${GREEN}✓ 日志目录已创建${NC}"
fi

# 检查配置目录
if [ ! -d "/app/config" ]; then
    echo -e "${YELLOW}创建配置目录...${NC}"
    mkdir -p /app/config
    chmod 755 /app/config
    echo -e "${GREEN}✓ 配置目录已创建${NC}"
fi

# 检查配置文件
if [ ! -f "/app/config/db_config.py" ]; then
    echo -e "${YELLOW}创建数据库配置文件...${NC}"
    cp /app/config/db_config.example.py /app/config/db_config.py
    chmod 644 /app/config/db_config.py
    echo -e "${GREEN}✓ 配置文件已创建${NC}"
fi

# 数据库连接参数
DB_HOST=${DB_HOST:-"219.92.22.148"}
DB_PORT=${DB_PORT:-3306}
DB_USER=${DB_USER:-"root"}
DB_PASS=${DB_PASS:-"Zxc000123"}
DB_NAME=${DB_NAME:-"stock"}
MAX_RETRIES=${DB_CONNECT_RETRY:-10}
RETRY_DELAY=${DB_CONNECT_RETRY_DELAY:-5}

# 测试数据库连接函数
test_db_connection() {
    echo -e "${YELLOW}测试数据库连接...${NC}"
    python -c "
import pymysql
import sys
try:
    conn = pymysql.connect(
        host='$DB_HOST',
        port=$DB_PORT,
        user='$DB_USER',
        password='$DB_PASS',
        database='$DB_NAME',
        connect_timeout=5
    )
    print('${GREEN}✓ 数据库连接成功!${NC}')
    conn.close()
    sys.exit(0)
except Exception as e:
    print('${RED}✗ 数据库连接失败: %s${NC}' % str(e))
    sys.exit(1)
"
    return $?
}

# 尝试连接数据库
echo -e "${YELLOW}等待数据库服务准备就绪...${NC}"
for i in $(seq 1 $MAX_RETRIES); do
    if test_db_connection; then
        DB_CONNECTED=true
        break
    else
        echo -e "${YELLOW}重试中 ($i/$MAX_RETRIES)...${NC}"
        sleep $RETRY_DELAY
    fi
done

if [ "$DB_CONNECTED" != "true" ]; then
    echo -e "${RED}无法连接到数据库，继续启动但可能会失败${NC}"
    echo -e "${YELLOW}请检查以下内容:${NC}"
    echo "1. 数据库服务是否正在运行"
    echo "2. 数据库主机地址是否正确: $DB_HOST"
    echo "3. 数据库密码是否正确"
    echo "4. 网络连接是否正常"
    echo "5. 防火墙设置"
fi

# 检查依赖项是否安装
echo -e "${YELLOW}检查Python依赖...${NC}"
pip install -r requirements.txt

# 启动应用
echo -e "${GREEN}启动应用...${NC}"
exec python main.py 