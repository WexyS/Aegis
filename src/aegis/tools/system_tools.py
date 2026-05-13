from __future__ import annotations

from aegis.tools.base import BaseTool


class GeneralChatTool(BaseTool):
    name = "general_chat"
    description = "Return a bounded local help response without external model calls."

    async def run(self, **kwargs) -> str:
        self.log_action()
        return "Aegis runtime is online. I can execute registered tools through guard, approval, cancellation, and evidence gates."
