
class ToolException(Exception):
    """Base exception for all tool-related errors."""
    def __init__(self, message: str, tool_name: str):
        super().__init__(message)
        self.message = message
        self.tool_name = tool_name


class AgentException(Exception):
    """Base exception for all agent-related errors."""
    def __init__(self, message: str, agent_name: str):
        super().__init__(message)
        self.message = message
        self.agent_name = agent_name