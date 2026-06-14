# 附录 A：Python 进阶速查

本附录汇总全书涉及的 Python 进阶概念，供查阅。

> **上一章：[第 36 章 架构全景与边界](../volume-4-why/ch36-panorama.md)**

---

## async/await

`async`（asynchronous，异步）定义异步函数，`await` 等待异步操作完成。

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)  # 模拟 IO（Input/Output，输入输出）等待
    return "data"

async def main():
    result = await fetch_data()
    print(result)

asyncio.run(main())
```

**要点**：
- `async def` 定义的函数是**协程**，不会立即执行
- `await` 暂停当前协程，让事件循环执行其他任务
- `asyncio.run()` 启动事件循环
- `asyncio.gather()` 并发执行多个协程

---

## TypedDict

### 先看普通 dict

`dict`（dictionary，字典）是 Python 最常用的数据结构——键值对容器：

```python
# 创建 dict 的两种写法
user = {"name": "Alice", "age": 30}
user = dict(name="Alice", age=30)

# 读写字段
print(user["name"])        # "Alice"
user["email"] = "a@x.com"  # 随意加字段
print(user["country"])     # KeyError! 访问不存在的键会崩溃
```

dict 的痛点是**没有约束**：字段名可能拼错、值类型可能搞混、IDE（Integrated Development Environment，集成开发环境）无法补全。

### TypedDict 解决了什么

`TypedDict` 给 dict 加上**类型契约**——告诉类型检查器和 IDE 这个 dict 该有哪些字段、各自是什么类型：

```python
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int

# 创建方式和普通 dict 完全一样
u: User = {"name": "Alice", "age": 30}  # OK
u = User(name="Alice", age=30)          # OK（TypedDict 特有写法）

# 运行时就是普通 dict
print(type(u))   # <class 'dict'>

# 类型检查器（mypy/pyright）会报错：
u = User(name="Alice", age="三十")  # ❌ age 应该是 int
u = User(name="Alice")             # ❌ 缺少 age（默认必填）
u = User(name="Alice", age=30, foo="bar")  # ❌ foo 不是合法字段
print(u["namee"])  # ❌ 拼写错误
```

**核心对比**：

| | 普通 `dict` | `TypedDict` |
|---|---|---|
| 运行时行为 | dict | dict（完全一样） |
| 字段约束 | 无 | mypy/pyright 检查 |
| IDE 补全 | 无 | 有（输入 `u["` 会提示 `name`/`age`） |
| 拼写错误 | 运行时报 `KeyError` | **编码时就报错** |
| 序列化（JSON） | `json.dumps()` | `json.dumps()`（零成本） |
| 创建开销 | 极低 | 极低（相同） |

### 可选字段：total=False

```python
from typing import TypedDict

class UserProfile(TypedDict, total=False):
    name: str
    age: int        # 现在 age 也是可选的
    bio: str        # 所有字段都是可选的

# total=False：所有字段都是可选的
u = UserProfile(name="Bob")          # OK，age 和 bio 可以不写
u = UserProfile()                     # OK，甚至全空也行
```

### 部分可选：Required

Python 3.11+ 支持混合必填和可选字段：

```python
from typing import TypedDict, Required

class ToolUseBlock(TypedDict, total=False):
    id: Required[str]       # 必填（覆盖了 total=False）
    name: Required[str]     # 必填
    input: Required[dict]   # 必填
    raw_input: str          # 可选——可选项是 total=False 带来的（键可以不存在），跟类型里写不写 | None 无关

# id、name、input 必填，raw_input 可选
block: ToolUseBlock = {"id": "1", "name": "search", "input": {"q": "hi"}}  # OK

block = ToolUseBlock(id="1", name="search", input={})  # OK
block = ToolUseBlock(id="1")                            # ❌ 缺少 name、input
```

**要点**：
- 运行时全部是普通 `dict`，只在开发期做类型检查
- TypedDict 适合"数据容器"场景——不需要方法，只需要字段
- 如果要运行时验证，用 Pydantic `BaseModel` 而非 TypedDict

---

## ContextVar

`ContextVar`（Context Variable，上下文变量）为每个异步任务提供独立的变量副本。

```python
from contextvars import ContextVar

user_id: ContextVar[str] = ContextVar("user_id", default="")

async def handle_request(name):
    user_id.set(name)
    await asyncio.sleep(0.1)
    print(f"{user_id.get()} processing")  # 不受其他任务影响

async def main():
    await asyncio.gather(
        handle_request("Alice"),
        handle_request("Bob"),
    )
```

---

## 元类（Metaclass）

元类是"创建类的类"。可以拦截类定义过程，修改类的属性和方法。

```python
class MyMeta(type):
    def __new__(mcs, name, bases, attrs):
        # 类定义时自动执行
        if "reply" in attrs:
            attrs["reply"] = wrap(attrs["reply"])
        return super().__new__(mcs, name, bases, attrs)

class Agent(metaclass=MyMeta):
    async def reply(self):  # 自动被 wrap 包装
        ...
```

---

## functools.wraps

`functools`（function tools，函数工具）是 Python 标准库。`@wraps` 装饰器保留原函数的名称和文档。

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def my_function():
    """My docstring"""
    pass

print(my_function.__name__)  # "my_function"（没有 @wraps 会是 "wrapper"）
```

---

## AsyncGenerator

`AsyncGenerator`（Asynchronous Generator，异步生成器）用 `async for` 迭代，用 `yield` 产生值。

```python
async def stream_data():
    for i in range(3):
        await asyncio.sleep(0.1)
        yield i

async def main():
    async for value in stream_data():
        print(value)

asyncio.run(main())
```

---

## Pydantic BaseModel

Pydantic 的 `BaseModel` 自动生成 JSON（JavaScript Object Notation）Schema，用于数据验证。

```python
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    age: int = 0

# 自动生成 JSON Schema
schema = UserProfile.model_json_schema()
# {"type": "object", "properties": {"name": {"type": "string"}, ...}}

# 自动验证
user = UserProfile(name="Alice", age=30)
```

---

## inspect.signature

`inspect.signature()` 获取函数的参数签名。

```python
import inspect

def greet(name: str, greeting: str = "Hello"):
    pass

sig = inspect.signature(greet)
for param_name, param in sig.parameters.items():
    print(f"{param_name}: {param.annotation}, default={param.default}")
# name: <class 'str'>, default=<class 'inspect._empty'>   # 没有默认值时，param.default 就是 inspect.Parameter.empty 这个哨兵
# greeting: <class 'str'>, default=Hello
```

---

## OrderedDict

`OrderedDict`（Ordered Dictionary，有序字典），保持插入顺序。Python 3.7+ 的普通 `dict` 也是有序的，但 `OrderedDict` 提供了额外的 `move_to_end()` 等方法。

---

## deepcopy

`deepcopy`（deep copy，深拷贝），递归复制对象及其所有嵌套对象。

```python
from copy import deepcopy

original = {"msgs": [Msg("user", "hello", "user")]}
copied = deepcopy(original)  # 完全独立的副本
```

---

## match/case（Python 3.10+）

结构化模式匹配，对 Union 类型做类型分发：

```python
def handle_block(block: ContentBlock):
    match block:
        case {"type": "text", "text": str(t)}:
            return f"文本: {t}"
        case {"type": "tool_use", "name": str(n), "input": dict(i)}:
            return f"工具调用: {n}({i})"
        case {"type": "image"}:
            return "图片"
        case _:
            return "未知类型"
```

**要点**：
- `match/case` 比 `if/elif` 链更清晰，特别是对嵌套结构
- 对 TypedDict Union（如 `ContentBlock`），match 可以按 `type` 字段分发
- 在 ch33（ContentBlock Union 设计）中使用

---

> **下一章：[附录 B：术语表](./glossary.md)**