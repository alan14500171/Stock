# 贡献指南

感谢您考虑为股票交易管理系统做出贡献！

## 如何贡献

1. Fork 这个仓库
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m '添加一些功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 开发流程

1. 确保您的开发环境满足要求：
   - Python 3.12+
   - Node.js 18+
   - MySQL 8.0+

2. 安装依赖：
   ```bash
   # 后端依赖
   pip install -r requirements.txt

   # 前端依赖
   cd frontend
   npm install
   ```

3. 运行测试：
   ```bash
   # 后端测试
   python -m pytest

   # 前端测试
   cd frontend
   npm test
   ```

## 代码风格

- Python 代码遵循 PEP 8 规范
- JavaScript 代码遵循 Airbnb 风格指南
- 使用 4 个空格进行缩进
- 使用有意义的变量名和函数名
- 添加必要的注释

## 提交消息规范

提交消息应该清晰地描述更改内容。请使用以下格式：

```
<类型>: <描述>

[可选的详细描述]

[可选的关闭问题]
```

类型可以是：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更改
- style: 代码风格更改（不影响代码运行的变动）
- refactor: 重构（既不是新增功能，也不是修复 bug 的代码变动）
- perf: 性能优化
- test: 增加测试
- chore: 构建过程或辅助工具的变动

## 问题报告

请使用 GitHub Issues 来报告问题。在创建问题之前，请：

1. 检查是否已经存在相同的问题
2. 使用问题模板
3. 提供尽可能多的信息
4. 包含重现问题的步骤

## Pull Request

1. 更新 README.md 以反映更改（如果需要）
2. 更新文档以反映更改（如果需要）
3. PR 应该针对 `main` 分支
4. 确保所有测试都通过
5. 确保代码符合代码风格要求

## 许可证

通过贡献您的代码，您同意您的贡献将在 MIT 许可证下获得许可。 