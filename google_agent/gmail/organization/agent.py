from textwrap import dedent

from google_agent.shared.base_agent import BaseReactGoogleAgent
from .tools import ApplyLabelTool, RemoveLabelTool, CreateLabelTool, DeleteLabelTool, RenameLabelTool, DeleteEmailTool


class OrganizationAgent(BaseReactGoogleAgent):
    name = "OrganizationAgent"
    description = dedent("""
        Specialized agent for managing Gmail labels and email deletion with the following capabilities:
            - Apply labels to emails (needs message_id)
            - Remove labels from emails (needs message_id)
            - Create new labels
            - Delete existing labels
            - Rename labels
            - Delete emails (needs message_id)
    """)

    @property
    def tools(self):
        if self._tools is None:
            self._tools = [
                ApplyLabelTool(self.google_service),
                RemoveLabelTool(self.google_service),
                CreateLabelTool(self.google_service),
                DeleteLabelTool(self.google_service),
                RenameLabelTool(self.google_service),
                DeleteEmailTool(self.google_service)
            ]
        return self._tools
