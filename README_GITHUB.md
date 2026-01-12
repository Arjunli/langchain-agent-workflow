# 快速推送代码到GitHub

## 方法1: 使用PowerShell脚本（最简单）

### 步骤1: 在GitHub网页创建仓库
1. 访问 https://github.com/new
2. Repository name: `langchain-agent-workflow`
3. Description: `A powerful LangChain-based intelligent Agent system`
4. **选择 Private（私有仓库）**
5. **不要勾选** "Initialize this repository with a README"
6. 点击 "Create repository"

### 步骤2: 运行脚本
```powershell
cd d:\code\agent
.\setup_github.ps1 -Username arjun
```

脚本会自动：
- 添加远程仓库
- 重命名分支为main
- 推送代码

## 方法2: 手动命令

如果脚本不工作，可以手动执行：

```bash
cd d:\code\agent

# 添加远程仓库
git remote add origin https://github.com/arjun/langchain-agent-workflow.git

# 重命名分支
git branch -M main

# 推送代码
git push -u origin main
```

**注意**: 推送时如果提示输入密码，需要使用GitHub Personal Access Token，不是GitHub密码。

## 获取Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" -> "Generate new token (classic)"
3. 选择权限：至少勾选 `repo` 权限
4. 生成后复制token
5. 推送时：
   - Username: `arjun`
   - Password: 粘贴token（不是GitHub密码）

## 当前状态

✅ Git仓库已初始化
✅ 代码已提交（3个提交）
✅ 包含57个文件，6343行代码
✅ 准备推送到GitHub

## 验证

推送成功后，访问 https://github.com/arjun/langchain-agent-workflow 查看仓库。
