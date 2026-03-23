# Services 分层落地规划

## 目标

本文档用于整理 `src/services/` 后续落地顺序、各层职责、需要实现的功能、依赖关系，以及建议先固定的数据结构。

当前建议实施顺序为：

1. `template`
2. `excel`
3. `workflow`
4. `document`

这个顺序的核心原因是：先稳定字段契约，再稳定 Excel 写入契约，再接主业务编排，最后补 PDF 抽图与页码审计能力。这样可以先用纯图片发票打通主链路，避免一开始就被 PDF 处理细节拖慢。

---

## 总体原则

- `template` 负责定义字段与模板，不负责 LLM 调用和 Excel 写入。
- `excel` 负责显式字段映射与表格写入，不负责字段推断。
- `workflow` 负责主链路编排，不负责承接各层内部实现细节。
- `document` 负责文件识别、图像准备、PDF 抽图与页码审计，不负责模板与表格逻辑。
- `services/llm` 继续负责 prompt 组装、模型调用、JSON 清洗与结构化结果输出。

---

## 跨层先固定的核心契约

在开始写各层代码前，建议先统一以下约束。

### 1. 系统内部字段统一使用 `field_id`

同一个字段的标识必须在以下位置保持一致：

- 模板字段定义
- LLM prompt 中的目标字段
- LLM JSON 输出键
- Excel 映射键
- workflow 中间结果键

建议区分：

- `field_id`：系统内部稳定标识，用于 JSON、映射、编排、持久化
- `field_label`：展示名称，用于界面、文档、说明

不要直接拿展示文案当唯一业务键，否则后续一旦改名，整条链路都要返工。

### 2. 模板定义独立放在 JSON 文件中

模板定义不建议硬编码在 Python 模块里，建议采用配置化管理。

当前建议：

- 模板定义文件放在项目根目录 `template/`
- 使用 JSON 格式
- 每个模板可单独一个文件，或使用统一索引文件加拆分文件的方式管理

这样做的目的：

- 模板字段调整不必直接改业务代码
- 后续新增模板时，不需要修改 workflow 主链路
- 更方便做版本化管理和比对

### 3. Excel 映射按模板版本管理

Excel 映射不能只绑定 `template_id`，还应显式绑定 `template_version`。

原因：

- 同一模板名称在不同版本下，sheet、单元格、字段位置都可能变化
- 映射配置必须和模板文件版本一一对应
- 后续排查填表错误时，需要明确是哪个模板版本、哪个映射版本产出的结果

建议至少保证以下关系可追溯：

- `template_id`
- `template_version`
- `excel_template_path`
- `mapping_version`

### 4. 缺失值统一使用空字符串

当前主链路统一约定：

- 缺失值一律使用空字符串 `""`

这一规则应在以下位置保持一致：

- prompt 缺失值说明
- LLM 输出约束
- JSON 清洗后的标准结果
- Excel 写入层默认空值策略

不要在不同层混用 `null`、`None`、`未识别`、`未知` 之类值，否则后面校验和写表会变复杂。

### 5. Workflow 审计结果需要持久化到文件

workflow 不仅要在内存里组织中间结果，还需要把关键审计结果落盘保存。

建议至少持久化：

- 原始输入文件信息
- 模板快照
- 最终字段集合
- prompt 上下文
- LLM 原始文本
- 清洗后的 JSON
- Excel 输出路径
- document manifest
- 任务状态与错误信息

建议优先使用文件持久化，后续如有需要再扩展到数据库。

---

## 推荐目录职责

### `src/services/template/`

负责：

- 默认模板定义
- 模板字段定义
- 可选字段定义
- 模板字段合并
- 模板版本管理
- 字段到 Excel 的映射配置管理
- 从根目录 `template/` 读取模板 JSON

不负责：

- Excel 写入
- LLM prompt 细节实现
- 文件检测
- PDF 抽图

### `src/services/excel/`

负责：

- 加载 Excel 模板
- 根据显式映射写入字段
- 保存输出文件
- 返回输出结果与写入摘要

不负责：

- 模板字段定义
- 业务字段推断
- 文件识别
- 主流程编排

### `src/services/workflow/`

负责：

- 串联 `template / llm / excel / document`
- 组装 `PromptContext`
- 管理阶段状态
- 汇总中间结果和最终结果
- 将审计结果持久化到文件

不负责：

- 直接处理 provider 协议
- 直接写 Excel 单元格
- 直接做 PDF 抽图

### `src/services/document/`

负责：

- 文件类型识别
- 图片文件直通
- PDF 抽图
- 图像顺序与页码映射
- 输出图像清单与 manifest

不负责：

- 模板字段处理
- LLM prompt 构造
- Excel 写入

---

## 分层实施顺序

## 第一阶段：`template`

### 本阶段目标

先稳定“系统到底抽哪些字段、这些字段如何组织、Excel 需要怎样的映射”这套业务契约。

### 建议优先实现的功能

1. 定义模板 JSON 结构
2. 定义字段 JSON 结构
3. 定义默认字段与可选字段
4. 定义模板版本与映射版本
5. 实现模板加载与查询
6. 实现默认字段与用户勾选字段的合并
7. 输出给 LLM 和 Excel 共同消费的字段集合
8. 产出字段到 Excel 的映射配置

### 已知默认模板必填字段

当前已在 `contexts/tmp.md` 中明确了两个默认模板的必填字段，后续应将其整理进根目录 `template/` 的 JSON 定义中。

#### 默认模板 1：财务系统录入发票字段

建议至少包含以下必填字段：

- `serial_no`
- `invoice_number`
- `invoice_code`
- `invoice_amount`
- `remark`

补充约束：

- `serial_no` 为 Excel 内自增主键，不依赖发票识别结果
- `invoice_code` 若发票中不存在，则回填 `invoice_number`
- `invoice_amount` 对应发票中的“合计”类金额
- `remark` 建议填写对应源文件名

#### 默认模板 2：大创低值材料资产入库模板自动导入

建议至少包含以下必填字段：

- `asset_category_code`
- `asset_name`
- `brand`
- `model`
- `unit`
- `quantity`
- `unit_price`
- `total_price`
- `supplier_name`
- `invoice_serial_number`
- `invoice_date`
- `storage_location`
- `remark`

补充约束：

- `asset_category_code` 需要根据资产名称进行规则推断
- `asset_name` 来自发票中的项目名称或商品名
- `total_price` 对应价税合计小写
- `storage_location` 由用户自行填写，不应依赖发票识别
- `remark` 建议填写对应源文件名

### 本阶段需要的数据结构

#### `TemplateFieldDefinition`

建议字段：

- `field_id`
- `field_label`
- `description`
- `required`
- `example_value`
- `value_type`
- `source_hint`
- `default_value`

说明：

- `field_id` 是内部稳定标识
- `field_label` 用于前端展示或文档说明
- `source_hint` 可描述“来源于发票识别”或“来源于用户补充”
- `default_value` 用于像缺失值、固定补位值这类规则

#### `TemplateDefinition`

建议字段：

- `template_id`
- `template_name`
- `template_version`
- `mapping_version`
- `excel_template_path`
- `default_field_ids`
- `optional_field_ids`

#### `ExcelFieldMapping`

建议字段：

- `template_id`
- `template_version`
- `mapping_version`
- `field_id`
- `sheet_name`
- `cell`
- `write_mode`

说明：

- `write_mode` 初期可只支持简单覆盖写入
- 映射必须和模板版本一起管理

#### `TemplateBundle`

这是 template 层最重要的产物，建议直接作为后续 `excel` 和 `workflow` 的输入。

建议字段：

- `template_id`
- `template_name`
- `template_version`
- `mapping_version`
- `excel_template_path`
- `field_definitions`
- `default_fields`
- `optional_fields`
- `target_fields`
- `excel_mappings`

说明：

- `target_fields` 是本次任务最终字段集合
- `default_fields` 和 `optional_fields` 继续保留，便于构造 `PromptFieldSet`

### 对下游的产出

template 层完成后，下游至少应能拿到：

- 模板元信息
- 最终字段集合
- 字段定义说明
- Excel 映射配置

### 验收标准

- 能列出系统支持的模板
- 能基于模板 ID 获取指定版本模板定义
- 能将默认字段与用户勾选字段合并为稳定、有序、去重的目标字段集合
- 能拿到字段到 Excel 的显式映射

---

## 第二阶段：`excel`

### 本阶段目标

在 template 层提供稳定字段结构后，实现一套只依赖结构化结果和映射配置的 Excel 写入能力。

### 建议优先实现的功能

1. 读取 Excel 模板文件
2. 校验映射配置是否合法
3. 按映射写入结构化字段
4. 对缺失值统一写入空字符串
5. 保留模板原有结构并生成输出文件
6. 返回输出文件信息和写入摘要

### 本阶段需要的数据结构

#### `StructuredInvoiceData`

建议字段：

- `data`
- `missing_fields`
- `extra_fields`

说明：

- 可以直接兼容 `src/services/llm/models.py` 中的 `StructuredExtractionResult`
- 进入 Excel 层前，应保证缺失字段已经统一标准化为空字符串

#### `ExcelWriteRequest`

建议字段：

- `template_id`
- `template_version`
- `mapping_version`
- `excel_template_path`
- `structured_data`
- `target_fields`
- `excel_mappings`
- `output_dir`

#### `ExcelWriteResult`

建议字段：

- `output_file_path`
- `written_fields`
- `skipped_fields`
- `missing_mappings`

### 对上游的输入要求

excel 层只应要求上游提供：

- 最终字段集合
- 字段写入映射
- 结构化结果
- 模板文件路径

### 对下游的产出

- 生成后的 Excel 文件路径
- 本次实际写入摘要

### 验收标准

- 能用一份 mock 结构化数据写入默认模板
- 缺字段时按空字符串写入
- 映射缺失时能给出明确错误或跳过摘要

---

## 第三阶段：`workflow`

### 本阶段目标

把已经稳定的 `template`、现有的 `llm`、以及 `excel` 串起来，先打通“图片输入 -> 字段提取 -> Excel 输出”的主链路。

在这一阶段，`document` 可以先用最小实现替代，只支持图片直通。

### 建议优先实现的功能

1. 定义 workflow 请求与结果对象
2. 定义 workflow 状态流转
3. 接入 template，获取 `TemplateBundle`
4. 将图片输入组装为 `PromptContext`
5. 调用 `LLMService.extract_structured_data(...)`
6. 对缺失字段统一补空字符串
7. 调用 excel 层生成输出文件
8. 汇总中间结果与最终结果
9. 将审计结果持久化到文件
10. 统一错误处理与阶段失败信息

### 本阶段建议依赖现有 LLM 接口

已存在的核心对象：

- `PromptFieldSet`
- `PromptContext`
- `StructuredExtractionResult`
- `LLMService`

workflow 的职责不是重写这些对象，而是负责把 template 和 document 的产物整理成它们需要的输入。

### 本阶段需要的数据结构

#### `WorkflowRequest`

建议字段：

- `task_id`
- `input_file_path`
- `template_id`
- `template_version`
- `selected_optional_field_ids`

说明：

- 缺失值策略已经统一为全局空字符串，不建议在 request 里再单独传 `missing_value`

#### `WorkflowAuditRecord`

建议字段：

- `task_id`
- `template_snapshot`
- `target_fields`
- `prompt_context`
- `llm_raw_text`
- `llm_cleaned_json`
- `excel_output_path`
- `document_manifest`
- `status_history`
- `error_info`

说明：

- 审计记录需要持久化到文件
- 即使在当前阶段 `document_manifest` 还比较简单，也建议先保留字段

#### `WorkflowResult`

建议字段：

- `task_id`
- `status`
- `structured_data`
- `excel_output_path`
- `audit_file_path`

#### `WorkflowStatus`

建议先至少包含：

- `created`
- `template_ready`
- `prompt_ready`
- `llm_processing`
- `json_validated`
- `excel_generating`
- `audit_persisted`
- `succeeded`
- `failed`

### 审计文件建议内容

建议 workflow 每次执行后在固定目录下生成审计文件，例如：

- `task_id`
- 输入文件路径与文件名
- 模板 ID / 模板版本 / 映射版本
- 最终字段集合
- prompt 上下文摘要
- LLM 原始返回
- 清洗后的结构化 JSON
- Excel 输出路径
- document manifest
- 错误栈或失败阶段
- 时间戳

### 本阶段最小可行链路

建议先实现这条最小主链路：

1. 输入图片文件路径
2. 选择模板
3. 合并字段
4. 组装 `PromptContext`
5. 调用 `LLMService.extract_structured_data(...)`
6. 将缺失字段标准化为空字符串
7. 把结果写入 Excel
8. 持久化审计文件
9. 返回结构化数据与 Excel 输出路径

### 验收标准

- 能基于图片发票完整跑通一次主链路
- 能返回结构化字段结果
- 能生成 Excel 文件
- 能把审计结果落盘
- 出错时能定位失败阶段

---

## 第四阶段：`document`

### 本阶段目标

在 workflow 已经支持图片主链路后，再补完整的文件预处理能力，让 workflow 不再只接收图片，而是统一接受图片和 PDF。

### 建议优先实现的功能

1. 文件类型识别
2. 图片文件直通
3. PDF 抽图或 PDF 转页图
4. 生成图像路径列表
5. 生成页码与图像的一一对应 manifest
6. 输出统一的 document 结果对象
7. 将结果接入 workflow，替代原来的图片直通 stub

### 本阶段需要的数据结构

#### `UploadedFileMeta`

建议字段：

- `file_name`
- `file_path`
- `content_type`
- `size`

#### `PageImageItem`

建议字段：

- `page_index`
- `image_path`
- `source_type`

说明：

- `source_type` 可标识来自原始图片还是 PDF 页面抽图

#### `DocumentManifest`

建议字段：

- `source_file_path`
- `file_type`
- `page_images`

#### `DocumentParseResult`

建议字段：

- `file_type`
- `image_paths`
- `page_indices`
- `manifest`

说明：

- `image_paths` 直接供 LLM 调用使用
- `page_indices` 直接供 `PromptContext` 使用
- `manifest` 用于审计与回溯

### 与 workflow 的衔接方式

workflow 后续只依赖：

- `image_paths`
- `page_indices`
- `manifest`

它不需要关心 PDF 是如何抽图的，也不需要关心底层使用哪种库。

### 验收标准

- 能识别图片文件与 PDF 文件
- 图片文件能按统一结构返回
- PDF 能返回稳定顺序的图像列表
- manifest 能追踪图像与页码对应关系

---

## 推荐的跨层数据流

建议最终主链路数据流如下：

1. `document` 输出 `DocumentParseResult`
2. `template` 输出 `TemplateBundle`
3. `workflow` 基于两者组装 `PromptContext`
4. `services/llm` 输出 `StructuredExtractionResult`
5. `excel` 消费结构化结果与映射配置，输出 `ExcelWriteResult`
6. `workflow` 持久化审计文件并汇总为 `WorkflowResult`

---

## 每层的先后依赖关系

### 可以先做 `template`

因为它决定字段契约，是整个系统的业务基础。

### `excel` 必须在 `template` 之后

因为 Excel 写入依赖：

- 最终字段集合
- 字段到单元格的映射
- 模板版本与映射版本

### `workflow` 适合在 `template` 和 `excel` 之后

因为它要消费：

- 模板字段结构
- Excel 输出能力
- 现有 LLM 能力
- 审计持久化规则

### `document` 可以放最后

因为主链路早期可以先使用图片发票测试。等 workflow 跑通后，再把 `document` 统一接进来，替换图片直通实现。

---

## 建议优先补的测试

### `template`

- 模板查询测试
- 模板版本查询测试
- 字段合并测试
- 去重与顺序稳定性测试
- 映射完整性测试

### `excel`

- 基于 mock 结构化结果的写入测试
- 空字符串缺失值写入测试
- 缺映射处理测试

### `workflow`

- 图片主链路集成测试
- LLM 返回缺字段时的标准化结果测试
- Excel 输出成功测试
- 审计文件落盘测试
- 阶段失败测试

### `document`

- 图片文件识别测试
- PDF 文件识别测试
- 页码顺序测试
- manifest 生成测试

---

## 当前阶段最值得先锁定的内容

在正式开始写 `template` 代码前，建议先最终确认以下内容：

- 系统内部字段统一使用 `field_id`
- 模板定义单独写在根目录 `template/` 下的 JSON 文件中
- Excel 映射按 `template_version` 和 `mapping_version` 管理
- 两个默认模板的必填字段以 `contexts/tmp.md` 为准，并整理进模板 JSON
- 缺失值默认策略统一为空字符串
- workflow 审计结果需要持久化到文件

这些问题一旦先定下来，后续四层实现会顺很多。

---

## 一句话结论

按 `template -> excel -> workflow -> document` 的顺序推进是合理的。你这次补充的信息实际上已经把当前阶段最关键的跨层契约补齐了，下一步可以直接进入 `template` 层的数据模型和 JSON 结构设计。
