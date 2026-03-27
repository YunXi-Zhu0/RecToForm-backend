# API 层实施说明

## 目标

本文件用于指导后续 `src/api/` 的具体实施，要求 API 层围绕以下业务闭环落地：

`模式选择 -> 多文件上传 -> RQ 投递任务 -> worker 调用 workflow -> 查询状态 -> 获取结果 -> 下载或导出 Excel`

API 层必须兼容两种模式：

- `template`
- `standard_edit`

其中：

- `template`：后端按模板导出结果
- `standard_edit`：后端统一返回标准字段全集结果，前端自行编辑后再导出

---

## 设计边界

### 1. API 层职责

- 接收 HTTP 请求
- 做基础参数校验
- 保存上传文件
- 创建任务记录
- 投递 RQ 任务
- 返回任务状态、结果摘要和下载信息

### 2. API 层不负责

- 不直接在路由中编排 document / llm / excel 主流程
- 不在路由中拼 prompt
- 不在路由中做模板字段映射
- 不在 API 层做“自定义表头与模板字段绑定”

### 3. 与 services 层协作方式

- 识别与导出主链路仍由 `src/services/workflow/` 驱动
- API 层通过 `src/api/services/` 做任务封装与结果适配
- 若现有 workflow 仅支持单文件，应在 services 层新增批量任务编排能力，API 层不直接循环拼业务

---

## 目录建议

- `src/api/app.py`
- `src/api/routes/templates.py`
- `src/api/routes/fields.py`
- `src/api/routes/tasks.py`
- `src/api/routes/exports.py`
- `src/api/schemas/common.py`
- `src/api/schemas/template.py`
- `src/api/schemas/field.py`
- `src/api/schemas/task.py`
- `src/api/schemas/export.py`
- `src/api/services/task_dispatcher.py`
- `src/api/services/task_repository.py`
- `src/api/services/result_builder.py`

如需拆出队列接入，可补：

- `src/api/services/queue.py`

---

## 接口约定

### 1. `GET /api/v1/templates`

用途：

- 返回模板列表

响应字段建议：

- `template_id`
- `template_name`
- `template_version`
- `mapping_version`

### 2. `GET /api/v1/templates/{template_id}`

用途：

- 返回模板详情

响应字段建议：

- `template_id`
- `template_name`
- `template_version`
- `mapping_version`
- `recommended_field_ids`
- `default_header_labels`

说明：

- 当前模板详情主要服务模板模式
- 自定义表头模式不依赖模板映射

### 3. `GET /api/v1/standard-fields`

用途：

- 返回标准字段全集及版本信息

响应字段建议：

- `version`
- `default_missing_value`
- `fields`

其中 `fields` 建议直接来自 `standard_fields.json`

### 4. `POST /api/v1/tasks`

用途：

- 上传多文件并创建任务

请求建议采用：

- `multipart/form-data`

字段建议：

- `config`: JSON 字符串
- `files[]`: 多文件

`config` 建议结构：

```json
{
  "mode": "template",
  "template_id": "finance_invoice",
  "template_version": "v1",
  "extra_instructions": []
}
```

或：

```json
{
  "mode": "standard_edit",
  "extra_instructions": []
}
```

响应字段建议：

- `task_id`
- `status`
- `mode`
- `total_files`

### 5. `GET /api/v1/tasks/{task_id}`

用途：

- 查询任务状态

响应字段建议：

- `task_id`
- `mode`
- `status`
- `stage`
- `total_files`
- `processed_files`
- `succeeded_files`
- `failed_files`
- `progress_percent`
- `error_message`

### 6. `GET /api/v1/tasks/{task_id}/result`

用途：

- 返回任务结果摘要

`template` 模式建议响应：

- `task_id`
- `mode`
- `status`
- `preview_headers`
- `preview_rows`
- `excel_download_url`
- `failed_items`

`standard_edit` 模式建议响应：

- `task_id`
- `mode`
- `status`
- `standard_fields`
- `rows`
- `failed_items`

### 7. `GET /api/v1/tasks/{task_id}/excel`

用途：

- 下载任务生成的 Excel 文件

### 8. `POST /api/v1/exports/standard-fields`

用途：

- 接收前端编辑后的最终二维表并导出 Excel

请求字段建议：

- `headers`
- `rows`
- `filename`

请求示例：

```json
{
  "headers": ["发票号码", "发票代码", "合计", "备注"],
  "rows": [
    ["12345678", "011002300111", "100.00", ""],
    ["87654321", "011002300222", "230.00", "前端补充"]
  ],
  "filename": "发票信息.xlsx"
}
```

响应建议：

- 文件流
- 或 `download_url`

---

## 任务模型建议

### 1. 任务状态

建议状态枚举：

- `queued`
- `running`
- `file_preprocessing`
- `llm_processing`
- `assembling_results`
- `excel_generating`
- `succeeded`
- `partially_succeeded`
- `failed`

### 2. 任务记录建议字段

- `task_id`
- `mode`
- `status`
- `stage`
- `total_files`
- `processed_files`
- `succeeded_files`
- `failed_files`
- `progress_percent`
- `input_files`
- `result_payload_path`
- `excel_output_path`
- `error_message`
- `created_at`
- `updated_at`

### 3. 文件级结果建议字段

- `file_name`
- `status`
- `structured_data`
- `error_message`
- `audit_file_path`

---

## 调度与并发模型

### 1. 总体模型

采用两层并发：

1. `RQ worker` 负责进程级并发
2. 单个任务内部使用 `asyncio` 负责文件级并发

### 2. 典型执行流程

1. API 接收请求并保存上传文件
2. API 初始化任务记录，状态置为 `queued`
3. API 通过 RQ 把任务投递到指定队列
4. worker 获取任务后执行 job
5. job 内部 `asyncio.run(...)` 调用批量 workflow
6. job 使用 `Semaphore` 控制并发文件数量
7. 汇总结构化结果
8. 根据模式决定是否直接生成 Excel
9. 更新任务记录与结果路径

### 3. RQ 使用约束

- RQ job 入口保持同步函数
- 同步 job 中启动 async workflow
- 不把 API 请求上下文对象直接传入 RQ
- RQ job 只接收最小化可序列化参数，例如：
  - `task_id`
  - `mode`
  - `file_paths`
  - `template_id`
  - `template_version`

### 4. async 使用约束

- LLM 调用走 async
- 阻塞式文件解析和 Excel 写入需避免直接压住事件循环
- 如需在 async 流程中调用同步方法，优先考虑 `asyncio.to_thread(...)`

---

## 配置项要求

所有配置统一进入 `src/core/config.py`，通过 `.env` 驱动，不在其他层散落 `os.getenv`。

建议新增：

- `REDIS_URL`
- `RQ_QUEUE_NAME`
- `RQ_JOB_TIMEOUT`
- `RQ_RESULT_TTL`
- `RQ_WORKER_PROCESSES`
- `WORKFLOW_ASYNC_CONCURRENCY`
- `MAX_UPLOAD_FILES`
- `MAX_FILE_SIZE_MB`
- `API_HOST`
- `API_PORT`

建议说明：

- `RQ_WORKER_PROCESSES`：机器层面同时跑多少个 worker 进程
- `WORKFLOW_ASYNC_CONCURRENCY`：单任务内同时分析多少个文件

`.env.example` 建议值：

```env
API_HOST=0.0.0.0
API_PORT=8000
REDIS_URL=redis://127.0.0.1:6379/0
RQ_QUEUE_NAME=invoice_tasks
RQ_JOB_TIMEOUT=1800
RQ_RESULT_TTL=86400
RQ_WORKER_PROCESSES=4
WORKFLOW_ASYNC_CONCURRENCY=15
MAX_UPLOAD_FILES=50
MAX_FILE_SIZE_MB=10
```

---

## 与现有代码的衔接判断

### 1. 已可复用部分

- `TemplateService.list_templates`
- `TemplateService.get_template_bundle`
- `StandardSchemaService.load_schema`
- `WorkflowService.run`
- `ExcelService.write_standard_fields`

### 2. 需要新增或调整的部分

- API 层目录与 FastAPI 应用入口
- 多文件任务模型
- 批量 workflow 编排
- 任务仓储与状态持久化
- RQ 投递与 worker job
- 自定义表格导出接口
- 结果摘要构造器

### 3. 关键差距

当前 workflow 偏向单文件输入、单结果输出。

后续需要在 services 层新增一个“批量任务编排服务”，语义建议为：

- 一个任务对应多个输入文件
- 一个输入文件对应一条标准字段结果
- `template` 模式可聚合并生成 Excel
- `standard_edit` 模式可先返回标准字段全集结果供前端编辑

---

## 实施顺序建议

### 第一阶段：API 骨架

- 建立 `src/api/` 目录
- 建立 FastAPI app
- 注册路由与 CORS
- 增加基础 health 接口

### 第二阶段：元数据接口

- 模板列表接口
- 模板详情接口
- 标准字段接口

### 第三阶段：任务创建与查询

- 上传文件落盘
- 创建任务记录
- RQ 投递
- 状态查询接口

### 第四阶段：worker 与批量 workflow

- RQ job
- 批量并发编排
- 状态推进
- 结果聚合

### 第五阶段：结果接口与导出接口

- 结果摘要接口
- Excel 下载接口
- 自定义标准字段表格导出接口

---

## 实施时必须坚持的约束

1. 自定义表头模式不做后端字段绑定。
2. 标准字段全集始终以 `standard_fields.json` 为准。
3. API 路由层保持薄，不把业务编排直接塞进路由。
4. 任务调度参数全部配置化。
5. 先保证任务制闭环，再做高级体验优化。
