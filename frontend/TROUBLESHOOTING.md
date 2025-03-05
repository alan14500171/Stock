# 股票交易系统前端部署故障排除指南

本文档提供了在部署股票交易系统前端时可能遇到的常见问题及其解决方案。

## 构建错误

### 问题: `npm run build` 失败，出现 "XSym: not found" 错误

错误信息示例:
```
#11 6.172 /app/node_modules/.bin/vite: line 1: XSym: not found
#11 6.172 /app/node_modules/.bin/vite: line 2: 0019: not found
#11 6.172 /app/node_modules/.bin/vite: line 3: 94d8a167e5fc58922c363ccb1c
#11 6.172 /app/node_modules/.bin/vite: line 4: ../vite/bin/vite.js: not found
```

### 解决方案

这个错误通常是由于Node.js环境中的符号链接问题导致的。以下是几种解决方法:

1. **手动修复符号链接**

   在Dockerfile中添加以下命令来修复vite的符号链接:
   ```dockerfile
   RUN cd node_modules/.bin && \
       rm -f vite && \
       ln -s ../vite/bin/vite.js vite && \
       chmod +x vite
   ```

2. **使用Node.js 16版本**

   将Dockerfile中的Node.js版本从18降级到16:
   ```dockerfile
   FROM node:16-alpine
   ```

3. **使用 `--legacy-peer-deps` 安装依赖**

   修改 `Dockerfile` 中的安装命令:
   ```dockerfile
   RUN npm install --legacy-peer-deps
   ```

4. **增加Node.js内存限制**

   在 `Dockerfile` 中添加环境变量:
   ```dockerfile
   ENV NODE_OPTIONS="--max-old-space-size=4096"
   ```

5. **清理并重新构建**

   完全清理Docker资源并重新构建:
   ```bash
   ./start.sh clean
   ./start.sh start
   ```

6. **直接安装vite**

   在Dockerfile中添加以下命令:
   ```dockerfile
   RUN npm install -g vite
   ```

7. **使用npm脚本替代vite命令**

   修改package.json中的build脚本:
   ```json
   "scripts": {
     "build": "node ./node_modules/vite/bin/vite.js build"
   }
   ```

## 端口冲突问题

### 问题: 启动容器时出现端口被占用错误

错误信息示例:
```
Error response from daemon: driver failed programming external connectivity on endpoint stock-frontend: Error starting userland proxy: listen tcp4 0.0.0.0:80: bind: address already in use
```

### 解决方案

1. **修改端口映射**

   编辑 `docker-compose.nginx.yml` 文件，将端口映射修改为其他未被占用的端口:
   ```yaml
   ports:
     - "8080:80"  # 将主机的8080端口映射到容器的80端口
   ```

2. **停止占用端口的服务**

   找出并停止占用该端口的服务:
   ```bash
   # 查找占用端口的进程
   sudo lsof -i :80
   
   # 停止该进程
   sudo kill <进程ID>
   ```

## 网络连接问题

### 问题: 前端无法连接到后端API

### 解决方案

1. **检查API地址配置**

   确保 `.env.production` 文件中的API地址配置正确:
   ```
   VITE_API_BASE_URL=http://实际后端IP地址:9099
   ```

2. **检查网络连接**

   确保前端容器可以访问后端服务:
   ```bash
   docker exec -it stock-frontend ping 后端IP地址
   ```

3. **检查Nginx配置**

   如果使用Nginx模式，确保 `nginx.conf` 中的代理配置正确:
   ```nginx
   location /api {
     proxy_pass http://实际后端IP地址:9099;
     # 其他代理设置...
   }
   ```

## Docker相关问题

### 问题: 容器启动后立即退出

### 解决方案

1. **检查容器日志**

   查看容器的详细日志:
   ```bash
   docker logs stock-frontend
   ```

2. **以交互模式启动容器进行调试**

   ```bash
   docker run -it --rm --entrypoint /bin/sh stock-frontend:latest
   ```

3. **检查构建过程**

   使用 `--no-cache` 参数重新构建镜像:
   ```bash
   docker-compose build --no-cache
   ```

## 使用诊断工具

系统提供了诊断工具来帮助排查问题:

1. **使用启动脚本的诊断功能**

   ```bash
   ./start.sh clean  # 清理资源
   ./start.sh start  # 重新启动并查看详细日志
   ```

2. **查看详细构建日志**

   ```bash
   docker-compose build --no-cache --progress=plain
   ```

## 性能优化

如果前端应用在生产环境中加载缓慢，可以尝试以下优化:

1. **优化构建配置**

   修改 `vite.config.mjs` 文件，添加构建优化选项:
   ```javascript
   build: {
     chunkSizeWarningLimit: 1000,
     cssCodeSplit: false,
     target: 'es2015',
     reportCompressedSize: false
   }
   ```

2. **使用CDN加速静态资源**

   考虑将静态资源部署到CDN以提高加载速度。

## 构建过程中的 `crypto.getRandomValues is not a function` 错误

### 错误信息

在执行 `npm run build` 命令时，可能会遇到以下错误：

```
TypeError: crypto$2.getRandomValues is not a function
```

这个错误通常与 Node.js 的加密模块有关，在 Vite 构建过程中可能会出现。

### 解决方案

1. **修改 vite.config.mjs 文件**

   在 `vite.config.mjs` 文件中添加以下配置：

   ```javascript
   optimizeDeps: {
     esbuildOptions: {
       define: {
         global: 'globalThis'
       }
     }
   },
   define: {
     'process.env': {},
     __VUE_PROD_DEVTOOLS__: false,
     'process.env.NODE_DEBUG': false,
     'global': 'window'
   }
   ```

2. **安装必要的系统依赖**

   在 Dockerfile 中添加以下命令：

   ```dockerfile
   RUN apk add --no-cache python3 make g++
   ```

3. **使用 Node.js 16 版本**

   将 Dockerfile 中的基础镜像从 Node.js 18 降级到 Node.js 16：

   ```dockerfile
   FROM node:16-alpine as build-stage
   ```

4. **设置 NODE_ENV 环境变量**

   在构建命令中设置 NODE_ENV 环境变量：

   ```dockerfile
   RUN NODE_ENV=production npm run build
   ```

5. **安装 crypto-browserify 包**

   ```bash
   npm install crypto-browserify --save-dev
   ```

   然后在 `vite.config.mjs` 中添加别名：

   ```javascript
   resolve: {
     alias: {
       '@': path.resolve(__dirname, './src'),
       'crypto': 'crypto-browserify'
     }
   }
   ```

6. **清理 node_modules 并重新安装**

   ```bash
   rm -rf node_modules
   npm install --legacy-peer-deps
   ```

7. **使用直接路径执行 vite**

   修改 `package.json` 中的构建脚本：

   ```json
   "build": "node ./node_modules/vite/bin/vite.js build"
   ```

以上解决方案可以单独尝试，也可以组合使用。如果问题仍然存在，请检查项目中是否有使用了不兼容的加密库或模块。

## 联系支持

如果您在部署过程中遇到无法解决的问题，请联系技术支持团队，并提供以下信息:

1. 详细的错误信息和日志
2. 系统环境信息（操作系统、Docker版本等）
3. 已尝试的解决方案 