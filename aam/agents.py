from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

class Completer(Protocol):
    def complete(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str: ...

@dataclass
class Agent:
    name: str
    system_prompt: str
    temperature: float = 0.2

    def run(self, llm: Completer | None, prompt: str, mock_result: str) -> str:
        if llm is None:
            return mock_result
        return llm.complete(self.system_prompt, prompt, self.temperature)

def build_agents(config: dict) -> dict[str, Agent]:
    result = {}
    for name, item in config.get("agents", {}).items():
        if item.get("enabled", True):
            result[name] = Agent(name, item["system_prompt"], float(item.get("temperature", 0.2)))
    required = {"researcher", "developer", "reviewer"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"Missing enabled agents: {', '.join(sorted(missing))}")
    return result
