# 第 8 站：格式转换

> 消息在 Agent 内部用的是 `Msg` 对象，但 OpenAI API 要的是 `[{"role": "user", "content": "..."}]` 这样的 JSON——谁来负责翻译？

> **上一章：[第 7 站：检索与知识](./ch07-retrieval-knowledge.md)**

## 路线图

前几站我们追踪了消息从诞生到存储的路径。现在消息即将被发送给大模型，但有一个问题：**大模型 API 有自己要求的格式**。

```
Agent 内部: Msg(name="user", content=[TextBlock(...)], role="user")
                                    ↓
                          Formatter 翻译
                                    ↓
OpenAI API:  {"role": "user", "content": "北京今天天气怎么样？"}
```

这一站，我们打开 **Formatter（格式转换器）**，看翻译如何完成。

读完本章，你会理解：
- Formatter 的继承链：`FormatterBase` → `TruncatedFormatterBase` → `OpenAIChatFormatter`
- Token 截断策略：消息太长怎么办？
- 为什么 Formatter 独立于 Model（而不是 Model 自己做翻译）

---

## 知识补全：JSON Schema

Formatter 的输出是 JSON 字典列表。`{"role": "user", "content": "..."}` 这种结构就是 JSON。

JSON Schema 是一种描述 JSON 格式的规范——"这个字段必须是字符串""这个字段只能是 user/assistant/system 之一"。OpenAI API 就是用 JSON Schema 来定义请求格式的。

不需要深入了解 JSON Schema 规范。只要知道：**Formatter 的任务就是把 `Msg` 对象翻译成符合特定 API JSON 格式的字典列表**。

---

## 第一层：FormatterBase

打开 `src/agentscope/formatter/_formatter_base.py`：

```python
# _formatter_base.py:11
class FormatterBase:
    @abstractmethod
    async def format(self, *args, **kwargs) -> list[dict[str, Any]]:
        """把 Msg 对象格式化为 API 需要的字典列表"""
```

这就是全部的接口定义——**一个抽象方法**。输入是 `Msg` 列表，输出是字典列表。

还有一个实用静态方法：

```python
# _formatter_base.py:37
@staticmethod
def convert_tool_result_to_string(
    output: str | list[TextBlock | ImageBlock | AudioBlock | VideoBlock],
) -> tuple[str, list[tuple[str, Block]]]:
    """把工具结果拆成「文本」和「多模态数据」两部分（有些 API 不支持工具结果中的多模态数据）"""
```

当工具返回了图片或音频，但目标 API 不支持在工具结果中放多模态数据时，这个方法会把**文本部分**单独提取出来，同时把图片/音频等拆成一个 `(路径或 URL, Block)` 列表单独返回（前者是给模型的纯文本，后者留给 Formatter 决定怎么安置这些多模态数据）。

---

## 第二层：TruncatedFormatterBase

打开 `src/agentscope/formatter/_truncated_formatter_base.py`：

```python
# _truncated_formatter_base.py:19
class TruncatedFormatterBase(FormatterBase, ABC):
    def __init__(
        self,
        token_counter: TokenCounterBase | None = None,
        max_tokens: int | None = None,
    ): ...
```

这一层加入了**Token 截断**功能。看看核心的 `format` 方法：

```python
# _truncated_formatter_base.py:48
@trace_format
async def format(self, msgs: list[Msg], **kwargs) -> list[dict[str, Any]]:
    self.assert_list_of_msgs(msgs)
    msgs = deepcopy(msgs)    # 先深拷贝，不修改原始消息

    while True:
        formatted_msgs = await self._format(msgs)
        n_tokens = await self._count(formatted_msgs)

        if (
            n_tokens is None
            or self.max_tokens is None
            or n_tokens <= self.max_tokens
        ):
            return formatted_msgs

        # Token 数超标 → 截断旧消息 → 重新格式化
        msgs = self._truncate(msgs)
```

这是一个**循环截断**策略：

```mermaid
flowchart TD
    A[格式化消息] --> B[计算 Token 数]
    B --> C{Token 数 ≤ 上限？}
    C -->|是| D[返回格式化结果]
    C -->|否| E[截断旧消息]
    E --> A
```

关键点：`_format` 和 `_truncate` 都是抽象方法，由具体子类实现。

### TokenCounterBase

Token 计数器是一个独立的抽象：

```python
# _token_base.py:7
class TokenCounterBase:
    @abstractmethod
    async def count(self, messages: list[dict], **kwargs) -> int:
        """计算消息列表的 Token 数"""
```

为什么 Token 计数要单独抽象？因为不同模型计算 Token 的方式不同——GPT-4o 和 Claude 的 tokenizer 不一样。

---

## 第三层：OpenAIChatFormatter

打开 `src/agentscope/formatter/_openai_formatter.py`，找到第 168 行：

```python
# _openai_formatter.py:168
class OpenAIChatFormatter(TruncatedFormatterBase):
    support_tools_api: bool = True
    support_multiagent: bool = True
    support_vision: bool = True
    supported_blocks: list[type] = [
        TextBlock, ImageBlock, AudioBlock, ToolUseBlock, ToolResultBlock,
    ]
```

这个类声明了它支持的能力：工具调用 API、多 Agent 对话、视觉（图片）、以及支持哪些 ContentBlock 类型。

### format 方法的实际工作

`OpenAIChatFormatter._format()` 方法（大约在第 210 行开始）做这些事：

1. **遍历每条消息**，直接用 `msg.role` 和 `msg.name` 作为 OpenAI 消息的 `role` 和 `name` 字段
2. **处理消息中的每个 ContentBlock**，但不同 Block 的落点不同：
   - `TextBlock` → 进入消息的 `content` 列表：`{"type": "text", "text": "..."}`
   - `ImageBlock` → 进入消息的 `content` 列表：`{"type": "image_url", "image_url": {"url": "..."}}`
   - `ToolUseBlock` → 进入消息**独立的 `tool_calls` 字段**（不是 `content`）：`{"id": "...", "type": "function", "function": {"name": "...", "arguments": "..."}}`
   - `ToolResultBlock` → 生成一条**独立的 `tool` 角色消息**（不是当前消息的 content）：`{"role": "tool", "tool_call_id": "...", "content": "...", "name": "..."}`
3. **处理特殊的图片提升**：有些 API 不支持工具结果中带图片，`promote_tool_result_images=True` 会把图片提取到单独的用户消息中

```mermaid
flowchart LR
    subgraph 输入
        MSG["Msg(name='assistant', content=[TextBlock, ToolUseBlock])"]
    end

    subgraph Formatter 翻译
        MSG --> ROLE["role: 'assistant'"]
        MSG --> TB["TextBlock → content 列表"]
        MSG --> TUB["ToolUseBlock → tool_calls 字段"]
    end

    subgraph 输出
        ROLE --> OUT["{'role':'assistant', 'content':[...], 'tool_calls':[...]}"]
        TB --> OUT
        TUB --> OUT
    end
```

### 其他 Formatter 实现

AgentScope 为不同的模型 API 提供了不同的 Formatter：

```
src/agentscope/formatter/
├── _formatter_base.py              # 基类
├── _truncated_formatter_base.py    # Token 截断层
├── _openai_formatter.py            # OpenAI / GPT 系列
├── _anthropic_formatter.py         # Anthropic / Claude
├── _dashscope_formatter.py         # 阿里云通义千问
├── _gemini_formatter.py            # Google Gemini
├── _ollama_formatter.py            # Ollama 本地模型
├── _deepseek_formatter.py          # DeepSeek
└── _a2a_formatter.py               # Agent-to-Agent 协议
```

每个 API 对消息格式的要求略有不同。比如 Anthropic 把系统提示放在单独的 `system` 字段，而不是 `{"role": "system"}` 消息中。

> **设计一瞥**：为什么 Formatter 独立于 Model？
> 你可能觉得"格式转换应该是模型自己的事"。但把它们分开有一个大好处：**同一个 Formatter 可以搭配不同的模型**。
> 比如 `OpenAIChatFormatter` 适用于所有兼容 OpenAI API 的服务（OpenAI、DeepSeek、本地 Ollama 等）。
> 如果 Formatter 和 Model 绑定，换一个兼容服务就要写一个新的 Model 类。
> 代价：用户需要自己选择 Formatter 和 Model 的组合。详见卷四第 35 章。

---

## _truncate 截断策略深入分析

当 Token 数超过 `max_tokens` 时，`_truncate` 方法（第 151 行）负责裁剪消息。它的策略是**从旧到新删除消息对**，但有几条重要规则：

### 规则 1：系统提示不截断

```python
# _truncated_formatter_base.py:179-189
if len(msgs) > 0 and msgs[0].role == "system":
    if len(msgs) == 1:
        raise ValueError("系统提示已经超过 Token 限制！")
    start_index = 1   # 跳过系统提示，只截断后面的消息
```

系统提示（`sys_prompt`）是最重要的上下文，永远不被截断。如果连系统提示都超限了，直接报错。

### 规则 2：工具调用和结果成对删除

```python
# _truncated_formatter_base.py:193-207
tool_call_ids = set()
for i in range(start_index, len(msgs)):
    msg = msgs[i]
    # 遇到 ToolUseBlock → 加入待删除集合
    for block in msg.get_content_blocks("tool_use"):
        tool_call_ids.add(block["id"])

    # 遇到对应的 ToolResultBlock → 从集合中移除（配对完成）
    for block in msg.get_content_blocks("tool_result"):
        try:
            tool_call_ids.remove(block["id"])
        except KeyError:
            pass

    # 所有工具调用都配对完成 → 截断到当前位置
    if len(tool_call_ids) == 0:
        return msgs[:start_index] + msgs[i + 1:]
```

工具调用和工具结果必须成对出现，否则 API 会报错。所以截断时，代码追踪每个 `tool_call_id`，确保不会留下"只有调用没有结果"的消息。

### 规则 3：从旧到新删除

截断从最早的消息开始删除（`start_index = 1` 表示跳过系统提示，从第二条开始）。最近的消息被保留——因为最近的对话上下文最相关。

---

## Token 计数器

Token 计数器的实现在 `src/agentscope/token/` 中：

```python
# _token_base.py
class TokenCounterBase:
    @abstractmethod
    async def count(self, messages: list[dict], **kwargs) -> int:
        """计算消息列表的 Token 数"""
```

如果没有传入 `token_counter`，`_count` 方法返回 `None`，截断循环直接跳过——不会截断任何消息。这就是为什么你可以不设 `max_tokens` 和 `token_counter` 来使用 Formatter。

AgentScope 提供了基于 tiktoken（OpenAI 的分词器）的实现，也支持通过 API 远程计数（更精确但更慢）。

---

## 不同 Provider 的格式差异

虽然 `OpenAIChatFormatter` 适用于所有兼容 OpenAI API 的服务，但其他 Provider 有独特的格式要求：

| Provider | 系统提示 | 工具结果 | 多模态 |
|----------|---------|---------|--------|
| **OpenAI** | `{"role": "system", "content": "..."}` | `{"role": "tool", "tool_call_id": "...", "content": "..."}` | 支持 ImageBlock |
| **Anthropic** | 独立的 `system` 参数，不在 messages 中 | `{"role": "user", "content": [ToolResultBlock]}` | 支持 ImageBlock |
| **Gemini** | `{"role": "user", "parts": [{"text": "..."}]}` | 不同的 parts 结构 | 支持 ImageBlock |
| **Ollama** | 兼容 OpenAI 格式 | 兼容 OpenAI 格式 | 取决于模型 |

最大的差异在于**系统提示**和**工具结果**的处理。Anthropic 把系统提示放在请求的 `system` 字段（不在 `messages` 列表中），工具结果放在 `user` 角色消息中（不是 `tool` 角色）。这就是为什么每种 Provider 需要自己的 Formatter 子类。

---

## 调试实践：观察 Formatter 的格式化过程

这个练习不需要 API key。

### 技巧 1：观察消息分组

在 `_truncated_formatter_base.py` 的 `_group_messages` 方法中（第 260 行），加一行 print：

```python
for msg in msgs:
    print(f"[DEBUG] 消息: name={msg.name}, role={msg.role}, "
          f"有tool_use={msg.has_content_blocks('tool_use')}, "
          f"有tool_result={msg.has_content_blocks('tool_result')}")
```

运行 test_formatter.py，你会看到消息是如何被分组为 `agent_message` 和 `tool_sequence` 的。

### 技巧 2：观察截断效果

创建一个超长消息列表，测试截断行为：

```python
# 在 test_formatter.py 中替换消息列表
from agentscope.token import TokenCounterBase

class SimpleCounter(TokenCounterBase):
    """简单的字符计数器（不是真正的 Token 计数）"""
    async def count(self, messages, **kwargs):
        total = sum(len(str(m)) for m in messages)
        return total

formatter = OpenAIChatFormatter(
    token_counter=SimpleCounter(),
    max_tokens=100,  # 设置很小的限制
)

# 创建超过 100 字符的消息列表
msgs = [
    Msg("system", "你是助手。" + "x" * 50, "system"),
    Msg("user", "第一条很长的消息" + "y" * 50, "user"),
    Msg("assistant", "回答" + "z" * 50, "assistant"),
    Msg("user", "最新的短消息", "user"),
]

result = await formatter.format(msgs)
print(f"截断后剩余消息数: {len(result)}")
```

你会看到旧消息被截断，只保留系统提示和最新的消息。

**改完后恢复：**

```bash
rm test_formatter.py
git checkout src/agentscope/formatter/
```

AgentScope 官方文档的 Building Blocks > Models 页面展示了不同模型的使用方法。本章解释了 Formatter 的三层继承体系（FormatterBase → TruncatedFormatterBase → OpenAIChatFormatter）和 Token 截断循环的实现。

AgentScope 1.0 论文对 Formatter 与 Model 分离的设计说明是：

> "we abstract foundational components essential for agentic applications and provide unified interfaces and extensible modules"
>
> — AgentScope 1.0: A Comprehensive Framework for Building Agentic Applications, arXiv:2508.16279, Section 2.1

Formatter 的独立设计正是"可扩展模块"思想的体现——新增模型提供商只需要实现对应的 Formatter，不需要修改 Model 的代码。

---

## 试一试：观察 Formatter 的输入和输出

这个练习不需要 API key。

**目标**：直接调用 Formatter，看看它如何把 `Msg` 转换成 OpenAI 格式。

**步骤**：

1. 在项目根目录创建一个测试脚本 `test_formatter.py`：

```python
import asyncio
from agentscope.message import Msg, TextBlock, ToolUseBlock
from agentscope.formatter import OpenAIChatFormatter

async def main():
    formatter = OpenAIChatFormatter()

    # 创建几条消息
    msgs = [
        Msg(name="system", content="你是天气助手。", role="system"),
        Msg(name="user", content="北京天气如何？", role="user"),
        Msg(
            name="assistant",
            content=[
                TextBlock(type="text", text="让我查一下天气。"),
                ToolUseBlock(
                    type="tool_use",
                    id="call_123",
                    name="get_weather",
                    input={"city": "北京"},
                ),
            ],
            role="assistant",
        ),
    ]

    # 格式化
    result = await formatter.format(msgs)

    # 打印结果
    import json
    for msg in result:
        print(json.dumps(msg, ensure_ascii=False, indent=2))
        print("---")

asyncio.run(main())
```

2. 运行：

```bash
python test_formatter.py
```

3. 观察输出：每条消息如何被转换成 OpenAI API 的 JSON 格式。

4. **进阶**：在 `src/agentscope/formatter/_openai_formatter.py` 的 `_format` 方法中加一行 `print(f"[DEBUG] 格式化消息: {msg.name}")`，再运行一次，观察遍历过程。

**完成后清理：**

```bash
rm test_formatter.py
git checkout src/agentscope/formatter/
```

---

## 检查点

你现在理解了：

- **Formatter** 是 `Msg` 对象和模型 API 之间的翻译器
- 三层继承链：`FormatterBase`（接口）→ `TruncatedFormatterBase`（加 Token 截断）→ 具体实现（如 `OpenAIChatFormatter`）
- Token 截断是一个"格式化 → 计数 → 超标则截断旧消息 → 重新格式化"的循环
- Formatter 独立于 Model，使得同一格式转换可以复用于多个兼容模型

**自检练习**：

1. 如果不传 `token_counter` 和 `max_tokens`，`TruncatedFormatterBase.format()` 的 `while True` 循环会执行几次？（提示：看 `n_tokens` 为 `None` 时的判断）
2. AgentScope 提供了多少种 Formatter 实现？（提示：`ls src/agentscope/formatter/`）

> **参考答案**：
>
> 1. **恰好 1 次**。循环体内先调用 `_format` 格式化，再调用 `_count` 计数。当没有 `token_counter` 时，`_count` 返回 `None`，循环条件 `if n_tokens is None or ...` 立即满足，直接 `return formatted_msgs`，不会进入第二轮。
> 2. 可用 `ls src/agentscope/formatter/` 查看，当前有 7 个具体实现：`_openai_formatter.py`、`_anthropic_formatter.py`、`_dashscope_formatter.py`、`_gemini_formatter.py`、`_ollama_formatter.py`、`_deepseek_formatter.py`、`_a2a_formatter.py`。前 6 个都继承 `_truncated_formatter_base.py`（带 Token 截断），`_a2a_formatter.py` 直接继承 `_formatter_base.py`。

---

## 下一站预告

消息已经被格式化成 OpenAI API 需要的 JSON 了。下一站，我们追踪最核心的一步——**调用大模型**。看看 `ChatModelBase` 如何发送请求、接收响应、处理流式返回。

> **下一章：[第 9 站：调用模型](./ch09-model.md)**