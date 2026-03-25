# Services 分层重构规划

## 目标

本轮重构将 `src/services/` 的核心设计从“模板驱动识别字段”调整为“LLM 固定输出程序级标准 JSON，模板后置消费识别结果”。

重构后的主思路如下：

1. 系统预先定义一套全局稳定的标准 JSON。
2. `LLMService` 只面向这套固定中文键输出结构化结果，避免字段漂移。
3. 当前阶段先固定 LLM 识别契约，不提前绑定 Excel 最终表头策略。
4. 模板层不再负责限制 LLM 本次能抽哪些字段，而是在后续阶段消费这套标准 JSON。
5. Excel 层后续再基于这套标准 JSON 和模板映射生成输出。

这次调整的目标不是弱化结构化约束，而是把“识别约束”和“展示约束”解耦。

---

## 新的分层原则

### 1. `services/llm` 负责稳定输出标准 JSON

- LLM 输出的 key 必须固定为系统定义的中文键
- 不允许把模板中的表头名直接作为 LLM 输出 key
- 不允许不同模板驱动出不同命名风格的 JSON key
- LLM 的主要职责是“识别值”，不是“定义字段名”

### 2. `services/template` 在当前阶段先不反向约束 LLM 输出

- 模板不再决定 LLM 输出哪些 key
- 模板后续只消费标准 JSON 并生成导出方案
- 模板仍可保留默认模板元信息与映射资源
- 模板不再对白名单外字段做“是否允许抽取”的强约束

### 3. `services/excel` 后续负责把标准 JSON 写成目标表格

- 当前阶段先不把 Excel 表头方案并入 LLM 契约
- Excel 后续根据模板映射和标准 JSON 生成目标表格
- Excel 不参与字段识别和字段合法性推断

### 4. `services/workflow` 负责主链路编排

- `document` 输出图像与 manifest
- `llm` 输出固定标准 JSON
- `template` 输出导出列方案和布局
- `excel` 负责导出结果文件
- `workflow` 负责审计、状态推进和错误汇总

---

## 核心设计结论

### 1. 固定一套全局标准 JSON 定义

系统必须维护一套全局唯一的标准 JSON 契约，建议以独立配置或文档形式维护，例如：

- `template/standard_fields.json`
- `contexts/tmp.md`

当前已确认的标准 JSON key 为：

- `发票代码`
- `发票号码`
- `开票日期`
- `购买方名称`
- `购买方纳税人识别号`
- `购买方地址电话`
- `购买方开户行及账号`
- `货物或应税劳务、服务名称`
- `规格型号`
- `单位`
- `数量`
- `单价`
- `金额`
- `税率`
- `税额`
- `合计`
- `价税合计(大写)`
- `销售方名称`
- `销售方纳税人识别号`
- `销售方地址电话`
- `销售方开户行及账号`
- `收款人`
- `复核`
- `开票人`
- `销售方`
- `备注`

其中：

- 这些中文键本身就是当前阶段的程序级稳定 key
- `LLMService` 必须严格按这些 key 返回 JSON
- 模板表头、Excel 字段名、前端展示名暂时都不能反向影响这些 key

### 2. 模板从“识别字段定义”降级为“展示方案定义”

模板文件不再维护：

- `default_field_ids`
- `optional_field_ids`

模板文件改为维护：

- `template_id`
- `template_name`
- `template_version`
- `mapping_version`
- `excel_template_path`
- `recommended_field_ids`
- `default_header_labels`
- `excel_mappings`

说明：

- `recommended_field_ids` 是该模板默认建议展示的字段集合
- `default_header_labels` 是模板级表头名覆盖
- `excel_mappings` 仍然负责 `field_id -> sheet/cell`

如果后续还需要区分“默认展示字段”和“可扩展字段”，建议使用：

- `default_selected_field_ids`
- `available_field_ids`

但它们只用于展示选择，不再用于限制 LLM 输出字段合法性。

### 3. 当前阶段先固定识别契约，再处理用户选列

当前阶段优先级如下：

1. 先固定 LLM 层输出这组中文键。
2. 先移除“模板 optional 白名单决定识别字段”的思路。
3. `selected_field_ids`、模板推荐列、表头覆盖策略作为下一阶段能力接入。

### 4. 表头与导出策略属于后续阶段

在当前文档版本中，表头覆盖、模板推荐列、Excel 导出列优先级均属于后续设计，不应回写到 LLM 标准 JSON 契约中。

当前已确认的 Excel 输出侧默认表头预置方案如下：

#### 模板1：财务系统录入发票字段

- `序号`
- `发票号码`
- `发票代码`
- `发票金额`
- `备注`

#### 模板2：大创低值材料资产入库模板自动导入

- `低值材料分类号`
- `资产名称`
- `品牌`
- `规格型号`
- `单位`
- `数量`
- `单价`
- `总价`
- `供应商`
- `发票编号`
- `开票日期`
- `存放地址`
- `备注`

这些字段属于 Excel 输出侧供用户选择的默认表头集合，不参与 LLM 固定中文键的定义。

### 5. LLM 输出仍应受控，不建议输出“自由字段”

这次重构不是让 LLM 返回任意原始字段名，而是让它严格输出上面这组固定中文键。

当前阶段建议：

- prompt 明确要求输出完整标准 JSON
- JSON key 必须与标准契约逐字一致
- 缺失值填空字符串
- 不因模板不同改变 key 集合

当前阶段的核心不是压缩字段集合，而是先把程序内部识别契约固定下来。

---

## 分层改造方案

## 第一阶段：标准字段层

### 目标

先固化系统唯一认可的标准 JSON，作为 LLM 输出的统一契约。

### 需要落地的内容

1. 新增全局标准 JSON 配置文件
2. 定义标准 JSON 数据模型
3. 增加标准 JSON 加载与校验服务
4. 固定并校验所有中文 key

### 建议数据结构

#### `StandardJsonSchema`

- `keys: List[str]`
- `required_keys: List[str]`
- `default_missing_value`
- `version`

### 产出

- 可被 `llm`、`template`、`excel`、`workflow` 共同使用的标准 JSON 契约定义

### 验收标准

- 能加载标准 JSON 配置文件
- 能校验中文 key 是否唯一且完整
- LLM 输出可按这组中文 key 完成补空和清洗
- 不存在重复或缺失的标准 key

---

## 第二阶段：模板层重构

### 目标

将模板层从“识别字段约束层”重构为“导出展示方案层”。

### 需要移除或弱化的旧职责

- 移除模板对白名单外 optional 字段的识别限制
- 不再使用 `selected_optional_field_ids` 作为主要导出输入
- 不再以模板字段集合决定 LLM 输出字段 key

### 需要新增的能力

1. 读取模板推荐列方案
2. 读取模板默认表头名
3. 基于标准字段校验模板引用是否合法
4. 根据用户的 `selected_field_ids` 构造最终导出字段列表
5. 输出 Excel 所需映射和表头策略

### 建议数据结构

#### `TemplateDefinition`

- `template_id`
- `template_name`
- `template_version`
- `mapping_version`
- `excel_template_path`
- `recommended_field_ids`
- `available_field_ids`
- `default_header_labels`

#### `TemplateBundle`

- `template_id`
- `template_name`
- `template_version`
- `mapping_version`
- `excel_template_path`
- `recommended_fields`
- `selected_fields`
- `field_definitions`
- `resolved_header_labels`
- `excel_mappings`
- `all_excel_mappings`

### 行为规则

- `selected_fields` 来自用户传入或模板推荐值
- `resolved_header_labels` 按“用户覆盖 > 模板默认 > 标准字段默认”计算
- 模板引用的字段必须全部存在于标准字段字典中
- 模板映射只校验自身使用到的字段，不再承担 LLM 字段合法性白名单职责

### 验收标准

- 能列出系统模板
- 能按模板读取推荐列方案
- 能校验模板引用字段均存在于标准字段字典
- 能根据 `selected_field_ids` 生成稳定有序去重后的导出字段列表
- 不再因为字段不属于模板 optional 列表而报旧式错误

---

## 第三阶段：LLM 层重构

### 目标

让 `LLMService` 输出基于固定中文键的稳定 JSON，并保留足够的原始响应审计信息。

### 需要调整的内容

1. `PromptContext` 不再依赖模板 default/optional 字段语义
2. prompt 直接要求模型返回固定中文键 JSON
3. JSON 解析器只面向这组中文键做标准化
4. 保留模型原始文本与清洗后的 JSON

### 建议数据结构

#### `StructuredExtractionResult`

- `data`
- `raw_text`
- `cleaned_text`
- `extra_fields`
- `missing_fields`

这里的 `data` 必须是固定中文键对应的值。

### 行为规则

- system prompt 中明确要求只输出固定中文键
- user prompt 中明确要求输出完整标准 JSON
- 如果模型返回额外字段，保留在 `extra_fields` 中用于审计
- 如果模型漏字段，则统一补空字符串

### 验收标准

- prompt 中不再出现模板 optional 字段语义
- LLM 解析结果 key 必须与标准中文键逐字一致
- 额外字段会被识别并记录，但不会破坏标准结果
- 缺失字段统一标准化为空字符串

---

## 第四阶段：Excel 层重构

### 目标

Excel 层只消费标准字段结果、字段选择结果和表头覆盖策略，生成最终文件。

### 需要调整的内容

1. `ExcelWriteRequest` 改为接收 `selected_field_ids`
2. 支持 `header_label_overrides`
3. 支持解析后的 `resolved_header_labels`
4. 不再依赖模板 default/optional 二分法做表头控制

### 建议数据结构

#### `ExcelWriteRequest`

- `template_id`
- `template_version`
- `mapping_version`
- `excel_template_path`
- `structured_data`
- `selected_field_ids`
- `resolved_header_labels`
- `excel_mappings`
- `all_excel_mappings`
- `output_dir`
- `output_filename`

### 行为规则

- 只为 `selected_field_ids` 写表头和数据
- 未选字段清空表头与数据单元格
- 表头按 `resolved_header_labels[field_id]` 写入
- 数据值来自标准字段 JSON

### 验收标准

- 能按用户选择字段导出 Excel
- 能按用户自定义表头写表头
- 未覆盖时可回退到模板默认表头
- 未被选择的字段不会出现在导出结果中

---

## 第五阶段：Workflow 层重构

### 目标

将主链路输入切换为“标准字段选择 + 表头覆盖”，统一驱动识别与导出。

### 建议请求结构

#### `WorkflowRequest`

- `task_id`
- `input_file_path`
- `template_id`
- `template_version`
- `selected_field_ids`
- `header_label_overrides`
- `extra_instructions`

### 新的主链路

1. `document` 解析文件并输出图像与 manifest
2. `template` 加载模板推荐列方案和布局
3. `workflow` 计算本次最终 `selected_field_ids`
4. `workflow` 构造面向标准字段的 `PromptContext`
5. `llm` 输出标准字段 JSON
6. `excel` 根据 `selected_field_ids` 和 `resolved_header_labels` 导出
7. `workflow` 落审计文件

### 审计文件建议补充

- `selected_field_ids`
- `resolved_header_labels`
- `standard_field_version` 或字段字典快照

### 验收标准

- 主链路可基于 `selected_field_ids` 跑通
- 不再依赖 `selected_optional_field_ids`
- 审计文件可回溯本次识别字段和表头策略
- 失败时仍能保留已完成阶段与错误信息

---

## 迁移顺序建议

建议按以下顺序推进：

1. 新增标准字段配置与注册表
2. 重构模板 JSON 结构
3. 调整 `TemplateService`
4. 调整 `PromptContext` 与 `LLMService`
5. 调整 `ExcelWriteRequest` 与 `ExcelService`
6. 调整 `WorkflowRequest` 与 `WorkflowService`
7. 调整测试与验收文档

原因：

- 先定字段契约，后改模板
- 先定模板输出契约，后改 LLM 和 Excel 消费方式
- 最后再切 workflow，避免中途主链路长期不可用

---

## 兼容性与风险

### 1. 兼容旧模板文件

如果需要平滑迁移，可短期兼容旧字段：

- `default_field_ids`
- `optional_field_ids`

但应明确这是临时兼容，不应继续扩展旧模型。

### 2. LLM 输出字段过多的风险

如果一次请求字段过多，模型稳定性会下降。当前建议优先采用：

- 识别字段 = 当前用户选择字段 + 必要公共字段

而不是一次性全量抽所有标准字段。

### 3. 用户完全自由改表头不等于自由改字段

用户可以改表头名，但不能改底层 `field_id` 语义。否则会重新引入字段漂移。

---

## 本轮重构完成后的预期结果

完成后系统应达到以下状态：

- 字段 key 稳定，模板变化不影响 LLM 输出结构
- 用户选择列时不再受模板 optional 白名单限制
- 模板只负责常用展示方案和默认表头
- Excel 导出逻辑更直接，职责更清晰
- workflow 审计可明确区分“识别字段选择”和“表头展示策略”

---

## 一句话结论

本轮 services 层重构应以“LLM 固定输出程序级标准 JSON”为第一优先级推进，模板消费和 Excel 展示策略放在后续阶段逐步接入。
