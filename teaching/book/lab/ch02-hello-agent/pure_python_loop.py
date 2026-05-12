"""第 2 章附录：用纯 Python 模拟 ReAct 循环

不需要 AgentScope、不需要 LLM、不需要 API key。
用 if/else 展示 ReAct（推理-行动）的核心逻辑。
运行: python ch02-hello-agent/pure_python_loop.py
"""


def get_weather(city):
    return {"北京": "晴，25°C", "上海": "多云，28°C"}.get(city, "未知")


def simulate_react(user_input, max_steps=5):
    """纯 Python 的 ReAct 循环模拟。
    → src/agentscope/agent/_react_agent.py:408 (_react_loop 真实实现)
    """
    messages = []  # → src/agentscope/memory/_working_memory/_in_memory_memory.py
    for step in range(1, max_steps + 1):
        print(f"\n--- 第 {step} 轮 ---")

        # Think: 决定用什么工具
        think = decide_action(user_input, messages)
        print(f"  [Think]  {think}")

        if think == "ANSWER":
            answer = "北京今天晴朗，25°C，适合出行。"
            print(f"  [Answer] {answer}")
            return answer
        elif think.startswith("TOOL:"):
            tool_name = think.split(":")[1].strip()
            city = "北京"
            result = get_weather(city)
            messages.append(f"工具结果: {result}")
            print(f"  [Act]    {tool_name}({city}) → {result}")
            # 循环继续，下一轮 Think 根据结果决定 ANSWER
    return "无法在限定轮数内回答。"


def decide_action(user_input, messages):
    """模拟 LLM 的推理。
    真实版 → src/agentscope/model/ (LLM 返回 tool_calls 或 text)
    """
    if not messages:
        return "TOOL: get_weather"
    if "25°C" in str(messages):
        return "ANSWER"
    return "TOOL: get_weather"


if __name__ == "__main__":
    result = simulate_react("北京今天天气怎么样？")
    print(f"\n最终结果: {result}")
