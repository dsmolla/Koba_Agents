from google_client.services.drive import DriveApiService
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig

from google_agent.shared.base_agent import BaseAgent


class BaseDriveAgent(BaseAgent):
    """Base class for all Drive-specific agents"""

    def __init__(
        self,
        drive_service: DriveApiService,
        llm: BaseChatModel,
        config: RunnableConfig = None,
        print_steps: bool = False,
    ):
        self.drive_service = drive_service
        super().__init__(llm, config, print_steps)