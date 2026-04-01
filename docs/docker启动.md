# Docker 启动说明

本文档总结当前仓库中的 Docker 相关实现，便于在本地或服务器上直接启动 `RecToForm`。

## 1. 当前容器结构

项目根目录当前包含以下 Docker 文件：

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

`docker-compose.yml` 会同时启动 3 个服务：

- `backend`
  - 基于项目根目录 `Dockerfile` 构建
  - 运行命令：`uvicorn src.api.app:app --host 0.0.0.0 --port 8080`
  - 对外暴露端口：`8080`
- `worker`
  - 与 `backend` 共用同一个镜像
  - 运行命令：`rq worker invoice_tasks`
  - 用于消费异步任务队列
- `redis`
  - 使用 `redis:latest`
  - 用于任务队列与导出映射存储

容器共享一个命名卷：

- `rec2form_outputs:/app/outputs`

该卷用于持久化接口产物、导出文件及运行过程中的输出目录。

## 2. 镜像实现说明

当前 `Dockerfile` 的实现流程如下：

1. 以 `python:3.12-slim` 为基础镜像。
2. 安装 `curl`。
3. 通过官方安装脚本安装 `uv`。
4. 复制 `pyproject.toml` 和 `uv.lock` 后执行 `uv sync --frozen --no-dev`。
5. 再复制项目源码到容器内。
6. 默认启动 `uvicorn` 并监听 `8080` 端口。

`.dockerignore` 当前排除了以下内容进入构建上下文：

- `.venv`
- `__pycache__`
- `.git`
- `docs`
- `tests`
- `outputs`
- `contexts`

说明：
- 当前镜像使用的是 Python 3.12。
- 当前 Compose 和镜像启动命令都固定使用 `8080`，即使 `.env` 中配置了 `API_PORT`，容器命令本身也不会跟随变化。

## 3. 启动前准备

启动前需要准备：

- 已安装 Docker
- 已安装 Docker Compose 插件，命令为 `docker compose`
- 项目根目录下存在 `.env`

推荐至少在 `.env` 中确认以下配置。

### 3.1 队列与 Redis

在 Docker Compose 场景下，`backend` 和 `worker` 访问 Redis 不能使用 `127.0.0.1`，应改为服务名：

```env
REDIS_URL=redis://redis:6379/0
```

另外需要注意：

- 代码中的默认队列名为 `invoice_tasks`
- `docker-compose.yml` 里 `worker` 启动命令也固定写成了 `rq worker invoice_tasks`
- 因此如果修改 `.env` 中的 `RQ_QUEUE_NAME`，还需要同步调整 `docker-compose.yml` 里的 `worker` 命令，否则生产者和消费者会监听不同队列

### 3.2 LLM 相关配置

系统默认的 LLM provider 为：

```env
LLM_PROVIDER=qwen_official
```

如果使用官方千问兼容接口，至少需要：

```env
QWEN3_VL_PLUS_API_KEY=你的密钥
```

对应基础地址在代码中固定为：

- `https://dashscope.aliyuncs.com/compatible-mode/v1`

如果使用本地 OpenAI 兼容服务，则需要至少配置：

```env
LLM_PROVIDER=qwen_local_openai_compatible
QWEN3_VL_8B_SSPU_API_URL=http://你的服务地址/v1/chat/completions
QWEN3_VL_8B_SSPU_MODEL_NAME=/model/Qwen3-VL-8B
```

### 3.3 可选接口配置

以下配置没有强制要求，但容器化部署时经常需要显式设置：

```env
API_TITLE=RecToForm API
API_PREFIX=/api/v1
API_CORS_ORIGINS=*
EXPORT_FILE_MAPPING_TTL=86400
RQ_JOB_TIMEOUT=1800
RQ_RESULT_TTL=86400
```

## 4. 启动命令

在项目根目录执行：

```bash
docker compose up -d --build
```

首次启动会完成镜像构建，并拉起以下容器：

- `rec2form-backend`
- `rec2form-worker`
- `rec2form-redis`

如果只想前台观察日志，可以执行：

```bash
docker compose up --build
```

## 5. 运行验证

### 5.1 查看容器状态

```bash
docker compose ps
```

### 5.2 查看后端日志

```bash
docker compose logs -f backend
```

### 5.3 查看 worker 日志

```bash
docker compose logs -f worker
```

### 5.4 健康检查

后端启动后可访问：

```text
http://localhost:8080/health
```

预期返回：

```json
{"status":"ok"}
```

## 6. 停止与清理

停止服务：

```bash
docker compose down
```

如果连同命名卷一起删除：

```bash
docker compose down -v
```

注意：

- `docker compose down -v` 会删除 `rec2form_outputs` 卷
- 卷中保存的 `/app/outputs` 数据也会一起清空

## 7. 当前实现下的几个注意点

1. 当前 Compose 编排只启动后端、worker 和 Redis，不包含前端服务。
2. `backend` 与 `worker` 共用同一镜像，因此代码更新后通常需要重新执行 `docker compose up -d --build`。
3. `worker` 命令当前写死为 `rq worker invoice_tasks`，队列名不应只在 `.env` 中单独修改。
4. 容器输出目录落在命名卷 `rec2form_outputs` 中，而不是宿主机目录绑定。
5. 健康检查接口只覆盖后端进程存活，不代表 LLM 配置、Redis 连通性和业务链路一定全部可用。
