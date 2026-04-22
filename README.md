# PaddleOCR-VL ARM Container Service

将 PaddleOCR-VL API 服务封装为可在 ARM（鲲鹏）环境下运行的 Docker 容器。

## 文件结构

```
├── api.py              # Flask API 服务
├── requirements.txt    # Python 依赖
├── Dockerfile          # ARM 兼容容器定义
├── docker-compose.yml  # 本地运行配置
├── download_model.py   # 模型下载脚本
├── PP-DocLayoutV2/     # 模型文件目录（需下载）
└── .github/workflows/
    └── build-arm.yml   # GitHub Actions 构建流程
```

## 快速开始

### 1. 下载模型

在你的 Python 环境中运行：

```bash
pip install modelscope
python download_model.py
```

或者直接使用 Python 代码：

```python
from modelscope import snapshot_download
snapshot_download('PaddlePaddle/PP-DocLayoutV2', cache_dir='./')
```

### 2. 本地构建和运行（x86 测试）

```bash
docker-compose up --build
```

### 3. 测试 API

```bash
curl http://localhost:5001/health

curl -X POST http://localhost:5001/ocr \
  -F "file=@test.png" \
  -F "format=both"
```

## GitHub Actions 部署到 ARM

### 前置条件

1. 在 GitHub 仓库 Settings -> Secrets 中添加：
   - `DOCKER_USERNAME`: Docker Hub 用户名
   - `DOCKER_PASSWORD`: Docker Hub 密码或 Access Token

2. 修改 `.github/workflows/build-arm.yml`（已预配置为 `tujinkai/paddleocr-vl-api`）

如需修改镜像名，编辑：
```yaml
env:
  REGISTRY: docker.io          # 或使用 ghcr.io（GitHub Container Registry）
  IMAGE_NAME: tujinkai/paddleocr-vl-api
```

### 自动构建

- 推送到 `main` 或 `master` 分支时自动构建
- 手动触发：Actions -> Build ARM Docker Image -> Run workflow

### 在鲲鹏 ARM 上运行

```bash
# 拉取镜像
docker pull tujinkai/paddleocr-vl-api:latest

# 运行容器
docker run -d \
  --name paddleocr-vl-api \
  -p 5001:5001 \
  -e VL_REC_SERVER_URL=http://your-vllm-server:3000/v1 \
  -e VL_REC_API_KEY=your-api-key \
  tujinkai/paddleocr-vl-api:latest
```

## 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VL_REC_SERVER_URL` | vLLM 服务地址 | `http://10.9.42.175:3000/v1` |
| `VL_REC_API_KEY` | API 密钥 | (内置) |
| `VL_REC_API_MODEL_NAME` | 模型名称 | `PaddleOCR-VL-0.9B` |
| `PORT` | 服务端口 | `5001` |

## API 接口

### 健康检查
```
GET /health
```

### OCR 处理
```
POST /ocr
Content-Type: multipart/form-data

参数:
- file: 图片文件 (png/jpg/jpeg)
- format: 返回格式 (json/md/both)
```

## 注意事项

1. **ARM 兼容性**: Dockerfile 使用 `python:3.10-slim` 基础镜像，原生支持 ARM64
2. **PaddlePaddle**: 支持 ARM CPU 运行，无需 GPU
3. **模型体积**: PP-DocLayoutV2 约 100MB，构建时自动下载
4. **启动时间**: 首次运行需要加载模型，约 30-60 秒