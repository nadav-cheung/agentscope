# 附录 A：Python 进阶概念速查

> 正文中遇到的不那么基础的 Python 概念，集中在这里用大白话 + 极小示意片段讲清楚。需要时翻回来查。

> **上一章：[第 40 章 从开发到部署：服务化与生产考量](../volume-5-team/ch40-deploy-app.md)**

---

## async / await：等，但不闲着

普通（同步）代码调用一个要等两秒的网络接口时，整个程序就"卡"在那两秒里，CPU 空转。`async`/`await` 给了另一种可能：**等的时候，程序可以去做别的事**。

```python
async def ask_model(question):
    answer = await call_api(question)   # 等 API，但此时事件循环可以去跑别的任务
    return answer
```

三个关键词：

- `async def`：定义一个"协程函数"，调用它得到的不是结果，而是一个协程对象，要用 `await` 或事件循环去驱动它。
- `await`：只能写在 `async def` 里，表示"在这里暂停等这个耗时操作完成，期间把控制权交还事件循环"。
- 事件循环（event loop）：幕后的调度员，在多个"正在等"的任务之间来回切换，让它们看起来像在同时进行。

AgentScope 全库采用异步设计——`await agent(msg)` 就是"把消息交给 Agent，等它处理完"。原因很实际：Agent 要等 LLM API、等工具执行、等网络，这些都是"等"，异步能让一个进程同时伺候很多请求或很多 Agent。第 3 章详细讲过它为什么必须异步。

---

## ContextVar：每个任务一份的"全局变量"

全局变量有个老毛病：谁都能改，一改所有人都受影响。在异步世界里，多个任务共享一个进程，如果一个任务改了全局的"当前项目名"，别的任务读到的也跟着变了——这在多租户、多 Agent 场景下是灾难。

`ContextVar`（来自标准库 `contextvars`）解决这个问题：**它对每个异步任务（或线程）呈现独立的值**。

```python
from contextvars import ContextVar

project = ContextVar("project", default="默认项目")
project.set("weather-demo")   # 任务 A 设置
# 任务 B 里读 project，看到的还是它自己那份，互不干扰
```

可以把它想成"每人一个抽屉"：同名抽屉，但每个任务打开的是自己的那一格。AgentScope 用它存运行配置（项目名、运行 ID、是否开启追踪等），保证同进程里多个 Agent 各自的配置互不串台。第 34 章专门讨论了这个选择。

---

## TypedDict：一份带说明书的 dict

普通 `dict` 什么键都能塞，类型检查器对里面的内容两眼一抹黑。`TypedDict` 给 dict 配上一份"字段说明书"：声明它一定有哪些键、每个键是什么类型，但**运行时它依然是个普通 dict**，零额外开销。

```python
from typing_extensions import TypedDict

class TextBlock(TypedDict, total=False):
    type: str          # 必填
    text: str
```

`total=False` 表示"不是所有字段都必须存在"；想让某个字段在 `total=False` 下仍然必填，就用 `Required[...]` 标注。AgentScope 的七种内容块（ContentBlock）全是 TypedDict——因为它们要在 Python 对象和 LLM API 的 JSON 之间高频往返，TypedDict 天生就是 dict，省掉了所有转换。第 4 章和第 33 章详述。

---

## dataclass：少写样板的数据类

写一个"主要用来装数据"的类，往往要手写 `__init__`、`__repr__`、`__eq__` 等一堆样板。`@dataclass` 装饰器帮你自动生成它们。

```python
from dataclasses import dataclass

@dataclass
class ChatUsage:
    input_tokens: int
    output_tokens: int
```

注意：dataclass 实例是一个**对象**，不是 dict。所以它适合"字段固定、需要方法或相等比较"的场景（如模型响应、用量统计），而不适合"要直接序列化成 JSON"的场景——后者 TypedDict 更顺手。AgentScope 里 `ChatResponse`、`ChatUsage` 这类用 dataclass，内容块用 TypedDict，正是按这个分工来的。

---

## Mixin：把一小块能力"混"进来

Mixin（混入）是一种复用手法：把一小段可复用功能写成一个类，再让别的类继承它，从而"混入"这段能力，而不必走完整的继承谱系。

```python
class DictMixin(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__
```

上面这两行是 AgentScope 的 `DictMixin`：它让一个对象**同时支持点号访问和方括号访问**，因为这两种访问在底层被指向了同一份 dict 数据。模型响应这类"字段可能动态扩展"的对象就靠它同时获得两种访问风格（第 4 章）。

---

## 元类 metaclass：造类的类

普通类是"对象的模板"，元类则是"类的模板"——它拦截**类的创建过程**，能在类被定义出来的那一刻偷偷做手脚，比如给类里每个方法包上一层钩子。

```python
class MyMeta(type):
    def __new__(mcs, name, bases, namespace):
        # 在类真正诞生前，可以改写 namespace 里的方法
        return super().__new__(mcs, name, bases, namespace)
```

AgentScope 用一个 `_AgentMeta` 元类，在 Agent 类定义时自动给它的方法套上"钩子"，从而实现"方法被调用前后自动触发 hook"——开发者只管写普通方法，拦截逻辑由元类统一注入。第 15 章和第 32 章讨论它的代价与边界。

---

## @property：把方法伪装成属性

想让一个属性"读取时自动算、设置时自动校验"，又不想让调用方写括号，就用 `@property`。

```python
@property
def project(self) -> str:
    return self._project.get()      # 读：从 ContextVar 取

@project.setter
def project(self, value):
    self._project.set(value)        # 写：存进 ContextVar
```

外面用 `config.project` 像普通属性，背后却走了自定义的 get/set。AgentScope 的运行配置类正是用它把 ContextVar 的 `.get()`/`.set()` 包装成顺手的属性访问（第 3 章）。

---

## @overload：同一个名字，多种类型签名

Python 函数能接受不同类型的参数、返回不同类型的结果，但类型检查器一次只能认一个签名。`@overload` 让你写出多个"假签名"给检查器看，真正的实现只留一份。

```python
@overload
def get_content_blocks(self, t: Literal["text"]) -> list[TextBlock]: ...
@overload
def get_content_blocks(self, t: Literal["tool_use"]) -> list[ToolUseBlock]: ...
def get_content_blocks(self, t=None):
    ...   # 真正的实现只有这一份
```

调用 `msg.get_content_blocks("tool_use")` 时，检查器就知道返回的是 `ToolUseBlock` 列表，可以直接访问 `name`、`input`。这是一种"不用子类也能拿到类型安全的多态"，第 29 章把它和 TypedDict Union 并称为 AgentScope 的类型多态手段。

---

## Literal / Union：把类型说得更精确

- `Literal["user", "assistant", "system"]`：这个值只能是列出的那几个之一（而非任意字符串）。
- `Union[A, B]`（写作 `A | B`）：这个值可以是 A 或 B 任一种。

```python
role: Literal["user", "assistant", "system"]   # 只能三选一
content: str | list[ContentBlock]               # 字符串或列表
```

AgentScope 大量用它们给"看起来灵活、其实有边界"的字段画红线：`role` 锁死三个值，`content` 允许两种形态。这让类型检查能在运行前就拦住不少错误。

---

## 序列化：对象 ↔ 可传输的格式

"序列化"就是把内存里的对象变成可以存盘、可以上网传输的格式（通常是 JSON），反序列化则是反过来。因为 AgentScope 的内容块天生是 dict（TypedDict），它和 JSON 之间几乎零距离：

```python
import json
d = msg.to_dict()          # Msg → dict
text = json.dumps(d)       # dict → JSON 字符串（可存可传）
```

`to_dict()` / `from_dict()` 这对方法，是消息能进 Memory、能上网、能回放的根基（第 4 章）。

---

## 上下文管理器：with 包裹的"配对动作"

有些操作必须"成对"出现：打开文件要关闭、获取锁要释放、进入会话要退出。`with`（或异步的 `async with`）保证这对动作一定成对完成，哪怕中间抛了异常。

```python
async with MsgHub(participants=[a, b, c]):
    # 在这个块里，a/b/c 之间互相喊话会被自动广播
    ...
# 离开块，广播自动结束
```

AgentScope 的 `MsgHub`（多 Agent 通信的发布-订阅作用域，第 19 章）就是以上下文管理器的形式提供：进入即开启广播，离开即关闭，开发者不用手动开关。

---

> **下一章：[附录 B：术语表](./glossary.md)**
