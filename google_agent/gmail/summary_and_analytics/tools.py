import json
from textwrap import dedent
from typing import Optional, Literal

from google_client.api_service import APIServiceLayer
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import ArgsSchema
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from google_agent.gmail.shared.email_cache import EmailCache
from google_agent.shared.exceptions import ToolException
from google_agent.shared.llm_models import MODELS
from google_agent.shared.response import ToolResponse


class SummarizeEmailsInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids of the emails to summarize")
    summary_type: Optional[Literal["conversation", "key_points", "action_items"]] = Field(default="conversation",
                                                                                          description="Type of summary: 'conversation' (default), 'key_points', or 'action_items'")


class SummarizeEmailsTool(BaseTool):
    name: str = "summarize_emails"
    description: str = "Summarize an email or a list of emails"
    args_schema: ArgsSchema = SummarizeEmailsInput

    google_service: APIServiceLayer
    email_cache: EmailCache

    def __init__(
            self,
            google_service: APIServiceLayer,
            email_cache: EmailCache
    ):
        super().__init__(
            google_service=google_service,
            email_cache=email_cache
        )

    def _run(self, message_ids: list[str], summary_type: Optional[
        Literal["conversation", "key_points", "action_items"]] = "conversation") -> ToolResponse:
        try:
            emails = []
            for message_id in message_ids:
                if self.email_cache.retrieve(message_id):
                    email = self.email_cache.retrieve(message_id).copy()
                else:
                    email = self.email_cache.save(self.google_service.gmail.get_email(message_id)).copy()

                keys_to_remove = ['message_id', 'thread_id', 'snippet', 'label_ids', 'has_attachments']
                for key in keys_to_remove:
                    email.pop(key, None)
                emails.append(email)

            system_prompt = dedent(
                """
                You are a helpful writer thread summary assistant.
                You have the ability to concisely summarize threads, extract action items and identify key points.
                You should not perform any task other than these 3.
                When a user asks you to summarize, extract action items or identify key points, respond with that and NO ADDITIONAL TEXT.
                """
            )
            llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
            summaries = []

            for i in range(0, len(emails), 5):
                conversation_emails = emails[i: min(i + 5, len(emails))]
                if summary_type == "key_points":
                    summary_prompt = dedent(
                        f"""
                        Please identify the key points from the following email:
                        Only respond with the key points, NO ADDITIONAL TEXT
                        
                        {json.dumps(conversation_emails)}
                        
                        Key Points:
                        
                        """
                    )
                elif summary_type == "action_items":
                    summary_prompt = dedent(
                        f"""
                        Please extract any action items, tasks, or follow-ups from the following email:\n\n
                        Only respond with the action items, NO ADDITIONAL TEXT
                        
                        {json.dumps(conversation_emails)}
                        
                        Action Items:
                        
                        """
                    )
                else:  # conversation
                    summary_prompt = dedent(
                        f"""
                        Please provide a concise summary of the following email:
                        Only respond with a concise summary, NO ADDITIONAL TEXT
                        
                        {json.dumps(conversation_emails)}
                        
                        Summary:
                        """
                    )

                summary = llm.invoke([
                    SystemMessage(system_prompt),
                    HumanMessage(summary_prompt),
                ])

                summaries.append(summary.content)

            final_answer = llm.invoke([
                HumanMessage(dedent(
                    f"""
                    You are tasked with creating a unified summary from multiple email batch summaries.
                    Your goal is to produce one cohesive summary.
                    DO NOT CHANGE THE WRITING STYLE.
                    DO NOT DROP ANY INFORMATION.
                    DO NOT ADD ANY INFORMATION.
                    Only respond with the unified summary, NO ADDITIONAL TEXT
                    
                    Email Summaries:
                    {'---\n'.join(summaries)}
                    
                    Unified Summary:
                    
                    """
                ))
            ])

            return ToolResponse(
                status="success",
                message=final_answer.content,
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to summarize emails: {e}"
            )

    async def _arun(self, message_ids: list[str], summary_type: Optional[
        Literal["conversation", "key_points", "action_items"]] = "conversation") -> ToolResponse:
        try:
            emails = []
            for message_id in message_ids:
                if self.email_cache.retrieve(message_id):
                    email = self.email_cache.retrieve(message_id).copy()
                else:
                    email = self.email_cache.save(await self.google_service.async_gmail.get_email(message_id)).copy()

                keys_to_remove = ['message_id', 'thread_id', 'snippet', 'label_ids', 'has_attachments']
                for key in keys_to_remove:
                    email.pop(key, None)
                emails.append(email)

            system_prompt = dedent(
                """
                You are a helpful writer thread summary assistant.
                You have the ability to concisely summarize threads, extract action items and identify key points.
                You should not perform any task other than these 3.
                When a user asks you to summarize, extract action items or identify key points, respond with that and NO ADDITIONAL TEXT.
                """
            )
            llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
            summaries = []

            for i in range(0, len(emails), 5):
                conversation_emails = emails[i: min(i + 5, len(emails))]
                if summary_type == "key_points":
                    summary_prompt = dedent(
                        f"""
                        Please identify the key points from the following email:
                        Only respond with the key points, NO ADDITIONAL TEXT

                        {json.dumps(conversation_emails)}

                        Key Points:

                        """
                    )
                elif summary_type == "action_items":
                    summary_prompt = dedent(
                        f"""
                        Please extract any action items, tasks, or follow-ups from the following email:\n\n
                        Only respond with the action items, NO ADDITIONAL TEXT

                        {json.dumps(conversation_emails)}

                        Action Items:

                        """
                    )
                else:  # conversation
                    summary_prompt = dedent(
                        f"""
                        Please provide a concise summary of the following email:
                        Only respond with a concise summary, NO ADDITIONAL TEXT

                        {json.dumps(conversation_emails)}

                        Summary:
                        """
                    )

                summary = llm.invoke([
                    SystemMessage(system_prompt),
                    HumanMessage(summary_prompt),
                ])

                summaries.append(summary.content)

            final_answer = llm.invoke([
                HumanMessage(dedent(
                    f"""
                    You are tasked with creating a unified summary from multiple email batch summaries.
                    Your goal is to produce one cohesive summary.
                    DO NOT CHANGE THE WRITING STYLE.
                    DO NOT DROP ANY INFORMATION.
                    DO NOT ADD ANY INFORMATION.
                    Only respond with the unified summary, NO ADDITIONAL TEXT

                    Email Summaries:
                    {'---\n'.join(summaries)}

                    Unified Summary:

                    """
                ))
            ])

            return ToolResponse(
                status="success",
                message=final_answer.content,
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to summarize emails: {e}"
            )


class ExtractFromEmailInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids to extract data from")
    fields: list[str] = Field(description="A list of fields to extract data from the emails")


class ExtractFromEmailTool(BaseTool):
    name: str = "extract_from_email"
    description: str = "Extract specific fields or information from emails"
    args_schema: ArgsSchema = ExtractFromEmailInput

    google_service: APIServiceLayer
    email_cache: EmailCache

    def __init__(
            self,
            google_service: APIServiceLayer,
            email_cache: EmailCache
    ):
        super().__init__(
            google_service=google_service,
            email_cache=email_cache
        )

    def _run(self, message_ids: list[str], fields: list[str]) -> ToolResponse:
        try:
            emails = []
            for message_id in message_ids:
                if email := self.email_cache.retrieve(message_id):
                    email = email.copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)
                else:
                    email = self.email_cache.save(self.google_service.gmail.get_email(message_id)).copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)

            system_prompt = dedent(
                """
                You are a helpful data extraction assistant.
                You extract specific fields or information from emails as requested.
                You should only extract the requested information and return it in a structured format.
                When extracting data, be precise and only include information that is explicitly present in the emails.
                """
            )

            llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
            extracted_data = []

            for i in range(0, len(emails), 5):
                email_batch = emails[i: min(i + 5, len(emails))]

                extraction_prompt = dedent(
                    f"""
                        Extract the following fields from the emails:
                        Fields to extract: {', '.join(fields)}

                        Emails:
                        {json.dumps(email_batch)}

                        Only respond with the relevant data, NO ADDITIONAL TEXT.
                        
                        Extractions:
                        
                        """
                )

                response = llm.invoke([
                    SystemMessage(system_prompt),
                    HumanMessage(extraction_prompt),
                ])

                extracted_data.append(response.content)

            final_answer = llm.invoke([
                HumanMessage(dedent(
                    f"""
                    You are tasked with creating a unified output from multiple email batch outputs.
                    Your goal is to produce one cohesive output.
                    DO NOT CHANGE THE WRITING STYLE.
                    DO NOT DROP ANY INFORMATION.
                    DO NOT ADD ANY INFORMATION.
                    Only respond with the unified summary, NO ADDITIONAL TEXT

                    Email Summaries:
                    {'---\n'.join(extracted_data)}

                    Unified output:

                    """
                ))
            ])

            return ToolResponse(
                status="success",
                message=final_answer.content
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to extract from emails: {e}"
            )

    async def _arun(self, message_ids: list[str], fields: list[str]) -> ToolResponse:
        try:
            emails = []
            for message_id in message_ids:
                if email := self.email_cache.retrieve(message_id):
                    email = email.copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)
                else:
                    email = self.email_cache.save(await self.google_service.async_gmail.get_email(message_id)).copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)

            system_prompt = dedent(
                """
                You are a helpful data extraction assistant.
                You extract specific fields or information from emails as requested.
                You should only extract the requested information and return it in a structured format.
                When extracting data, be precise and only include information that is explicitly present in the emails.
                """
            )

            llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
            extracted_data = []

            for i in range(0, len(emails), 5):
                email_batch = emails[i: min(i + 5, len(emails))]

                extraction_prompt = dedent(
                    f"""
                        Extract the following fields from the emails:
                        Fields to extract: {', '.join(fields)}

                        Emails:
                        {json.dumps(email_batch)}

                        Only respond with the relevant data, NO ADDITIONAL TEXT.

                        Extractions:

                        """
                )

                response = llm.invoke([
                    SystemMessage(system_prompt),
                    HumanMessage(extraction_prompt),
                ])

                extracted_data.append(response.content)

            final_answer = llm.invoke([
                HumanMessage(dedent(
                    f"""
                    You are tasked with creating a unified output from multiple email batch outputs.
                    Your goal is to produce one cohesive output.
                    DO NOT CHANGE THE WRITING STYLE.
                    DO NOT DROP ANY INFORMATION.
                    DO NOT ADD ANY INFORMATION.
                    Only respond with the unified summary, NO ADDITIONAL TEXT

                    Email Summaries:
                    {'---\n'.join(extracted_data)}

                    Unified output:

                    """
                ))
            ])

            return ToolResponse(
                status="success",
                message=final_answer.content
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to extract from emails: {e}"
            )


class ClassifyEmailInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids to classify")
    classifications: list[str] = Field(description="A list of classification categories to classify emails into")


class ClassifyEmailTool(BaseTool):
    name: str = "classify_email"
    description: str = "Classify emails into specified categories"
    args_schema: ArgsSchema = ClassifyEmailInput

    google_service: APIServiceLayer
    email_cache: EmailCache

    def __init__(
            self,
            google_service: APIServiceLayer,
            email_cache: EmailCache
    ):
        super().__init__(
            google_service=google_service,
            email_cache=email_cache
        )

    def _run(self, message_ids: list[str], classifications: list[str],
             include_confidence: Optional[bool] = False) -> ToolResponse:
        try:
            emails = []
            for message_id in message_ids:
                if email := self.email_cache.retrieve(message_id):
                    email = email.copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)
                else:
                    email = self.email_cache.save(self.google_service.gmail.get_email(message_id))
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)

            system_prompt = dedent(
                """
                You are a helpful email classification assistant.
                You classify emails into the specified categories based on their content, subject, and context.
                Be accurate and consistent in your classifications.
                Only classify emails into the provided categories.
                """
            )

            llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
            classified_emails = []

            for i in range(0, len(emails), 5):
                email_batch = emails[i: min(i + 5, len(emails))]

                classification_prompt = dedent(
                    f"""
                        Classify the following emails into these categories: {', '.join(classifications)}

                        Emails to classify:
                        {json.dumps(email_batch)}

                        Only respond with the classifications, NO ADDITIONAL TEXT.
                        
                        """
                )

                response = llm.invoke([
                    SystemMessage(system_prompt),
                    HumanMessage(classification_prompt),
                ])
                classified_emails.append(response.content)

            final_answer = llm.invoke([
                HumanMessage(dedent(
                    f"""
                    You are tasked with creating a unified output from multiple email batch outputs.
                    Your goal is to produce one cohesive output.
                    DO NOT CHANGE THE WRITING STYLE.
                    DO NOT DROP ANY INFORMATION.
                    DO NOT ADD ANY INFORMATION.
                    Only respond with the unified summary, NO ADDITIONAL TEXT

                    Email Summaries:
                    {'---\n'.join(classified_emails)}

                    Unified output:

                    """
                ))
            ])

            return ToolResponse(
                status="success",
                message=final_answer.content
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to classify emails: {e}"
            )

    async def _arun(self, message_ids: list[str], classifications: list[str],
                    include_confidence: Optional[bool] = False) -> ToolResponse:
        try:
            emails = []
            for message_id in message_ids:
                if email := self.email_cache.retrieve(message_id):
                    email = email.copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)
                else:
                    email = self.email_cache.save(await self.google_service.async_gmail.get_email(message_id))
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)

            system_prompt = dedent(
                """
                You are a helpful email classification assistant.
                You classify emails into the specified categories based on their content, subject, and context.
                Be accurate and consistent in your classifications.
                Only classify emails into the provided categories.
                """
            )

            llm = ChatGoogleGenerativeAI(model=MODELS['gemini']['flash'])
            classified_emails = []

            for i in range(0, len(emails), 5):
                email_batch = emails[i: min(i + 5, len(emails))]

                classification_prompt = dedent(
                    f"""
                        Classify the following emails into these categories: {', '.join(classifications)}

                        Emails to classify:
                        {json.dumps(email_batch)}

                        Only respond with the classifications, NO ADDITIONAL TEXT.

                        """
                )

                response = llm.invoke([
                    SystemMessage(system_prompt),
                    HumanMessage(classification_prompt),
                ])
                classified_emails.append(response.content)

            final_answer = llm.invoke([
                HumanMessage(dedent(
                    f"""
                    You are tasked with creating a unified output from multiple email batch outputs.
                    Your goal is to produce one cohesive output.
                    DO NOT CHANGE THE WRITING STYLE.
                    DO NOT DROP ANY INFORMATION.
                    DO NOT ADD ANY INFORMATION.
                    Only respond with the unified summary, NO ADDITIONAL TEXT

                    Email Summaries:
                    {'---\n'.join(classified_emails)}

                    Unified output:

                    """
                ))
            ])

            return ToolResponse(
                status="success",
                message=final_answer.content
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to classify emails: {e}"
            )
