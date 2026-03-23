# LLM层验收文档

## 实现概述

本次重构围绕 `contexts/llm.md` 定义的分层目标，完成了 LLM 层的两阶段落地实现：

- `schema`：统一请求、响应、消息、图片输入结构
- `capabilities`：统一模型能力声明
- `base`：统一 provider 抽象接口
- `providers`：落地官方 `qwen` 与本地 `qwen3-vl` provider
- `factory`：基于配置或显式名称返回 provider
- `services/llm`：负责 prompt 组装、模型调用、JSON 清洗和结构化结果输出

同时保留了旧导入路径兼容层，使已有代码仍可通过原路径访问 `Qwen3MaxLLM` 和 `Qwen3VL8BSSPULLM`。

## 已完成功能

### 1. 统一分层骨架

新增目录：

- `src/integrations/llm/base/`
- `src/integrations/llm/capabilities/`
- `src/integrations/llm/schema/`
- `src/integrations/llm/providers/qwen/`
- `src/integrations/llm/factory/`
- `src/services/llm/`

### 2. 统一请求响应模型

已实现：

- `LLMImageInput`
- `LLMMessage`
- `LLMRequest`
- `LLMResponse`
- `LLMUsage`

其中 `LLMRequest.from_prompts(...)` 用于将上层常见的 `system_prompt/user_prompt/image_paths` 组装为统一请求对象。

### 3. 能力声明与工厂选择

已实现：

- `LLMCapabilities`
- `LLMFactory.create(...)`
- `get_llm_provider(...)`

当前支持：

- `qwen_official`
- `qwen_local_openai_compatible`

并支持基于能力做前置校验，例如视觉能力、JSON 输出能力。

### 4. provider 重构

#### 本地 qwen3-vl

将原有单体实现重构为：

- `src/integrations/llm/providers/qwen/local_openai_compatible.py`

它现在负责：

- 图片压缩与 base64 编码
- OpenAI 兼容消息体拼装
- HTTP 异步调用
- 原始响应转为统一 `LLMResponse`

#### 官方 qwen

新增：

- `src/integrations/llm/providers/qwen/official.py`

它现在负责：

- 基于 `AsyncOpenAI` 调用官方兼容接口
- 将响应转为统一 `LLMResponse`

### 5. services/llm 业务能力

新增：

- `src/services/llm/models.py`
- `src/services/llm/prompt_builder.py`
- `src/services/llm/json_parser.py`
- `src/services/llm/service.py`

当前已实现：

- `PromptContext` / `PromptFieldSet`：统一描述模板、字段、文件类型、页码和附加约束
- `build_system_prompt(...)`：按提示词规范构造系统提示词
- `build_user_prompt(...)`：按模板信息、字段集合和页码信息构造用户提示词
- `parse_structured_output(...)`：从模型输出中提取 JSON 对象
- `normalize_fields(...)`：过滤多余字段、补齐缺失字段、统一空值策略
- `LLMService.build_prompts(...)`
- `LLMService.parse_json_result(...)`
- `LLMService.extract_structured_data(...)`

### 6. 兼容迁移

旧路径：

- `src/integrations/llm/core/model/qwen.py`
- `src/integrations/llm/core/model/qwen3_vl_8b_sspu.py`

已改为兼容导出层，避免现有调用方在本次重构后立即失效。

## 代码改动说明

### 修改文件

- `.gitignore`
- `pyproject.toml`
- `src/core/config.py`

### 新增或重构文件

- `src/integrations/llm/__init__.py`
- `src/integrations/llm/base/__init__.py`
- `src/integrations/llm/base/llm.py`
- `src/integrations/llm/capabilities/__init__.py`
- `src/integrations/llm/capabilities/llm_capabilities.py`
- `src/integrations/llm/schema/__init__.py`
- `src/integrations/llm/schema/message.py`
- `src/integrations/llm/schema/request.py`
- `src/integrations/llm/schema/response.py`
- `src/integrations/llm/providers/__init__.py`
- `src/integrations/llm/providers/qwen/__init__.py`
- `src/integrations/llm/providers/qwen/official.py`
- `src/integrations/llm/providers/qwen/local_openai_compatible.py`
- `src/integrations/llm/factory/__init__.py`
- `src/integrations/llm/factory/llm_factory.py`
- `src/services/__init__.py`
- `src/services/llm/__init__.py`
- `src/services/llm/models.py`
- `src/services/llm/prompt_builder.py`
- `src/services/llm/json_parser.py`
- `src/services/llm/service.py`
- `src/integrations/llm/core/model/qwen.py`
- `src/integrations/llm/core/model/qwen3_vl_8b_sspu.py`
- `tests/test_llm_architecture.py`
- `tests/test_llm_service.py`

## 遇到的问题

### 1. 原文件编码读取异常

`contexts/llm.md` 初次读取时出现终端编码错乱，后续通过 UTF-8 重新读取解决，没有影响需求判断。

### 2. 现有实现职责混杂

原 `qwen3_vl_8b_sspu.py` 同时承担配置读取、图片处理、消息拼装、HTTP 调用、响应解析和业务调用接口，不利于后续同时支持多个 provider。本次通过 provider 化拆分解决。

### 3. 仓库 Python 版本声明不一致

`AGENTS.md` 目标是 Python `3.9.25`，但仓库文件中曾出现更高版本约束。本次统一恢复到 `>=3.9,<3.10`，使约束与项目目标一致。

### 4. 测试目录默认忽略

`.gitignore` 原先会拦住新增测试文件，本次补充白名单后才能纳入新的 LLM 单元测试。

### 5. Windows 环境下文本写入 BOM

在当前 PowerShell 环境中，直接使用 UTF-8 写文件会引入 BOM。本次额外做了无 BOM 重写，避免影响 Python 源文件头部。

## 验证结果

本次重构完成后，已补充结构级单元测试：

- `tests/test_llm_architecture.py`
- `tests/test_llm_service.py`

覆盖点包括：

- `LLMRequest` 组装
- `LLMFactory` provider 创建
- capability 校验失败路径
- prompt 构造
- fenced json 清洗
- 额外字段过滤
- 缺失字段补齐

已执行验证：

- `python -m unittest tests.test_llm_architecture tests.test_llm_service`
- `python -m compileall src tests`

说明：

- 本次未直接执行真实模型联网调用作为自动化验收，因为这依赖本地或远程模型服务地址、密钥和网络可达性。
- 结构上已为后续联调预留统一入口，联调时应优先验证 `qwen_local_openai_compatible` 与 `qwen_official` 两条调用链。

## 后续建议

- 在 `src/services/workflow/` 中接入 `PromptContext` 与 `LLMService.extract_structured_data(...)`
- 为 `factory` 增加按能力自动筛选 provider 的更完整逻辑
- 为本地 `qwen3-vl` provider 增加更严格的错误类型封装和超时重试策略
- 为真实接口调用补集成测试，并区分 mock 测试与联网联调测试
