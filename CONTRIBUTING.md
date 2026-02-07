# 贡献指南

感谢您对 AI Team 的兴趣！我们欢迎各种形式的贡献。

---

## 如何贡献

### 报告问题

如果您发现了bug或有功能建议，请通过 GitHub Issues 提交：

1. 检查是否已有相关问题
2. 创建新 Issue，详细描述问题
3. 提供复现步骤和环境信息

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 开发规范

### 代码风格

- 遵循 PEP 8 规范
- 使用有意义的变量名
- 添加必要的注释

### 提交信息

提交信息格式：

```
<type>: <subject>

<body>
```

类型：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat: 添加钉钉机器人支持

- 实现钉钉消息发送
- 添加钉钉群聊管理
```

### 测试

- 新功能需要添加测试
- 确保所有测试通过

```bash
python test_agent_company.py
```

---

## 开发环境

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python test_agent_company.py
```

### 运行演示

```bash
python main.py --demo
```

---

## 文档贡献

- 更新 README.md 中的相关说明
- 更新 USAGE.md 中的使用指南
- 更新 API.md 中的接口文档
- 更新 CHANGELOG.md 中的变更记录

---

## 行为准则

- 尊重他人
- 接受建设性批评
- 关注社区最佳利益

---

## 联系方式

- GitHub Issues: [提交问题](https://github.com/Carlehyy/MetaGPT/issues)

---

感谢您的贡献！
