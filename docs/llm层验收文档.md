# LLM层验收文档

## 验收范围

本文档用于汇总当前 `refactor/rec2form` 分支上 LLM 层已经完成的架构改造、Provider 接入、业务层能力落地、兼容层清理，以及当前遗留事项。

## 已完成内容

### 1. 完成 LLM 分层架构落地

当前 `src/integrations/llm/` 已按职责拆分为以下结构：

- `schema/`：统一请求、响应、消息、图像输入结构
- `capabilities/`：统一声明 provider 能力
- `base/`：抽象 provider 接口
- `providers/`：具体模型接入实现
- `factory/`：按配置或显式名称创建 provider

这一层的目标已经从“单个模型文件可调用”切换为“统一抽象下可替换 provider”。

### 2. 完成统一请求与响应模型

已实现的核心对象包括：

- `LLMImageInput`
- `LLMMessage`
- `LLMRequest`
- `LLMResponse`
- `LLMUsage`

其中 `LLMRequest.from_prompts(...)` 已支持将：

- `system_prompt`
- `user_prompt`
- `image_paths`
- `temperature`
- `max_tokens`
- `response_format`

统一组装为标准请求对象，供各 provider 消费。

### 3. 完成两个 Qwen Provider 的统一接入

当前已经存在并可用的 provider：

- `qwen_local_openai_compatible`
- `qwen_official`

对应实现文件：

- `src/integrations/llm/providers/qwen/local_openai_compatible.py`
- `src/integrations/llm/providers/qwen/official.py`

其中：

- 本地 provider 负责原图字节透传、base64 编码、OpenAI 兼容消息体构造、HTTP 异步调用、响应标准化
- 官方 provider 负责通过 `AsyncOpenAI` 调用官方兼容接口，并将响应转换成统一 `LLMResponse`

补充说明：

- `qwen_local_openai_compatible` 已取消 `thumbnail(...)` 缩放和 `JPEG quality` 重编码逻辑
- 本地 provider 现在与官方 provider 一致，按原始文件 MIME 类型读取原图字节并直接拼装 data URL
- 这样可以避免在进入模型前再次压缩画质，减少小字、印章、细表格线条等视觉信息损失

### 4. 完成官方 Qwen Provider 的图像输入支持

针对官方 provider 初始只支持文本消息的问题，现已补齐多模态能力：

- `supports_vision` 已改为 `True`
- `image_inputs` 会转换为兼容格式的 `messages[].content`
- 支持 `image_url + text` 的图文混合 user message
- 支持透传 `response_format`
- 包装类调用已支持 `image_paths`

同时增加了防御性校验：

- 当传入图片，但配置的模型名不是视觉模型时，会提前抛出清晰错误
- 避免把纯文本模型误当成 VL 模型调用

### 5. 完成 services/llm 业务层能力落地

当前 `src/services/llm/` 已承担业务层职责，不再直接混入 provider 协议细节。

已实现内容包括：

- `PromptContext`
- `PromptFieldSet`
- `StructuredExtractionResult`
- `prompt_builder.py`
- `json_parser.py`
- `service.py`

当前已支持：

- system prompt 生成
- user prompt 生成
- 目标字段拼装
- fenced JSON 清洗
- JSON 对象提取
- 多余字段过滤
- 缺失字段补齐
- 结构化结果输出

### 6. 完成旧兼容层清理

原先为兼容迁移保留的旧路径：

- `src/integrations/llm/core/model/qwen.py`
- `src/integrations/llm/core/model/qwen3_vl_8b_sspu.py`

现已删除，`src/integrations/llm/core/` 整个目录已清理完成。

同时清理了仍依赖该旧路径的过时脚本：

- `tests/scripts/resOCR_to_json_withLLM.py`

清理后，仓库内已不再保留 `src.integrations.llm.core` 的引用。

## 关键改动文件

本阶段重点涉及以下文件：

- `src/core/config.py`
- `src/integrations/llm/base/llm.py`
- `src/integrations/llm/capabilities/llm_capabilities.py`
- `src/integrations/llm/schema/message.py`
- `src/integrations/llm/schema/request.py`
- `src/integrations/llm/schema/response.py`
- `src/integrations/llm/factory/llm_factory.py`
- `src/integrations/llm/providers/qwen/local_openai_compatible.py`
- `src/integrations/llm/providers/qwen/official.py`
- `src/services/llm/models.py`
- `src/services/llm/prompt_builder.py`
- `src/services/llm/json_parser.py`
- `src/services/llm/service.py`
- `tests/unit/test_llm_architecture.py`
- `tests/unit/test_llm_service.py`

## 已完成验证

本阶段已执行并通过的验证包括：

- `python -m unittest tests.unit.test_llm_architecture`
- `python -m unittest tests.unit.test_llm_service`
- `python -m compileall src`
- `python3 -m py_compile src/integrations/llm/providers/qwen/local_openai_compatible.py`

当前单测已覆盖：

- `LLMRequest` 组装
- `LLMFactory` 创建 provider
- capability 校验失败路径
- 官方 provider 多模态消息构造
- 非视觉模型图像调用的防御性报错
- prompt 生成
- JSON 清洗与字段归一化

## 遇到的问题

### 1. 官方 provider 初始实现只有文本能力

最初 `src/integrations/llm/providers/qwen/official.py` 仅支持纯文本消息，未处理 `image_inputs`，也未声明 vision 能力。该问题已修复。

### 2. 旧 core 目录会干扰架构收口

虽然最初保留旧路径能减少迁移冲击，但在 provider 层稳定后，继续保留 `src/integrations/llm/core/` 会让调用入口不明确，增加维护成本，因此已整体删除。

### 3. 文档编码在当前终端下存在显示问题

原有 `docs/llm层验收文档.md` 在当前终端环境中存在乱码显示，因此本次对该文件进行了整体验收内容重写，并将阶段总结信息直接合并进来，避免重复维护两份文档。

### 4. 本地 provider 压缩画质会影响票据细节保真

`src/integrations/llm/providers/qwen/local_openai_compatible.py` 原先会在发送前执行缩放和 JPEG 重编码，这会让本地兼容链路与官方链路的输入保真度不一致。当前已调整为直接透传原图，统一两条 provider 链路的图像输入策略。

## 当前状态判断

到当前为止，LLM 层已经完成了以下目标：

- 分层边界已明确
- provider 已统一到新架构
- 官方与本地 provider 都具备图像处理能力
- 本地 provider 已改为原图透传，不再在 LLM 集成层做二次压缩
- `services/llm` 已承担 prompt 与 JSON 清洗职责
- 旧 `core` 路径已退出仓库

也就是说，LLM 层已经不再是“概念设计”阶段，而是进入“可接主业务工作流”的状态。

## 下一步建议

最自然的下一步是把这套 LLM 能力正式接入主工作流，包括：

- `src/services/document/` 的文件检测与 PDF 抽图产物
- `src/services/template/` 的模板字段与可选字段
- `src/services/workflow/` 的主链路编排
- `src/services/excel/` 的字段映射与填表

优先级上，建议先把 `workflow` 接起来，让 `PromptContext + LLMService.extract_structured_data(...)` 真正进入主流程。
