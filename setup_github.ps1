# GitHub仓库设置脚本
# 使用方法: .\setup_github.ps1 -Username YOUR_USERNAME

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [string]$RepoName = "langchain-agent-workflow"
)

Write-Host "=== GitHub仓库设置脚本 ===" -ForegroundColor Green
Write-Host ""

# 检查是否已配置远程仓库
$remoteUrl = git config --get remote.origin.url 2>$null

if ($remoteUrl) {
    Write-Host "检测到已配置的远程仓库: $remoteUrl" -ForegroundColor Yellow
    $response = Read-Host "是否要更新远程仓库URL? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        git remote remove origin
    } else {
        Write-Host "跳过远程仓库配置" -ForegroundColor Yellow
        exit
    }
}

# 添加远程仓库
$repoUrl = "https://github.com/$Username/$RepoName.git"
Write-Host "添加远程仓库: $repoUrl" -ForegroundColor Cyan
git remote add origin $repoUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: 无法添加远程仓库" -ForegroundColor Red
    exit 1
}

# 检查当前分支
$currentBranch = git branch --show-current
Write-Host "当前分支: $currentBranch" -ForegroundColor Cyan

# 重命名分支为main（如果需要）
if ($currentBranch -ne "main") {
    Write-Host "重命名分支为 main..." -ForegroundColor Cyan
    git branch -M main
}

# 显示推送命令
Write-Host ""
Write-Host "=== 准备推送代码 ===" -ForegroundColor Green
Write-Host ""
Write-Host "请确保已在GitHub创建仓库: https://github.com/new" -ForegroundColor Yellow
Write-Host "仓库名称: $RepoName" -ForegroundColor Yellow
Write-Host "仓库类型: Private (私有)" -ForegroundColor Yellow
Write-Host "不要勾选 'Initialize this repository with a README'" -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "仓库已创建? (y/n)"

if ($response -eq "y" -or $response -eq "Y") {
    Write-Host "推送代码到GitHub..." -ForegroundColor Cyan
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ 代码已成功推送到GitHub!" -ForegroundColor Green
        Write-Host "仓库地址: https://github.com/$Username/$RepoName" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "❌ 推送失败" -ForegroundColor Red
        Write-Host "可能的原因:" -ForegroundColor Yellow
        Write-Host "1. 仓库尚未创建" -ForegroundColor Yellow
        Write-Host "2. 认证失败（需要使用Personal Access Token）" -ForegroundColor Yellow
        Write-Host "3. 网络问题" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "解决方法:" -ForegroundColor Cyan
        Write-Host "1. 访问 https://github.com/settings/tokens 生成token" -ForegroundColor Cyan
        Write-Host "2. 推送时使用token作为密码" -ForegroundColor Cyan
    }
} else {
    Write-Host ""
    Write-Host "请先创建GitHub仓库，然后重新运行此脚本" -ForegroundColor Yellow
    Write-Host "或手动执行: git push -u origin main" -ForegroundColor Cyan
}
