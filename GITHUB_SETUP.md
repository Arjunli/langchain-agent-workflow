# GitHub 仓库设置指南

## 步骤1: 创建GitHub仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `langchain-agent-workflow`
   - **Description**: `A powerful LangChain-based intelligent Agent system with workflow engine, knowledge base, and message queue support`
   - **Visibility**: Public（或Private，根据你的需求）
   - **不要**勾选 "Initialize this repository with a README"（因为我们已经有了代码）

3. 点击 "Create repository"

## 步骤2: 添加远程仓库并推送代码

创建仓库后，GitHub会显示推送代码的命令。执行以下命令：

```bash
# 添加远程仓库（将YOUR_USERNAME替换为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/langchain-agent-workflow.git

# 或者使用SSH（如果你配置了SSH密钥）
git remote add origin git@github.com:YOUR_USERNAME/langchain-agent-workflow.git

# 推送代码到GitHub
git branch -M main
git push -u origin main
```

## 步骤3: 验证

推送完成后，访问你的GitHub仓库页面，应该能看到所有代码文件。

## 如果遇到问题

### 问题1: 认证失败

如果推送时提示需要认证，可以：

1. **使用Personal Access Token**:
   - 访问 https://github.com/settings/tokens
   - 生成新的token（选择repo权限）
   - 推送时使用token作为密码

2. **配置SSH密钥**:
   ```bash
   # 生成SSH密钥（如果还没有）
   ssh-keygen -t ed25519 -C "your_email@example.com"
   
   # 将公钥添加到GitHub
   # 访问 https://github.com/settings/keys
   # 点击 "New SSH key"，粘贴 ~/.ssh/id_ed25519.pub 的内容
   ```

### 问题2: 分支名称不匹配

如果GitHub默认分支是`main`而本地是`master`：

```bash
git branch -M main
git push -u origin main
```

### 问题3: 需要先拉取

如果GitHub仓库有初始文件（README等），需要先合并：

```bash
git pull origin main --allow-unrelated-histories
# 解决冲突后
git push -u origin main
```

## 后续操作

推送成功后，你可以：

1. **添加仓库描述和标签**
2. **设置README中的徽章**
3. **配置GitHub Actions进行CI/CD**
4. **添加LICENSE文件**（如果需要）

## 快速命令（如果仓库已创建）

```bash
# 在项目根目录执行
cd d:\code\agent

# 添加远程仓库（替换YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/langchain-agent-workflow.git

# 重命名分支为main（如果需要）
git branch -M main

# 推送代码
git push -u origin main
```
