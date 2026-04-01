# LLM 层架构范式

## 目标

LLM 层需要解决的问题不是“直接调用某个模型”，而是为上层业务提供一套稳定、可扩展、可替换的统一抽象，使项目后续可以同时接入：

- `qwen` 官方 API
- 本地部署的 `qwen3-vl`
- 未来可能新增的其他兼容 OpenAI 协议或私有协议的模型

这套分层的核心目标是：

- 统一模型调用入口
- 显式表达模型能力差异
- 将请求/响应数据结构标准化
- 将具体厂商接入和上层业务解耦
- 让 `factory` 可以基于配置稳定切换模型

---

## 分层职责

### 1. `schema`

`schema` 是模型调用过程中的请求和响应数据模型层，负责定义“调用 LLM 时传递的标准数据结构”和“LLM 返回结果的标准数据结构”。

它解决的是“数据长什么样”的问题，而不是“模型怎么调用”的问题。

推荐职责：

- 定义统一的请求模型
- 定义统一的响应模型
- 定义消息结构
- 定义多模态输入结构
- 定义模型调用参数结构
- 定义错误响应或异常上下文结构

典型内容包括：

- `system_prompt`
- `user_prompt`
- `messages`
- `image_inputs`
- `temperature`
- `max_tokens`
- `response_format`
- `raw_response`
- `parsed_text`
- `usage`

建议理解方式：

- `schema` 是跨 provider 的公共语言
- `provider` 需要消费 `schema`，并产出符合 `schema` 的结果
- `base` 暴露的方法签名也应尽量基于 `schema`

`schema` 不负责：

- 判断模型是否支持图片
- 判断模型是否支持 JSON 输出
- 发起 HTTP 请求
- 做工厂选择
- 承担业务层 prompt 拼装逻辑

---

### 2. `capabilities`

`capabilities` 是模型能力描述层，负责定义某个模型“能做什么”“不能做什么”“需要满足什么约束”。

它解决的是“模型能力边界是什么”的问题。

例如一个模型可能：

- 支持图片输入
- 不支持图片输入
- 支持 `system prompt`
- 不支持单独的系统级提示词
- 支持结构化 JSON 输出
- 只支持文本输出
- 支持流式输出
- 不支持流式输出

推荐职责：

- 定义能力描述模型
- 定义模型特性开关
- 定义输入限制和输出限制
- 让上层在运行前就知道某个 provider 是否满足调用要求

典型字段可以包括：

- `supports_vision`
- `supports_system_prompt`
- `supports_json_output`
- `supports_stream`
- `supports_tools`
- `max_image_count`
- `max_input_tokens`
- `max_output_tokens`

建议理解方式：

- `capabilities` 是 provider 的能力声明
- `factory` 可以基于 `capabilities` 做筛选
- `services/llm` 可以基于 `capabilities` 进行前置校验或降级

`capabilities` 不负责：

- 发起模型调用
- 定义业务字段
- 解析业务 JSON

---

### 3. `base`

`base` 是抽象接口层，负责统一规定 LLM 对外暴露的能力边界，是整个 LLM 层的稳定入口契约。

它解决的是“上层应该如何调用模型”的问题。

`base` 的核心价值是：

- 上层只依赖抽象接口，不依赖具体厂商
- provider 必须遵守统一方法定义
- 替换模型时不需要修改业务编排层

推荐职责：

- 定义抽象基类或协议接口
- 统一暴露 `invoke`、`chat`、`generate` 等异步方法
- 统一输入输出类型
- 约束 provider 必须实现的能力查询方法

建议至少包含的接口概念：

- `async invoke(request: LLMRequest) -> LLMResponse`
- `get_capabilities() -> LLMCapabilities`
- `provider_name`
- `model_name`

如果后续需要，也可以补充：

- `async invoke_json(...)`
- `async stream(...)`
- `validate_request(...)`

但要注意：

- `base` 应保持薄且稳定
- 不要在 `base` 中写具体厂商逻辑
- 不要在 `base` 中写业务 prompt 模板

---

### 4. `providers`

`providers` 是具体模型接入层，负责把统一的 `schema` 请求转换成目标模型 API 所需的请求格式，再把模型原始响应转换回统一的 `schema` 响应。

它解决的是“某个具体模型到底怎么接”的问题。

这里会包含：

- 官方 API 接入
- 本地部署模型接入
- OpenAI 兼容协议模型接入
- 私有协议模型接入

每个 provider 都必须：

- 使用 `schema` 作为输入输出标准
- 符合 `base` 定义的抽象接口
- 提供自己的 `capabilities`
- 从 `src/core/config.py` 获取配置

推荐职责：

- 参数转换
- 请求构造
- HTTP 客户端调用
- 响应转换
- provider 级错误封装

不应放进 `providers` 的内容：

- 发票字段定义
- 模板字段拼装
- JSON 业务兜底清洗
- 工作流编排
- API 路由逻辑

可以把 `providers` 理解为“适配器层”：

- 向上适配 `base`
- 向下适配不同模型厂商协议

---

### 5. `factory`

`factory` 是模型选择层，负责根据配置、模型名称、能力要求或运行环境，返回一个符合 `base` 接口的 provider 实例。

它解决的是“当前应该使用哪个模型实现”的问题。

推荐职责：

- 根据配置构造默认模型
- 根据显式模型标识选择 provider
- 根据能力要求选择满足条件的 provider
- 屏蔽 provider 初始化细节

典型使用方式：

- 通过配置选择“官方 qwen”
- 通过配置选择“本地 qwen3-vl”
- 未来支持测试环境与生产环境使用不同 provider

`factory` 不负责：

- 拼装业务 prompt
- 处理业务字段映射
- 清洗 LLM JSON

---

## 各层之间的依赖关系

建议依赖方向如下：

- `schema` 为底层公共数据定义，可被 `base`、`providers`、`factory` 使用
- `capabilities` 为底层公共能力定义，可被 `base`、`providers`、`factory`、`services/llm` 使用
- `base` 依赖 `schema` 和 `capabilities`
- `providers` 依赖 `schema`、`capabilities`、`base`
- `factory` 依赖 `base`、`providers`、`capabilities`
- `services/llm` 依赖 `factory` 和 `schema`，不应反向侵入 provider 内部实现

推荐单向关系：

`schema/capabilities -> base -> providers -> factory -> services/llm`

需要强调的是：

- `services/llm` 属于业务服务层
- `providers` 属于外部模型接入层
- 二者不能混写

`services/llm` 负责：

- system prompt 组装
- user prompt 组装
- 模板字段拼装
- 结果 JSON 清洗
- 结果校验

`providers` 只负责：

- 调模型
- 收响应
- 转标准结构

---

## 推荐目录结构

结合当前项目 `src layout` 和 `AGENTS.md` 约束，建议在 `src/integrations/llm/` 下逐步演进为如下结构：

```text
src/integrations/llm/
├─ base/
│  └─ llm.py
├─ capabilities/
│  └─ llm_capabilities.py
├─ schema/
│  ├─ message.py
│  ├─ request.py
│  └─ response.py
├─ providers/
│  ├─ qwen/
│  │  ├─ official.py
│  │  └─ local_openai_compatible.py
│  └─ sspu/
│     └─ qwen3_vl_8b.py
└─ factory/
   └─ llm_factory.py
```

如果项目还处于快速迭代早期，也可以先采用较轻量的版本：

```text
src/integrations/llm/
├─ base.py
├─ capabilities.py
├─ schema.py
├─ factory.py
└─ providers/
   ├─ qwen_official.py
   └─ qwen_local.py
```

但从可维护性看，后续更推荐前一种拆分方式，尤其是在你已经明确要同时支持：

- qwen 官方 API
- 本地部署模型 API

这两类 provider 的协议相似但不会完全一样，尽早抽象更稳。

---

## 推荐数据流

后续标准调用链建议如下：

1. `src/services/llm/` 根据模板、字段和文件上下文组装 `system_prompt` 与 `user_prompt`
2. `services/llm` 创建统一的 `LLMRequest`
3. `services/llm` 调用 `factory` 获取目标模型实例
4. `factory` 返回符合 `base` 接口的 provider
5. provider 基于 `schema` 将请求转换成目标模型协议
6. provider 发起调用并获得原始响应
7. provider 将原始响应转换为统一的 `LLMResponse`
8. `services/llm` 再对结果进行 JSON 清洗、校验和业务化处理

这条链路要坚持一个原则：

- prompt 属于 `services/llm`
- 模型协议适配属于 `providers`

---

## 对 qwen 官方 API 和本地部署 API 的落地建议

针对你后续的开发目标，这套架构尤其适合以下两类实现：

### 1. qwen 官方 API provider

建议特点：

- 使用官方 SDK 或官方兼容接口
- 明确声明支持的能力
- 将官方响应映射为统一 `LLMResponse`

### 2. 本地部署 qwen provider

建议特点：

- 面向本地网关、OpenAI 兼容服务或私有 HTTP 接口
- 将图片、多模态消息、JSON 输出参数统一适配
- 将部署差异封装在 provider 内部

这样上层 `services/llm` 不需要关心：

- 当前是官方模型还是本地模型
- 当前是直连协议还是兼容协议
- 图片字段是 `image_url` 还是别的格式

---

## 开发约束

为了符合当前仓库规范，后续实现 LLM 层时建议严格遵守以下约束：

- 所有敏感配置统一从 `src/core/config.py` 读取
- `providers` 中不得散落 `os.getenv`
- `providers` 默认使用异步接口
- `services/llm` 不得直接拼接厂商专属请求体
- `routes` 不得直接调用具体 provider
- `factory` 返回值类型应为 `base` 抽象接口
- `schema` 和 `capabilities` 应尽量保持与业务无关
- 业务字段定义、模板字段选择、JSON 清洗逻辑应留在 `src/services/llm/`

另外，考虑到项目目标 Python 版本为 `3.9.25`，实现时要注意：

- 避免使用仅适用于较高 Python 版本的语法
- 类型标注尽量保持 `3.9` 兼容

---

## 一句话总结

这套范式的本质是：

- `schema` 定义数据
- `capabilities` 定义能力
- `base` 定义接口
- `providers` 定义接入实现
- `factory` 定义选择逻辑

最终让 `services/llm` 只面向统一抽象开发，而不用关心底层到底是 qwen 官方 API，还是本地部署模型 API。
