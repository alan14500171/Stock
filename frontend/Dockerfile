FROM node:18-alpine

WORKDIR /app

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 增加Node.js内存限制
ENV NODE_OPTIONS="--max-old-space-size=4096"

COPY package*.json ./

# 安装依赖，使用--legacy-peer-deps解决潜在的依赖冲突
RUN npm install --legacy-peer-deps

COPY . .

# 添加错误处理，如果构建失败则输出详细信息
RUN npm run build || (echo "构建失败，查看错误信息" && exit 1)

RUN npm install -g serve

EXPOSE 9009

CMD ["serve", "-s", "dist", "-l", "9009"] 