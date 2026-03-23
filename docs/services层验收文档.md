# Services层验收文档

## 验收范围

本文档用于汇总当前分支内 `src/services/` 相关服务层的实施落地结果，覆盖以下四层：

- `src/services/template/`
- `src/services/excel/`
- `src/services/workflow/`
- `src/services/document/`

同时记录本阶段新增的模板配置、最小模板资源、验证方式与当前遗留限制。

## 已完成内容

### 1. 完成 services 四层目录落地

当前 `src/services/` 已形成如下结构：

- `template/`：模板定义、字段定义、字段合并、Excel 映射加载
- `excel/`：Excel 模板校验、字段写入、输出文件生成
- `workflow/`：主链路编排、状态推进、审计落盘、错误汇总
- `document/`：文件类型识别、图片直通、PDF 可选抽图、manifest 输出
- `llm/`：继续承接 prompt 组装、结构化结果清洗与模型调用

这意味着 `services.md` 中要求的服务层边界已经从规划状态进入可执行状态。

### 2. 完成 template 层契约实现

当前 `src/services/template/` 已实现：

- `TemplateFieldDefinition`
- `TemplateDefinition`
- `ExcelFieldMapping`
- `TemplateBundle`
- `TemplateSummary`
- `TemplateService`

已支持能力包括：

- 从根目录 `template/` 读取 JSON 模板定义
- 读取模板索引并列出系统支持的模板
- 按 `template_id + template_version` 获取模板
- 合并默认字段与用户勾选的可选字段
- 对目标字段集合做有序去重
- 校验字段定义是否完整
- 校验 Excel 模板文件是否存在
- 校验目标字段是否存在显式 Excel 映射

### 3. 完成模板配置与最小模板资源落地

本阶段已新增模板配置目录与资源：

- `template/index.json`
- `template/finance_invoice_v1.json`
- `template/asset_import_v1.json`
- `template/assets/finance_invoice_template_v1.xlsx`
- `template/assets/asset_import_template_v1.xlsx`

其中已整理并固化两个默认模板：

- `finance_invoice`
- `asset_import`

对应字段集合、模板版本、映射版本、Excel 路径和字段单元格映射均已进入 JSON 配置，不再散落在业务代码中。

### 4. 完成 excel 层写表能力落地

当前 `src/services/excel/` 已实现：

- `StructuredInvoiceData`
- `ExcelWriteRequest`
- `ExcelWriteResult`
- `ExcelService`

已支持能力包括：

- 读取 Excel 模板文件
- 校验模板文件存在性
- 校验映射中的 sheet 是否存在
- 按显式映射写入字段值
- 对缺失值统一写入空字符串
- 复制模板并生成输出文件
- 返回输出文件路径、实际写入字段、跳过字段、缺失映射摘要

这部分实现保持了“Excel 层不负责字段推断，只消费结构化结果和映射配置”的分层原则。

### 5. 完成 workflow 层主链路编排落地

当前 `src/services/workflow/` 已实现：

- `WorkflowStatus`
- `WorkflowRequest`
- `WorkflowAuditRecord`
- `WorkflowResult`
- `WorkflowService`

已支持能力包括：

- 串联 `document -> template -> llm -> excel`
- 构造 `PromptContext`
- 推进阶段状态：
  - `created`
  - `template_ready`
  - `prompt_ready`
  - `llm_processing`
  - `json_validated`
  - `excel_generating`
  - `audit_persisted`
  - `succeeded`
  - `failed`
- 将审计结果持久化到 JSON 文件
- 在失败时保留阶段信息、错误类型、错误消息和 traceback

当前 workflow 已满足最小可行主链路：

`图片输入 -> 模板字段合并 -> PromptContext -> LLMService.extract_structured_data(...) -> Excel 输出 -> 审计落盘`

### 6. 完成 document 层统一输入结果实现

当前 `src/services/document/` 已实现：

- `UploadedFileMeta`
- `PageImageItem`
- `DocumentManifest`
- `DocumentParseResult`
- `DocumentService`

已支持能力包括：

- 文件类型识别
- 图片文件直通
- 图片输入校验
- 生成统一的 `manifest`
- 输出 `image_paths`、`page_indices`、`manifest`
- PDF 文件走可选渲染后端抽图

当前 PDF 抽图后端按优先顺序支持：

- `PyMuPDF`（`fitz`）
- `pypdfium2`

如果环境中未安装上述库，会抛出明确错误，而不是把 PDF 逻辑耦合进 workflow。

### 7. 完成 services 层统一导出与配置补充

本阶段同步补充了：

- `src/services/__init__.py` 聚合导出
- `src/core/config.py` 中的模板目录、输出目录、审计目录、文档目录与缺失值常量
- `pyproject.toml` 中的 Python 版本约束调整为 `>=3.9,<3.10`
- `pyproject.toml` 新增 `openpyxl` 依赖声明

这一步使当前实现与项目目标 Python `3.9.25` 更一致，也补齐了 Excel 层运行所需依赖声明。

## 关键改动文件

本阶段重点涉及以下文件：

- `src/core/config.py`
- `src/services/__init__.py`
- `src/services/template/models.py`
- `src/services/template/service.py`
- `src/services/template/__init__.py`
- `src/services/excel/models.py`
- `src/services/excel/service.py`
- `src/services/excel/__init__.py`
- `src/services/document/models.py`
- `src/services/document/service.py`
- `src/services/document/__init__.py`
- `src/services/workflow/models.py`
- `src/services/workflow/service.py`
- `src/services/workflow/__init__.py`
- `template/index.json`
- `template/finance_invoice_v1.json`
- `template/asset_import_v1.json`
- `template/assets/finance_invoice_template_v1.xlsx`
- `template/assets/asset_import_template_v1.xlsx`
- `tests/unit/test_template_service.py`
- `tests/unit/test_excel_service.py`
- `tests/unit/test_document_service.py`
- `tests/unit/test_workflow_service.py`
- `pyproject.toml`

## 已完成验证

本阶段已执行并通过的验证包括：

- `python -m compileall src tests/unit/test_template_service.py tests/unit/test_excel_service.py tests/unit/test_document_service.py tests/unit/test_workflow_service.py`
- 基于内联 smoke script 的服务层联调验证，覆盖：
  - 模板加载与字段合并
  - Excel 写入与结果回读
  - 图片文件 document 解析
  - PDF 无渲染后端时的明确报错
  - workflow 主链路执行
  - Excel 输出文件生成
  - 审计文件落盘

smoke 验证结论：

- `template` 可正常返回目标字段集合与映射
- `excel` 可正确写入模板单元格
- `document` 可对图片返回统一结构
- `workflow` 可在 stub LLM 条件下跑通主链路并输出审计

## 已补充测试

当前新增测试覆盖了以下内容：

- 模板列表查询
- 默认字段与可选字段合并
- 字段顺序稳定性与去重
- Excel 模板写入
- 图片文件 document 解析
- PDF 依赖缺失时的错误路径
- workflow 成功路径

## 当前遗留问题与限制

### 1. pytest 在当前本地环境下未作为最终验收方式使用

本次尝试直接执行 `pytest` 时，测试启动阶段出现长时间卡住，运行环境显示为本机的 Python 3.7 / Anaconda 环境，不是项目目标 Python 3.9.25 环境。

因此本阶段没有将 `pytest` 通过作为最终验收结论，而是改用：

- `compileall`
- 内联 smoke script

进行代码有效性验证。

这说明当前仓库实现本身已可导入、可运行，但本地测试解释器环境仍需要统一。

### 2. PDF 抽图能力代码已接入，但当前环境未激活

当前仓库中已经实现 PDF 抽图的统一入口，但执行依赖以下库之一：

- `PyMuPDF`
- `pypdfium2`

在当前环境下，这两个库都未安装，因此 PDF 路径目前表现为：

- 代码结构已完成
- 错误提示明确
- 真实抽图能力待环境补齐后激活

### 3. workflow 仍以服务层联调为主，尚未接入 API 层

当前 `WorkflowService` 已经具备主链路能力，但还没有正式接到：

- `src/api/routes/`
- `src/api/services/`
- 请求响应 schema

因此本阶段的验收结论是：

- 服务层已落地
- API 集成尚未开始

## 当前状态判断

到当前为止，services 层已经完成以下目标：

- 分层边界已明确并代码化
- 模板定义从业务代码中抽离到 JSON 配置
- Excel 写表能力已可独立运行
- workflow 已具备最小主链路能力
- document 已具备统一输入结构与图片直通能力
- 审计落盘机制已建立

也就是说，`contexts/services.md` 中要求的 services 落地已经不再停留在设计阶段，而是进入“可继续向 API 层和完整业务流接入”的状态。

## 下一步建议

最自然的下一步是将这套服务层正式接入 API 层，至少补齐以下内容：

- `src/api/schemas/` 的请求响应模型
- `src/api/routes/` 的上传、执行、查询接口
- `src/api/services/` 的异步任务编排入口
- workflow 与前端参数的对接
- PDF 抽图依赖的环境补齐与真实验证
- 真实 LLM provider 下的集成测试

优先级上，建议先做 API 接入与环境统一，再做 PDF 抽图依赖补齐和端到端联调。
