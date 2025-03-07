FROM node:16-alpine

WORKDIR /app

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 增加Node.js内存限制
ENV NODE_OPTIONS="--max-old-space-size=4096"

# 安装必要的系统依赖
RUN apk add --no-cache python3 make g++

# 显示Node.js和npm版本
RUN node -v && npm -v

COPY package*.json ./

# 安装依赖，使用--legacy-peer-deps解决潜在的依赖冲突
RUN npm install --legacy-peer-deps

# 全局安装vite
RUN npm install -g vite

COPY . .

# 列出node_modules/.bin目录内容以进行调试
RUN ls -la node_modules/.bin/

# 检查vite可执行文件
RUN cat node_modules/.bin/vite || echo "无法读取vite文件"

# 尝试修复符号链接
RUN cd node_modules/.bin && \
    rm -f vite && \
    ln -s ../vite/bin/vite.js vite && \
    chmod +x vite

# 添加错误处理，如果构建失败则输出详细信息
RUN NODE_ENV=production npm run build || (echo "构建失败，查看错误信息" && exit 1)

RUN npm install -g serve

EXPOSE 9009

CMD ["serve", "-s", "dist", "-l", "9009"] 