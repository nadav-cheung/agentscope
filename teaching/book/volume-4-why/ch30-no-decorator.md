# 第 30 章：为什么不用装饰器注册工具

> **难度**：入门
>
> LangChain 用 `@tool` 装饰器注册工具函数。AgentScope 用 `toolkit.register_tool_function(func)`。显式注册有什么好处？

> **上一章：[第 29 章 消息为什么是唯一接口](./ch29-msg-interface.md)**

## 决策回顾

AgentScope 的工具注册（`_toolkit.py:274`）：

```python
toolkit = Toolkit()

# 方式一：装饰器注册（其实是语法糖）
@toolkit.register_tool_function
def get_weather(city: str) -> ToolResponse:
    ...

# 方式二：方法调用注册
toolkit.register_tool_function(get_weather, func_name="weather")
```

装饰器方式看起来和 LangChain 的 `@tool` 很像，但本质不同——AgentScope 的装饰器是实例方法，绑定到特定的 `Toolkit` 实例。

---

## 被否方案：全局装饰器

**方案**：用全局装饰器注册，像 LangChain：

```python
@tool(name="get_weather", description="获取天气")
def get_weather(city: str) -> str:
    ...
```

**问题**：

1. **全局状态**：工具注册到全局注册表，多个 Agent 无法使用不同的工具集
2. **测试困难**：全局状态在测试之间泄漏，需要手动清理
3. **运行时灵活性差**：不能在运行时决定注册哪些工具

**场景示例**：

```python
# 全局装饰器的问题
@tool
def admin_delete_database():  # 管理员专用工具
    ...

# Agent A（普通用户）不应该有这个工具
agent_a = Agent(tools=?)  # 怎么排除？

# Agent B（管理员）才有
agent_b = Agent(tools=?)  # 怎么只包含？
```

---

## AgentScope 的选择：实例级注册

每个 `Toolkit` 实例维护自己的工具字典：

```python
# _toolkit.py:170-173
class Toolkit(StateModule):
    def __init__(self):
        self.tools: dict[str, RegisteredToolFunction] = {}
        self._middlewares: list = []
```

这意味着：

1. **不同 Agent 可以有不同的工具集**：

```python
admin_toolkit = Toolkit()
admin_toolkit.register_tool_function(delete_database)

user_toolkit = Toolkit()
user_toolkit.register_tool_function(query_database)

admin_agent = ReActAgent(..., toolkit=admin_toolkit)
user_agent = ReActAgent(..., toolkit=user_toolkit)
```

2. **运行时动态注册**：

```python
toolkit = Toolkit()
if user_has_access("weather"):
    toolkit.register_tool_function(get_weather)
if user_has_access("database"):
    toolkit.register_tool_function(query_db)
```

3. **测试隔离**：

```python
def test_tool():
    toolkit = Toolkit()  # 每个测试创建新实例
    toolkit.register_tool_function(my_tool)
    # 测试结束后 toolkit 被销毁，无全局污染
```

---

## 后果分析

### 好处

1. **无全局状态**：每个 Toolkit 实例独立
2. **运行时灵活性**：可以动态决定注册哪些工具
3. **多 Agent 场景**：不同 Agent 绑定不同工具集
4. **测试友好**：无需清理全局注册表

### 麻烦

1. **多写一行代码**：需要先创建 `Toolkit` 实例
2. **装饰器不能独立使用**：必须用 `@toolkit.register_tool_function`，不能脱离 toolkit

---

## 横向对比

| 框架 | 注册方式 | 作用域 |
|------|---------|--------|
| **AgentScope** | `toolkit.register_tool_function()` | 实例级 |
| **LangChain** | `@tool` 装饰器 | 全局 |
| **CrewAI** | 装饰器 + 类方法 | 类级 |
| **AutoGen** | 函数列表传参 | 实例级 |

AgentScope 和 AutoGen 都选择了实例级注册——这是多 Agent 场景的刚需。

AgentScope 官方文档的 Building Blocks > Tool Capabilities 页面展示了 `register_tool_function` 的基本用法——传入一个 Python 函数，框架自动从 docstring 和类型标注中提取参数描述并生成 JSON Schema。此外还展示了工具分组（Tool Group）和中间件（Middleware）的高级用法。

AgentScope 1.0 论文对工具系统的设计说明是：

> "flexible and efficient tool-based agent-environment interactions for building agentic applications"
>
> — AgentScope 1.0: A Comprehensive Framework for Building Agentic Applications, arXiv:2508.16279, Section 1

显式注册让同一个函数可以在不同的 Agent 实例中以不同的配置使用——这是多 Agent 场景的刚需。

---

---

## 验证性实验：对比装饰器 vs 显式注册

**目标**：体验两种注册方式的差异。

**步骤**：

1. 写一个简单的 `@tool` 装饰器实现（模拟 LangChain 风格），用它注册一个函数。

2. 再创建一个用 AgentScope 的 `register_tool_function` 注册的 Toolkit。

3. 尝试创建两个不同的 Agent，让它们各自拥有不同的工具集。`@tool` 方案能做到吗？AgentScope 方案呢？

**思考**：如果你需要同一个函数在两个 Agent 中有不同的名称/描述，哪种方案更容易实现？

---

## 你的判断

1. 全局装饰器的简洁性是否值得牺牲灵活性？
2. 如果同时支持两种方式（全局 + 实例级），会不会增加认知负担？

---

## 参数覆盖能力

`register_tool_function` 支持覆盖函数的原始名称和描述：

```python
# _toolkit.py:274
def register_tool_function(self, func, func_name=None, func_description=None):
```

这意味着同一个函数可以在不同的 Toolkit 中以不同的名字和描述注册：

```python
def search(query: str) -> ToolResponse:
    """搜索数据库"""
    ...

admin_toolkit.register_tool_function(search, func_name="admin_search")
user_toolkit.register_tool_function(search, func_name="public_search",
                                     func_description="搜索公开数据")
```

全局装饰器做不到这一点——`@tool(name="...")` 只能定义一次。实例级注册让同一函数在不同上下文中有不同的"面具"。

### 与 ch17 的关联

`register_tool_function` 内部调用 `_parse_tool_function`（`_utils/_common.py:339`）从函数签名自动生成 JSON Schema。参数覆盖发生在 Schema 生成之前——覆盖后的 `func_name` 和 `func_description` 会替换 docstring 解析出来的值。

---

## 试一试：体验实例级注册的优势

**目标**：验证不同 Toolkit 实例可以独立注册同一函数。

**步骤**：

1. 创建测试脚本：

```python
from agentscope.tool import Toolkit

def greet(name: str) -> str:
    """Say hello"""
    return f"Hello, {name}!"

# 两个独立的 Toolkit
toolkit_a = Toolkit()
toolkit_a.register_tool_function(greet)

toolkit_b = Toolkit()
toolkit_b.register_tool_function(greet, func_name="greet_formal",
                                  func_description="Formal greeting")

print(f"Toolkit A 的工具: {list(toolkit_a.tools.keys())}")
print(f"Toolkit B 的工具: {list(toolkit_b.tools.keys())}")
print(f"A 的 Schema: {toolkit_a.tools['greet'].json_schema}")
print(f"B 的 Schema: {toolkit_b.tools['greet_formal'].json_schema}")
```

2. 观察：两个 Toolkit 独立管理各自的工具注册，互不影响。

---

## 下一章预告

注册方式决定了"工具怎么来"。但工具相关的代码都塞在一个文件里——`_toolkit.py` 有 1500+ 行。这是上帝类还是合理的设计？下一章我们看模块拆分的权衡。

> **下一章：[第 31 章 上帝类 vs 模块拆分](./ch31-god-class.md)**