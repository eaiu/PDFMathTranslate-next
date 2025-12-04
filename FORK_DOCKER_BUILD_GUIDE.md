# Fork仓库Docker构建配置指南

## 总结

✅ **NumPy问题已修复**: 在 `pyproject.toml` 中添加了 `numpy>=1.20,<2.0` 限制
✅ **Docker构建不受影响**: Docker环境独立，不会遇到你本地的NumPy问题

## 快速配置步骤

### 1. 配置GitHub Secrets

进入你的fork仓库设置：
- Settings → Secrets and variables → Actions → New repository secret

添加两个secrets：

**DOCKERHUB_USERNAME**
```
你的Docker Hub用户名
```

**DOCKERHUB_TOKEN**  
```
你的Docker Hub访问令牌（在Docker Hub的Account Settings → Security创建）
```

### 2. 修改 `.github/workflows/release.yml`

只需修改两处：

#### 修改1: 第18行 - Docker Hub仓库名
```yaml
# 原来
DOCKERHUB_REPO: awwaawwa/pdfmathtranslate-next

# 改为（替换成你的用户名）
DOCKERHUB_REPO: 你的用户名/pdfmathtranslate-next
```

#### 修改2: 第27行 - 移除主仓库限制
```yaml
# 原来
is_main_repo: ${{ github.repository == 'PDFMathTranslate/PDFMathTranslate-next' }}

# 改为
is_main_repo: true
```

### 3. 推送并等待构建

```bash
git add .
git commit -m "Add new Web UI with authentication"
git push origin main
```

然后：
1. 进入GitHub仓库的 **Actions** 标签
2. 等待构建完成（约20-30分钟）
3. 检查你的Docker Hub仓库

### 4. 使用Docker镜像

```bash
# 拉取镜像
docker pull 你的用户名/pdfmathtranslate-next:latest

# 运行新Web UI
docker run -p 7860:7860 -e PDF2ZH_WEB_UI=1 你的用户名/pdfmathtranslate-next:latest --gui

# 访问 http://localhost:7860
```

## 完整修改示例

假设你的Docker Hub用户名是 `jinuser`，完整修改如下：

```yaml
# .github/workflows/release.yml

env:
  REGISTRY: ghcr.io
  REPO_LOWER: ${{ github.repository_owner }}/${{ github.event.repository.name }}
  GHCR_REPO: ghcr.io/${{ github.repository }}
  DOCKERHUB_REPO: jinuser/pdfmathtranslate-next  # ← 修改这里
  WIN_EXE_PYTHON_VERSION: "3.13.3"

jobs:
  check-repository:
    name: Check if running in main repository
    runs-on: ubuntu-latest
    outputs:
      is_main_repo: true  # ← 修改这里
    steps:
      - run: echo "Running repository check"
```

## 注意事项

1. **NumPy版本已修复**: `pyproject.toml` 已添加 `numpy<2.0` 限制，Docker构建不会有问题

2. **只构建Docker**: 如果你只想构建Docker镜像，不需要PyPI发布和Windows EXE，可以禁用那些job（在job名称下添加 `if: false`）

3. **构建时间**: 
   - 首次构建: 约30分钟
   - 后续构建: 约15-20分钟（有缓存）

4. **GitHub Actions免费额度**: 
   - 公开仓库: 无限制
   - 私有仓库: 每月2000分钟

## 验证构建成功

构建完成后，检查：
1. GitHub Actions显示绿色✅
2. Docker Hub上有新镜像
3. 镜像标签包括 `latest` 和 `dev`

然后测试运行：
```bash
docker run -p 7860:7860 -e PDF2ZH_WEB_UI=1 你的用户名/pdfmathtranslate-next:latest --gui
```

访问 http://localhost:7860 应该看到新的Web UI登录页面！
