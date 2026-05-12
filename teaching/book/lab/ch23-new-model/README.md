# 第 23 章：造一个新 Model Provider

**对应书籍：** 卷三 ch23
**对应源码：** `src/agentscope/model/`

## 运行

```bash
python ch23-new-model/custom_provider.py
```

## 学什么

- ChatModelBase 的抽象接口
- OpenAIChatModel 的实现参考
- 如何接入新的模型提供商（如本地模型、第三方 API）
- model 和 formatter 的配对关系

## 源码跳转

- `src/agentscope/model/_model_base.py` — ChatModelBase 基类
- `src/agentscope/model/_openai_model.py` — OpenAI 参考实现
