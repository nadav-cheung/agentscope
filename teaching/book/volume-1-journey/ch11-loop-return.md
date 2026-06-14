# 第 11 站：循环与返回

> 天气 Agent 收到了工具结果"北京：晴，25°C"。它是不是直接把这个结果返回给用户？不是——它还要再思考一次，用自然语言回答"北京今天天气晴朗，气温 25 度"。这就是 ReAct 循环。

> **上一章：[第 10 站：执行工具](./ch10-toolkit.md)**

## 路线图

前几站我们追踪了 ReAct 循环的每一站：消息、Agent 收信、记忆、知识、格式化、模型调用、工具执行。现在我们站在最高层，看 `ReActAgent.reply()` 如何把它们串成一个**循环**。

```mermaid
flowchart TD
    A["reply() 收到消息"] --> B["存入工作记忆"]
    B --> C["检索长期记忆 + 知识库"]
    C --> D["for 循环 (最多 max_iters 次)"]
    D --> E["压缩记忆(如果需要)"]
    E --> F["_reasoning: 调用大模型"]
    F --> G{"模型返回了 ToolUseBlock？"}
    G -->|是| H["_acting: 执行工具"]
    H --> I["工具结果存入记忆"]
    I --> D
    G -->|否，只有文本| J["退出循环，返回回复"]
    D -->|"达到 max_iters"| K["_summarizing: 总结当前状态"]
    K --> J
```

读完本章，你会理解：
- `reply()` 的完整循环结构
- 循环的退出条件
- `_reasoning`、`_acting`、`_summarizing` 三个阶段
- 记忆压缩机制
- PlanNotebook 计划子系统

---

## 知识补全：结构化输出

有时候你不想要一段文字，而想要特定格式的数据。比如让模型返回 `{"city": "北京", "temp": 25, "condition": "晴"}`。

这就是**结构化输出（Structured Output）**：用 Pydantic BaseModel 定义期望的格式，模型会被强制按这个格式返回。

AgentScope 通过 `structured_model` 参数支持这个功能。内部实现是：把 Pydantic 模型伪装成一个"工具函数"，让模型以为自己要调用工具——从而获得结构化的 JSON。

---

## reply() 的骨架

打开 `src/agentscope/agent/_react_agent.py`，找到第 376 行：

```python
# _react_agent.py:376
async def reply(
    self,
    msg: Msg | list[Msg] | None = None,
    structured_model: Type[BaseModel] | None = None,
) -> Msg:
```

整个方法的骨架可以用伪代码表示：

```python
async def reply(self, msg, structured_model=None):
    # 1. 记录输入
    await self.memory.add(msg)

    # 2. 检索增强
    await self._retrieve_from_long_term_memory(msg)
    await self._retrieve_from_knowledge(msg)

    # 3. 结构化输出准备
    if structured_model:
        # 注册 generate_response 工具
        self.toolkit.register_tool_function(self.generate_response)
        self.toolkit.set_extended_model(self.finish_function_name, structured_model)
        tool_choice = "required"
    else:
        self.toolkit.remove_tool_function(self.finish_function_name)

    # 4. ReAct 循环
    for _ in range(self.max_iters):
        await self._compress_memory_if_needed()
        msg_reasoning = await self._reasoning(tool_choice)

        # 执行所有工具调用
        futures = [self._acting(tc) for tc in msg_reasoning.get_content_blocks("tool_use")]
        if self.parallel_tool_calls:
            results = await asyncio.gather(*futures)
        else:
            results = [await f for f in futures]

        # 检查退出条件
        if not msg_reasoning.has_content_blocks("tool_use"):
            return msg_reasoning    # 没有工具调用 → 退出

    # 5. 达到最大迭代次数 → 总结
    return await self._summarizing()
```

五个清晰的阶段。让我们逐个展开。

---

## 阶段 1：记录输入

```python
# _react_agent.py:408
await self.memory.add(msg)
```

把用户消息存入工作记忆。这是每次对话的起点。

---

## 阶段 2：检索增强

```python
# _react_agent.py:411-413
await self._retrieve_from_long_term_memory(msg)
await self._retrieve_from_knowledge(msg)
```

两个检索操作，对应上一站学到的长期记忆和知识库：

- `_retrieve_from_long_term_memory`（第 882 行）：如果 `static_control` 模式开启，用当前消息作为查询，检索长期记忆，结果作为 `user` 角色消息加入对话记忆
- `_retrieve_from_knowledge`（第 908 行）：如果配置了知识库，用当前消息检索相关文档，结果也作为 `user` 消息加入对话记忆

这两个检索发生在循环**之前**——每次 `reply` 只检索一次。

---

## 阶段 3：循环体

```python
# _react_agent.py:432
for _ in range(self.max_iters):
```

默认 `max_iters = 10`（第 197 行）。循环最多跑 10 轮。

### 3a. 记忆压缩

```python
# _react_agent.py:434
await self._compress_memory_if_needed()
```

`_compress_memory_if_needed`（第 1015 行）做的事：

1. 获取未压缩的消息
2. 保留最近 N 条消息不压缩（`keep_recent` 参数）
3. 计算待压缩消息的 Token 数
4. 如果超过阈值（`trigger_threshold`），用大模型把旧消息压缩成摘要

这是一种**滑动窗口 + 摘要**策略：最近的消息保持原样，太旧的被压缩。

### 压缩的完整流程

`_compress_memory_if_needed`（第 1015 行）的实际流程比上面的伪代码更精细：

```python
# _react_agent.py:1015-1137（简化）

# 1. 获取未压缩的消息
uncompressed = await self.memory.get_memory(exclude_mark=_MemoryMark.COMPRESSED)

# 2. 保留最近 N 条（keep_recent 参数）
# 关键：ToolUseBlock 和 ToolResultBlock 必须成对保留
to_keep = []
accumulated_tool_call_ids = set()
for msg in reversed(uncompressed):
    # 追踪工具调用配对关系
    for block in msg.get_content_blocks("tool_result"):
        accumulated_tool_call_ids.add(block["id"])
    for block in msg.get_content_blocks("tool_use"):
        accumulated_tool_call_ids.discard(block["id"])

    to_keep.append(msg)
    if len(accumulated_tool_call_ids) == 0:
        n_keep += 1
    if n_keep >= keep_recent:
        break

# 3. 计算待压缩消息的 Token 数
to_compress = uncompressed[:-len(to_keep)]
n_tokens = await token_counter.count(formatted_compress_msgs)

# 4. 超过阈值？→ 用大模型压缩
if n_tokens > trigger_threshold:
    summary = await model(prompt_with_compress_instruction,
                          structured_model=SummarySchema)
    await self.memory.update_compressed_summary(summary)
    # 标记旧消息为 COMPRESSED
    await self.memory.update_messages_mark(to_compress, _MemoryMark.COMPRESSED)
```

注意第 2 步中的 `accumulated_tool_call_ids`——它确保工具调用和工具结果不会被分开压缩。如果一对中的调用被压缩但结果被保留，模型会收到不完整的上下文。

### 3b. 推理：_reasoning

```python
# _react_agent.py:540
async def _reasoning(self, tool_choice=None) -> Msg:
```

这是"思考"阶段。核心流程：

```python
# 1. 如果有计划，插入计划提示
if self.plan_notebook:
    hint_msg = await self.plan_notebook.get_current_hint()
    await self.memory.add(hint_msg, marks=_MemoryMark.HINT)

# 2. 格式化消息
prompt = await self.formatter.format([
    Msg("system", self.sys_prompt, "system"),
    *await self.memory.get_memory(exclude_mark=_MemoryMark.COMPRESSED),
])

# 3. 调用大模型
res = await self.model(prompt, tools=self.toolkit.get_json_schemas(), tool_choice=tool_choice)

# 4. 处理流式/非流式响应
msg = Msg(name=self.name, content=[], role="assistant")
if self.model.stream:
    async for content_chunk in res:
        msg.content = content_chunk.content
        await self.print(msg, False)    # 流式打印
else:
    msg.content = list(res.content)

# 5. 存入记忆
await self.memory.add(msg)
return msg
```

注意 `_MemoryMark.HINT`——计划提示和系统提示是"临时"消息，用完就删：

```python
await self.memory.delete_by_mark(mark=_MemoryMark.HINT)
```

### 3c. 行动：_acting

```python
# _react_agent.py:657
async def _acting(self, tool_call: ToolUseBlock) -> dict | None:
```

这是"行动"阶段。对每个 `ToolUseBlock`：

```python
# 1. 创建工具结果消息
tool_res_msg = Msg("system", [ToolResultBlock(...)], "system")

# 2. 执行工具
tool_res = await self.toolkit.call_tool_function(tool_call)

# 3. 流式处理结果
async for chunk in tool_res:
    tool_res_msg.content[0]["output"] = chunk.content
    await self.print(tool_res_msg, chunk.is_last)

# 4. 结果存入记忆
await self.memory.add(tool_res_msg)
```

如果 `parallel_tool_calls = True`（第 440-445 行），多个工具会**并行执行**：

```python
futures = [self._acting(tc) for tc in tool_calls]
if self.parallel_tool_calls:
    results = await asyncio.gather(*futures)   # 并行
else:
    results = [await f for f in futures]       # 顺序
```

---

## 阶段 4：退出条件

循环有三种退出方式：

### 退出 1：模型只返回文本（没有工具调用）

```python
# _react_agent.py:496（简化）
elif not msg_reasoning.has_content_blocks("tool_use"):
    reply_msg = msg_reasoning
    break
```

当模型认为不需要调用工具、直接给出文字回答时，循环退出。

### 退出 2：结构化输出成功

```python
# _react_agent.py:455（简化）
if self._required_structured_model:
    if structured_outputs:
        structured_output = structured_outputs[-1]
        reply_msg = Msg(self.name, text_blocks, "assistant", metadata=structured_output)
        break
```

当模型调用了 `generate_response` 工具并成功生成结构化输出时，循环退出。

### 退出 3：达到最大迭代次数

```python
# _react_agent.py:525（简化）
if reply_msg is None:
    reply_msg = await self._summarizing()
```

循环跑完 `max_iters` 次还没有退出 → 调用 `_summarizing()` 让模型总结当前状态。

---

## 阶段 5：_summarizing

```python
# _react_agent.py:725
async def _summarizing(self) -> Msg:
```

这是一个"紧急出口"：告诉模型"你已经达到了最大迭代次数，请直接总结"。

```python
hint_msg = Msg("user",
    "You have failed to generate response within the maximum iterations. "
    "Now respond directly by summarizing the current situation.",
    role="user")
```

---

## 辅助子系统

### PlanNotebook（计划子系统）

```python
# _plan_notebook.py:172
class PlanNotebook(StateModule):
```

高级 Agent 可以在推理前制定计划。`PlanNotebook` 管理计划（`Plan`）和子任务（`SubTask`），在每轮推理时插入提示，引导 Agent 按计划执行。

### PlanNotebook 的完整工作流程

```mermaid
flowchart TD
    A["构造 ReActAgent 时传入 PlanNotebook"] --> B["注册计划工具到 Toolkit"]
    B --> C["每轮 _reasoning 开始"]
    C --> D["plan_notebook.get_current_hint()"]
    D --> E["插入 hint 到记忆（标记 HINT）"]
    E --> F["模型推理（看到当前计划进度）"]
    F --> G["_acting: Agent 可能调用计划工具"]
    G --> H["更新计划状态"]
    H --> I["删除 hint 消息（delete_by_mark HINT）"]
    I --> C
```

初始化时（第 328-348 行），PlanNotebook 的工具被注册到 Toolkit：

```python
# _react_agent.py:334（简化）
if enable_meta_tool:
    # 创建专用工具组，Agent 可以动态激活/停用计划工具
    self.toolkit.create_tool_group("plan_related", ...)
    for tool_func in plan_notebook.list_tools():
        self.toolkit.register_tool_function(tool_func, group_name="plan_related")
else:
    # 直接注册到 basic 组，始终可用
    for tool_func in plan_notebook.list_tools():
        self.toolkit.register_tool_function(tool_func)
```

每轮推理时（第 546-551 行），PlanNotebook 注入当前任务的提示：

```python
if self.plan_notebook:
    hint_msg = await self.plan_notebook.get_current_hint()
    await self.memory.add(hint_msg, marks=_MemoryMark.HINT)
```

推理完成后（第 566 行），hint 被清除，不会污染后续上下文：

```python
await self.memory.delete_by_mark(mark=_MemoryMark.HINT)
```

### TTS（语音合成）

`_reasoning` 和 `_summarizing` 中都有 TTS 处理。支持两种语音来源：

1. **模型原生输出音频**：多模态模型（如 Qwen-Omni）可以直接在响应中返回 `AudioBlock`
2. **TTS 后处理**：文字回答通过 TTS 模型转换为语音

```python
# _react_agent.py:579（简化）
tts_context = self.tts_model or _AsyncNullContext()

async with tts_context:
    # ... 模型推理 ...

    # 场景 1：模型原生输出音频
    speech = [block for block in msg.content if block.get("type") == "audio"]

    # 场景 2：TTS 合成
    if self.tts_model and not speech:
        speech = await self.tts_model.synthesize(msg)
```

TTS 模型本身是一个异步上下文管理器——它需要在整个推理过程中保持会话状态（比如维护 WebSocket 连接）。

---

## 并行工具执行详解

当模型一次返回多个 `ToolUseBlock` 时（比如同时查北京和上海的天气），`parallel_tool_calls` 参数控制执行方式：

```python
# _react_agent.py:440-451
futures = [self._acting(tc) for tc in tool_calls]

if self.parallel_tool_calls:
    results = await asyncio.gather(*futures)   # 并行执行
else:
    results = [await f for f in futures]       # 顺序执行
```

两种模式的区别：

| | 并行 (`asyncio.gather`) | 顺序 (`await` 循环) |
|---|---|---|
| 速度 | 快（所有工具同时运行） | 慢（一个接一个） |
| 资源 | 可能同时占用多个连接 | 每次只占一个连接 |
| 风险 | 工具之间有依赖时可能出问题 | 安全 |
| 默认值 | `False` | `False` |

默认是**顺序执行**（`parallel_tool_calls=False`，第 192 行）。这是因为大部分工具之间可能有隐式依赖——比如"查完天气再决定是否带伞"。只有在确定工具之间互不影响时才开启并行。

AgentScope 官方文档的 Building Blocks > Agent > ReActAgent 页面展示了 `ReActAgent` 的使用方法和配置参数（`max_iters`、`sys_prompt`、`model`、`toolkit`、`memory` 等）。本章解释了 `reply()` 中的完整 ReAct 循环、三种退出条件和 `_compress_memory_if_needed` 的压缩机制。

AgentScope 1.0 论文对 ReAct Agent 的推理循环设计说明是：

> "we ground agent behaviors in the ReAct paradigm and offer advanced agent-level infrastructure based on a systematic asynchronous design"
>
> — AgentScope 1.0: A Comprehensive Framework for Building Agentic Applications, arXiv:2508.16279, Section 2.2

---

## 完整的循环流程图

```mermaid
sequenceDiagram
    participant User as 用户
    participant Reply as reply()
    participant Memory as 工作记忆
    participant LTM as 长期记忆
    participant KB as 知识库
    participant Reason as _reasoning
    participant Act as _acting
    participant Model as 大模型
    participant Toolkit as 工具箱

    User->>Reply: Msg("北京天气如何？")
    Reply->>Memory: add(msg)
    Reply->>LTM: retrieve(msg)
    Reply->>KB: retrieve(msg)

    loop 最多 max_iters 次
        Reply->>Reply: _compress_memory_if_needed()
        Reply->>Reason: _reasoning()
        Reason->>Reason: formatter.format()
        Reason->>Model: model(prompt, tools)
        Model-->>Reason: ChatResponse

        alt 返回了 ToolUseBlock
            Reason-->>Reply: msg (含工具调用)
            Reply->>Act: _acting(tool_call)
            Act->>Toolkit: call_tool_function()
            Toolkit-->>Act: ToolResponse
            Act->>Memory: add(工具结果)
        else 只返回文本
            Reason-->>Reply: msg (纯文本)
            Note over Reply: 退出循环
        end
    end

    Reply-->>User: 最终回复
```

> **设计一瞥**：为什么 max_iters 默认是 10？
> 这是一个经验值。大多数简单任务在 2-3 轮内完成（推理 → 调工具 → 推理 → 回答）。复杂任务可能需要 5-8 轮。10 是一个合理的上限，防止 Agent 陷入无限循环。
> 用户可以根据任务复杂度调整：`ReActAgent(max_iters=3)` 适合简单任务，`ReActAgent(max_iters=20)` 适合复杂多步任务。

---

## 试一试：观察 ReAct 循环的次数

这个练习需要修改源码中的 `max_iters`。

**目标**：观察不同 `max_iters` 值对 Agent 行为的影响。

**步骤**：

1. 打开 `src/agentscope/agent/_react_agent.py`，找到第 432 行的循环：

```python
for _ in range(self.max_iters):
```

2. 在循环体开头加一行 print：

```python
for _ in range(self.max_iters):
    print(f"[DEBUG] ReAct 循环第 {_ + 1} 轮 (共 {self.max_iters} 轮)")
    await self._compress_memory_if_needed()
    ...
```

3. 在 `_reasoning` 方法（第 540 行后）加一行 print：

```python
msg_reasoning = await self._reasoning(tool_choice)
print(f"[DEBUG] 推理结果: {len(msg_reasoning.get_content_blocks('tool_use'))} 个工具调用, {len(msg_reasoning.get_content_blocks('text'))} 个文本块")
```

4. 如果你有 API key，运行天气 Agent 示例，观察 print 输出。
5. 如果没有 API key，直接阅读循环代码，数一数"北京天气"这个查询大概需要几轮循环（提示：推理 → 调用 get_weather → 推理 → 回答 = 2 轮）。

---

## 调试实践：追踪 _acting 的错误处理

`_acting` 方法（第 657 行）有一个值得学习的错误处理模式——`try/finally`，没有 `except`：

```python
# _react_agent.py:671-714（简化）
async def _acting(self, tool_call):
    tool_res_msg = Msg("system", [ToolResultBlock(...)], "system")

    try:
        tool_res = await self.toolkit.call_tool_function(tool_call)
        async for chunk in tool_res:
            tool_res_msg.content[0]["output"] = chunk.content
            ...
    finally:
        # 无论成功还是异常，都记录工具结果到记忆
        await self.memory.add(tool_res_msg)
```

为什么不用 `except`？因为工具执行的异常应该**向上冒泡**——让 `reply()` 方法知道出了问题。但工具结果消息**必须**被记录到记忆中，否则模型在下一轮推理时会看到一个没有结果的工具调用，导致 API 报错。

**调试步骤**：

1. 在 `_acting` 的 `finally` 块（第 712 行后）加一行 print：

```python
finally:
    print(f"[DEBUG] _acting 完成: tool={tool_call.get('name')}, "
          f"结果消息长度={len(str(tool_res_msg.content))}")
    await self.memory.add(tool_res_msg)
```

2. 如果你注册了一个会抛异常的工具函数（比如网络超时），观察 `finally` 块是否仍然执行，以及 `tool_res_msg` 中记录了什么。

**改完后恢复：**

```bash
git checkout src/agentscope/agent/_react_agent.py
```

---

## 检查点

你现在理解了：

- **ReAct 循环**是 `for _ in range(max_iters)` 的推理-行动循环
- 三个核心方法：`_reasoning`（思考）、`_acting`（行动）、`_summarizing`（紧急总结）
- 三种退出条件：模型只返回文本、结构化输出成功、达到最大迭代次数
- **记忆压缩**在每轮循环开始时检查，超过阈值就压缩旧消息
- **工具并行执行**：`asyncio.gather` 同时运行多个工具
- PlanNotebook 和 TTS 是可选的辅助子系统

**自检练习**：

1. 一个"查天气"的简单查询，ReAct 循环会跑几轮？每轮分别做了什么？
2. 如果 `max_iters=1`，Agent 还能完成"查天气"任务吗？为什么？（提示：回忆 `_summarizing` 在什么时候被调用）
3. 记忆压缩的"滑动窗口"策略保留了哪些消息不压缩？

> **参考答案**：
>
> 1. **恰好 2 轮**。贯穿示例的天气 Agent 注册了 `get_weather` 工具：第 1 轮 `_reasoning` 模型决定调用工具，返回 `ToolUseBlock` → `_acting` 执行工具、把结果存入记忆（因为有 tool_use，不 `break`，继续循环）；第 2 轮 `_reasoning` 模型基于工具结果返回纯文本回复（没有 tool_use）→ `break` 退出。这与本章"试一试"里"推理 → 调用 get_weather → 推理 → 回答 = 2 轮"一致。（只有当 Agent 没注册任何工具、模型直接用自身知识作答时，才是 1 轮。）
> 2. **不能正常完成**。"查天气"需要 2 轮（先调工具、再回答）。`max_iters=1` 时，第 1 轮模型返回 `ToolUseBlock`、执行完工具后因为还有 tool_use 而不会 `break`，循环随即到上限结束，`reply_msg` 仍为 `None`，于是走到 `_summarizing()`——Agent 得到的是"总结当前状态"的兜底回复，而不是正常的天气回答。所以需要工具的任务，`max_iters` 至少要 ≥ 2。
> 3. 滑动窗口保留**最近 `keep_recent` 条消息**不压缩（N 由配置决定），并且**成对保留工具调用与工具结果**（避免把一对拆开导致 API 报错）。只有超出窗口范围的旧消息才会被压缩成摘要。注意系统提示并不在工作记忆里（每次 `_reasoning` 都是新拼上去的），所以它根本不参与压缩。

---

## 下一站预告

我们已经追踪了一次完整的 `agent()` 调用，从消息诞生到循环返回。下一站是卷一的**复盘章**——我们拉远视角，画一张完整的全景图，把 8 个站点串联起来。

> **下一章：[旅程复盘](./ch12-journey-review.md)**