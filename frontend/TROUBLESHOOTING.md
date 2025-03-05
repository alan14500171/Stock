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

1. **使用自定义polyfill**

   在项目根目录创建`crypto-polyfill.js`文件：
   ```javascript
   try {
     const { webcrypto } = require("crypto");
     global.crypto = webcrypto;
     console.log("使用Node.js webcrypto作为polyfill");
   } catch (e) {
     console.log("无法加载webcrypto，使用自定义随机函数");
     global.crypto = {
       getRandomValues: function(buffer) {
         for (let i = 0; i < buffer.length; i++) {
           buffer[i] = Math.floor(Math.random() * 256);
         }
         return buffer;
       }
     };
   }
   ```

   然后在构建命令中使用：
   ```bash
   node -r ./crypto-polyfill.js ./node_modules/vite/bin/vite.js build
   ```

2. **修改vite.config.mjs**

   在`vite.config.mjs`中添加以下配置：
   ```javascript
   // 自定义crypto polyfill
   if (typeof global !== 'undefined' && !global.crypto) {
     global.crypto = {
       getRandomValues: function(buffer) {
         for (let i = 0; i < buffer.length; i++) {
           buffer[i] = Math.floor(Math.random() * 256);
         }
         return buffer;
       }
     };
     console.log('已添加自定义crypto polyfill');
   }
   
   export default defineConfig({
     // ...其他配置
     resolve: {
       alias: {
         'crypto': 'crypto-browserify',
         'stream': 'stream-browserify',
         'assert': 'assert',
         'buffer': 'buffer',
         'util': 'util'
       }
     },
     optimizeDeps: {
       include: ['crypto-browserify'],
       esbuildOptions: {
         define: {
           global: "window"
         }
       }
     },
     define: {
       'global': 'window',
       // ...其他定义
     }
   })
   ```

3. **安装必要的polyfill包**

   ```bash
   npm install --save-dev crypto-browserify stream-browserify assert buffer util
   ```

4. **使用Node.js 16版本**

   Node.js 16版本对crypto模块有更好的支持：
   ```dockerfile
   FROM node:16-alpine as build
   ```

5. **群辉NAS环境特殊处理**

   在群辉NAS的Docker环境中，可能需要额外的配置：
   - 在`docker-compose.yml`中设置`network_mode: host`
   - 添加DNS配置：`dns: ["8.8.8.8", "8.8.4.4"]`
   - 确保Docker容器有足够的内存：`--max-old-space-size=4096`

6. **如果问题持续存在**

   考虑切换到webpack构建工具，它对Node.js polyfill有更好的支持。

## 联系支持

如果您在部署过程中遇到无法解决的问题，请联系技术支持团队，并提供以下信息:

1. 详细的错误信息和日志
2. 系统环境信息（操作系统、Docker版本等）
3. 已尝试的解决方案 

## 群辉NAS Docker部署特定问题

### 问题: 符号链接问题 (XSym错误)

在群辉NAS的Docker环境中，可能会遇到以下错误：

```
XSym
0019
94d8a167e5fc58922c363ccb1c217737
../vite/bin/vite.js
```

这是因为群辉NAS的文件系统对符号链接的处理与标准Linux系统不同。

### 解决方案

1. **直接创建执行脚本替代符号链接**

   在Dockerfile中添加以下命令：
   ```dockerfile
   RUN echo '#!/usr/bin/env node\nrequire("../vite/bin/vite.js")' > ./node_modules/.bin/vite && \
       chmod +x ./node_modules/.bin/vite
   ```

2. **修改package.json中的构建命令**

   将构建命令修改为直接使用vite.js文件：
   ```json
   "build": "node ./node_modules/vite/bin/vite.js build"
   ```

3. **使用Docker卷挂载**

   如果仍然遇到问题，可以尝试使用Docker卷挂载，避免在容器内部处理符号链接：
   ```yaml
   volumes:
     - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
   ```

### 问题: 群辉NAS上的Docker网络问题

在群辉NAS上，Docker容器可能无法正常访问外部网络或其他容器。

### 解决方案

1. **使用host网络模式**

   修改docker-compose.yml文件，使用host网络模式：
   ```yaml
   network_mode: "host"
   ```
   
   注意：使用host网络模式时，容器将直接使用宿主机的网络，不需要端口映射。

2. **配置DNS**

   如果容器无法解析域名，可以添加DNS配置：
   ```yaml
   dns:
     - 8.8.8.8
     - 8.8.4.4
   ```

3. **检查群辉防火墙设置**

   确保群辉的防火墙允许Docker容器的网络流量。

### 问题: 群辉NAS上的权限问题

群辉NAS上的Docker容器可能遇到文件权限问题。

### 解决方案

1. **设置适当的用户ID**

   在Dockerfile中添加以下命令：
   ```dockerfile
   RUN addgroup -g 1000 appgroup && \
       adduser -D -u 1000 -G appgroup appuser && \
       chown -R appuser:appgroup /app
   
   USER appuser
   ```

2. **使用root用户运行Nginx**

   在Nginx配置中添加：
   ```
   user root;
   ```

3. **设置卷的权限**

   在docker-compose.yml文件中设置卷的权限：
   ```yaml
   volumes:
     - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
   ``` 