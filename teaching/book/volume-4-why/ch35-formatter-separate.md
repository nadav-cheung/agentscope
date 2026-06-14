# 第 35 章：为什么 Formatter 独立于 Model

> **难度**：中等
>
> 其他框架把消息格式转换和 API 调用放在同一个类里。AgentScope 把它们分成 `Formatter` 和 `Model` 两个独立的类。为什么？

> **上一章：[第 34 章 为什么用 ContextVar](./ch34-contextvar.md)**

## 决策回顾

```
Agent 调用流程：

Msg 列表 → Formatter.format() → dict 列表 → Model.__call__() → ChatResponse → Formatter → Msg
```

`Formatter` 负责 `Msg ↔ dict` 转换，`Model` 负责 HTTP 调用。它们是独立的对象，通过 Agent 的 `reply` 方法协调。

---

## 被否方案：合并为 Model

**方案**：格式转换逻辑内置在 Model 中：

```python
class OpenAIModel:
    def __init__(self, model_name, api_key):
        self.client = openai.OpenAI(api_key=api_key)

    async def __call__(self, msgs: list[Msg], tools=None):
        # 格式转换 + API 调用都在这里
        messages = self._convert_msgs(msgs)
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
        )
        return self._convert_response(response)

    def _convert_msgs(self, msgs):
        # OpenAI 格式转换
        result = []
        for msg in msgs:
            if msg.role == "system":
                result.append({"role": "system", "content": msg.content})
            ...
        return result
```

LangChain 和很多框架就是这样做的——`ChatOpenAI` 类同时处理格式和调用。

---

## 为什么分离

### 理由一：Ollama 兼容 OpenAI 格式

Ollama 的 API 兼容 OpenAI 格式，但 HTTP 调用方式不同：

```python
# 不分离时
class OllamaOpenAIModel:     # 格式 = OpenAI, 调用 = Ollama
class OllamaModel:            # 格式 = 自定义, 调用 = Ollama
class DeepSeekModel:          # 格式 = OpenAI, 调用 = DeepSeek

# 分离后
OpenAIChatFormatter + OllamaChatModel   # Ollama 用 OpenAI 格式
OllamaChatFormatter + OllamaChatModel   # Ollama 用自定义格式
OpenAIChatFormatter + OpenAIChatModel   # DeepSeek 走 OpenAI 兼容端点，直接复用 OpenAI 格式与模型（框架没有独立的 DeepSeekChatModel）
```

分离前需要 N × M 个类（N 种格式 × M 种 API）。分离后只需 N + M 个类。

### 理由二：独立测试

```python
# 测试格式转换——不需要 mock HTTP
formatter = OpenAIChatFormatter()
formatted = await formatter.format(msgs)
assert formatted[0]["role"] == "system"

# 测试 API 调用——不需要构造 Msg
model = OpenAIChatModel(...)
response = await model(formatted_dicts, tools=schemas)
```

### 理由三：独立替换

```python
# 运行时切换格式——不影响 Model
agent.formatter = AnthropicChatFormatter()  # 从 OpenAI 切换到 Anthropic 格式
# Model 不变，还是同一个 HTTP 客户端
```

```mermaid
flowchart LR
    subgraph "合并方案 (N × M)"
        A1["OpenAI 全栈类"]
        A2["Anthropic 全栈类"]
        A3["Ollama 全栈类"]
        A4["DeepSeek 全栈类"]
    end

    subgraph "分离方案 (N + M)"
        B1["OpenAIChatFormatter"] --- C1["OpenAIChatModel"]
        B1 --- C2["OllamaChatModel"]
        B3["DeepSeekChatFormatter"] --- C1
        B2["AnthropicChatFormatter"] --- C4["AnthropicChatModel"]
    end
```

---

## 后果分析

### 好处

1. **组合自由**：N + M 个类替代 N × M 个
2. **独立测试**：格式转换和 API 调用分别测试
3. **运行时替换**：可以动态切换格式化策略
4. **关注点分离**：Formatter 只关心格式，Model 只关心 HTTP

### 麻烦

1. **两处修改**：添加新模型 API 可能需要同时写 Formatter 和 Model
2. **协调复杂**：Formatter 和 Model 的接口需要匹配（stream 参数、tool_schema 格式等）
3. **额外概念**：开发者需要理解"为什么要两个类"

---

## 横向对比

| 框架 | 格式与调用 | 组织方式 |
|------|-----------|---------|
| **AgentScope** | 分离（Formatter + Model） | 正交分解 |
| **LangChain** | 合并（`ChatOpenAI` 等） | 按提供者分 |
| **LiteLLM** | 合并（统一接口） | 一个类适配所有 |
| **AutoGen** | 合并 | 按模型分 |

LiteLLM 的方案也有趣——用一个类适配所有 API，内部做格式转换。但扩展性不如 AgentScope 的分离方案。

AgentScope 官方文档的 Building Blocks > Models 页面展示了不同模型提供商的使用方法，包括 OpenAI、Anthropic、DashScope、Gemini、Ollama 等。每种模型可以搭配不同的 Formatter，实现格式与通信的分离。

AgentScope 1.0 论文对这一设计的说明是：

> "we abstract foundational components essential for agentic applications and provide unified interfaces and extensible modules, enabling developers to easily leverage the latest progress, such as new models and MCPs"
>
> — AgentScope 1.0: A Comprehensive Framework for Building Agentic Applications, arXiv:2508.16279, Section 2

Formatter 与 Model 的分离正是"可扩展模块"思想的体现——新增一个模型提供商只需要实现 `ChatModelBase` 和对应的 `FormatterBase`，两者独立演进。

---

---

## 验证性实验：测量 Formatter-Model 耦合度

**目标**：验证分离设计的组合自由度。

**步骤**：

1. 列出 `src/agentscope/formatter/` 下所有 Formatter 子类（OpenAI/Anthropic/DashScope/Gemini/Ollama/DeepSeek 共 6 个，外加 A2A）。

2. 列出 `src/agentscope/model/` 下所有 Model 子类（OpenAI/Anthropic/DashScope/Gemini/Ollama 等约 5 个）。

3. 理论上可能的组合数：6 × 5 = 30 种。实际可行的有多少种？

4. 尝试用 `OllamaChatModel` + `AnthropicChatFormatter` 组合——它能工作吗？为什么能/不能？

---

## 你的判断

1. LiteLLM 的"统一接口"方案是否比 AgentScope 的"分离方案"更简单？在什么场景下？
2. 如果未来的模型 API 全部兼容 OpenAI 格式，Formatter 还有存在的必要吗？

---

## 接口契约：Formatter ↔ Model 的匹配

分离的前提是两个类的接口必须匹配。实际契约：

```
Formatter.format(msgs) → list[dict]              # 只翻译消息，不管工具/流式
                              ↓
Model.__call__(messages, tools, tool_choice, stream) → ChatResponse   # 工具 schema 和流式由 Model 直接处理
                              ↓
Agent 直接读 ChatResponse.content / .id 构造 Msg   # 没有 Formatter.parse_response 这一步
```

关键匹配点：
1. **tools/tool_choice**：工具的 JSON Schema 由 `Toolkit.get_json_schemas()` 生成，**直接传给 `Model.__call__`**，不经过 Formatter（`Formatter.format` 只接收 `msgs`，返回纯消息字典列表）
2. **stream 参数**：流式/非流式是 `Model` 的职责，Formatter 不参与
3. **消息角色**：Formatter 把 `Msg.role` 映射为 API 的角色字段（OpenAI 的 "user"/"assistant"/"system"，Anthropic 的 "user"/"assistant"）

不匹配时的典型问题：Formatter 用 OpenAI 格式输出 `tool_result` 角色为 `"tool"`，但 Anthropic API 要求 `"user"` 角色。这正是 Formatter 存在的核心价值——抹平不同 API 的语义差异。

### 试一试：验证 Formatter 与 Model 的解耦

**目标**：确认可以独立替换 Formatter。

**步骤**：

1. 搜索 `Formatter` 和 `Model` 的匹配关系：

```bash
grep -n "formatter" src/agentscope/agent/_react_agent.py | head -5
grep -n "self.model" src/agentscope/agent/_react_agent.py | head -5
```

2. 观察 Agent 的 `reply` 方法中 Formatter 和 Model 是如何协调的——Formatter 在 Model 调用前后各出现一次。

---

## 下一章预告

我们看了 7 个具体的设计决策。最后一章，我们拉远视角，看整个架构的全景图和边界。

> **下一章：[第 36 章 架构全景与边界](./ch36-panorama.md)**