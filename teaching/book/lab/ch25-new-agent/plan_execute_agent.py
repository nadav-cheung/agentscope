"""第 25 章：造一个新 Agent 类型 — Plan-Execute Agent

Plan-Execute vs ReAct:
  ReAct:       推理→行动→观察→推理→行动→...  (逐步推理)
  PlanExecute: 规划→执行步骤1→执行步骤2→...→审查 (先规划再执行)
"""
import asyncio

from agentscope.agent import AgentBase
from agentscope.message import Msg

# → src/agentscope/agent/_agent_base.py     (AgentBase 基类)
# → src/agentscope/agent/_react_agent.py    (ReActAgent 参考)
# → src/agentscope/agent/_react_agent_base.py (ReActAgentBase)


class PlanExecuteAgent(AgentBase):
    """先规划、再执行、最后审查的 Agent。

    与 ReActAgent 的关键区别：PlanExecute 在执行前制定完整计划，
    然后逐个步骤执行，而非每步推理一次。
    """

    def __init__(self, name: str, plan: list[str]) -> None:
        super().__init__()
        self.name = name
        self.plan = plan
        self.results: list[str] = []

    async def _plan_phase(self) -> str:
        """阶段 1: 规划。"""
        steps = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(self.plan))
        return f"[{self.name}] 规划完成，共 {len(self.plan)} 步:\n{steps}"

    async def _execute_step(self, step: str) -> str:
        """阶段 2: 执行单个计划步骤。"""
        return f"[{self.name}] 执行: {step}"

    async def _review_phase(self) -> str:
        """阶段 3: 审查执行结果。"""
        summary = "\n".join(f"  - {r}" for r in self.results)
        return f"[{self.name}] 审查完成:\n{summary}"

    async def reply(self, msg: Msg) -> Msg:  # type: ignore[override]
        """Plan-Execute 主循环: 规划 → 执行 → 审查。"""
        print(await self._plan_phase())
        for step in self.plan:
            self.results.append(await self._execute_step(step))
            print(self.results[-1])
        print(await self._review_phase())
        return Msg(self.name,
                   f"完成 {len(self.plan)} 步", "assistant")


async def main() -> None:
    agent = PlanExecuteAgent(
        name="策划助手",
        plan=["分析需求", "设计方案", "执行任务", "验证结果"],
    )
    msg = Msg("user", "请帮我完成这个任务", "user")
    result = await agent(msg)
    print(f"\n最终: {result.get_text_content()}")


if __name__ == "__main__":
    asyncio.run(main())
