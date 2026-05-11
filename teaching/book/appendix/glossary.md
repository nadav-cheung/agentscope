# 附录 B：术语表

全书涉及的中英文术语对照。

---

## 核心概念

| 术语 | 英文 | 含义 |
|------|------|------|
| Agent | Agent | 能感知环境、做出决策、执行动作的自主实体 |
| 大语言模型 | LLM (Large Language Model) | 通过海量文本训练的生成式 AI 模型 |
| 工具调用 | Tool Calling / Function Calling | LLM 请求执行外部函数的机制 |
| Token | Token | 模型处理文本的基本单位（约 0.75 个英文单词或 1 个汉字） |
| 流式响应 | Streaming Response | 模型逐字/逐块返回结果，而非一次性返回 |
| 提示词 | Prompt | 发送给模型的输入文本 |

---

## Agent 模式

| 术语 | 英文 | 含义 |
|------|------|------|
| ReAct | Reasoning + Acting | 先推理再行动的循环模式 |
| 规划-执行 | Plan-Execute | 先生成完整计划，再逐步执行 |
| 观察 | Observe | Agent 接收其他 Agent 的消息但不回复 |
| 回复 | Reply | Agent 处理消息并返回结果 |

---

## 框架组件

| 术语 | 英文 | 含义 |
|------|------|------|
| 消息 | Msg | AgentScope 中统一的消息对象 |
| 内容块 | ContentBlock | 消息中的结构化内容（文本、图片、工具调用等） |
| 工作记忆 | Working Memory | 当前对话的短期记忆 |
| 长期记忆 | Long-term Memory | 跨会话的持久化记忆 |
| 格式转换器 | Formatter | 将 Msg 转换为模型 API 需要的格式 |
| 工具箱 | Toolkit | 管理工具函数的注册和调用 |
| 中间件 | Middleware | 包裹工具执行的拦截器 |
| Hook | Hook | 在方法前后自动执行的回调函数 |

---

## 设计模式

| 术语 | 英文 | 含义 |
|------|------|------|
| 策略模式 | Strategy Pattern | 统一接口 + 多种实现，运行时选择 |
| 模板方法 | Template Method | 定义算法骨架，子类填充细节 |
| 发布-订阅 | Pub-Sub | 发布者不直接发送给接收者，通过调度中心广播 |
| 洋葱模型 | Onion Model | 中间件层层包裹核心操作的执行模式 |
| 元类 | Metaclass | 创建类的类，可以拦截类定义过程 |
| 序列化 | Serialization | 将对象状态保存为可存储/传输的格式 |
| 正交分解 | Orthogonal Decomposition | 将两个独立的变化维度分离 |
| 外观模式 | Facade Pattern | 用简化接口封装复杂子系统 |
| 组合爆炸 | Combinatorial Explosion | N×M 个类 vs N+M 个类的选择问题 |
| 编译期注入 | Compile-time Injection | 在类定义时而非调用时注入行为 |
| 内聚性 | Cohesion | 模块内部元素之间的关联程度 |

---

## 框架对比

| 术语 | 英文 | 含义 |
|------|------|------|
| 全局装饰器 | Global Decorator | 注册到全局作用域的装饰器（如 @tool） |
| 实例级注册 | Instance Registration | 注册到特定实例，不同实例互不影响 |
| 运行时回调 | Runtime Callback | 在调用时传递的回调函数（如 LangChain callbacks） |

---

## Python 概念

| 术语 | 英文 | 含义 |
|------|------|------|
| 协程 | Coroutine | async def 定义的异步函数 |
| 事件循环 | Event Loop | asyncio 的执行引擎，调度协程 |
| 上下文变量 | ContextVar | 每个异步任务有独立副本的变量 |
| TypedDict | TypedDict | 带类型提示的字典类型 |
| 异步生成器 | AsyncGenerator | 用 async yield 产生值的生成器 |
| 深拷贝 | Deepcopy | 递归复制对象及所有嵌套对象 |

---

## 模型 API

| 术语 | 英文 | 含义 |
|------|------|------|
| JSON Schema | JSON Schema | 描述 JSON 数据格式的规范 |
| Chat Completions API | Chat Completions API | OpenAI 的对话 API |
| Messages API | Messages API | Anthropic 的对话 API |
| 结构化输出 | Structured Output | 让模型返回特定 JSON 格式 |
| 向量嵌入 | Embedding | 将文本转换为数值向量 |

---

## 可观测性

| 术语 | 英文 | 含义 |
|------|------|------|
| 追踪 | Trace | 记录请求从开始到结束的完整调用链 |
| 跨度 | Span | 追踪中的一个操作单元 |
| OpenTelemetry | OpenTelemetry | 云原生可观测性标准 |
