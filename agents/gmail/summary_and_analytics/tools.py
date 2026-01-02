import json
from textwrap import dedent
from typing import Optional, Literal, Annotated

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agents.common.llm_models import MODELS
from core.auth import get_gmail_service
from core.cache import get_email_cache


class SummarizeEmailsInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids of the emails to summarize")
    summary_type: Optional[Literal["conversation", "key_points", "action_items"]] = Field(default="conversation",
                                                                                          description="Type of summary: 'conversation' (default), 'key_points', or 'action_items'")


class SummarizeEmailsTool(BaseTool):
    name: str = "summarize_emails"
    description: str = "Summarize an email or a list of emails"
    args_schema: ArgsSchema = SummarizeEmailsInput

    def _run(self, message_ids: list[str], summary_type: Optional[
        Literal["conversation", "key_points", "action_items"]] = "conversation", config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_ids: list[str], config: Annotated[RunnableConfig, InjectedToolArg], summary_type: Optional[
        Literal["conversation", "key_points", "action_items"]] = "conversation") -> str:
        try:
            gmail = get_gmail_service(config)
            email_cache = get_email_cache(config)

            emails = []
            for message_id in message_ids:
                if email_cache.get(message_id):
                    email = email_cache.get(message_id).copy()
                else:
                    email = email_cache.save(await gmail.get_email(message_id)).copy()

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

            return final_answer.content

        except Exception as e:
            return "Unable to summarize emails due to internal error"


class ExtractFromEmailInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids to extract data from")
    fields: list[str] = Field(description="A list of fields to extract data from the emails")


class ExtractFromEmailTool(BaseTool):
    name: str = "extract_from_email"
    description: str = "Extract specific fields or information from emails"
    args_schema: ArgsSchema = ExtractFromEmailInput

    def _run(self, message_ids: list[str], fields: list[str], config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_ids: list[str], fields: list[str], config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        try:
            gmail = get_gmail_service(config)
            email_cache = get_email_cache(config)

            emails = []
            for message_id in message_ids:
                if email := email_cache.get(message_id):
                    email = email.copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)
                else:
                    email = email_cache.save(await gmail.get_email(message_id)).copy()
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

            return final_answer.content

        except Exception as e:
            return "Unable to extract from emails due to internal error"


class ClassifyEmailInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids to classify")
    classifications: list[str] = Field(description="A list of classification categories to classify emails into")


class ClassifyEmailTool(BaseTool):
    name: str = "classify_email"
    description: str = "Classify emails into specified categories"
    args_schema: ArgsSchema = ClassifyEmailInput

    def _run(self, message_ids: list[str], classifications: list[str],
             config: Annotated[RunnableConfig, InjectedToolArg] = None, include_confidence: Optional[bool] = False) -> str:
        raise NotImplementedError("Use async execution.")

    async def _arun(self, message_ids: list[str], classifications: list[str],
                    config: Annotated[RunnableConfig, InjectedToolArg], include_confidence: Optional[bool] = False) -> str:
        try:
            gmail = get_gmail_service(config)
            email_cache = get_email_cache(config)

            emails = []
            for message_id in message_ids:
                if email := email_cache.get(message_id):
                    email = email.copy()
                    del email["snippet"]
                    del email["has_attachments"]
                    emails.append(email)
                else:
                    email = email_cache.save(await gmail.get_email(message_id))
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

            return final_answer.content

        except Exception as e:
            return "Unable to classify emails due to internal error"
