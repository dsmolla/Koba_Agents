import asyncio
import json
import logging
from textwrap import dedent
from typing import Optional, Literal, Annotated

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_gmail_service
from core.cache import get_email_cache

logger = logging.getLogger(__name__)


class SummarizeEmailsInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids of the emails to summarize")


class SummarizeEmailsTool(BaseGoogleTool):
    name: str = "summarize_emails"
    description: str = dedent("""
        - Generates a high-level, summary of one or more emails.
        - Use when the user wants an overview 
        - Requires one or more message_ids
    """)
    args_schema: ArgsSchema = SummarizeEmailsInput

    def _run(self, message_ids: list[str], summary_type: Optional[
        Literal["conversation", "key_points", "action_items"]] = "conversation",
             config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_ids: list[str]) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Summarizing Emails...", "icon": "📝"}
        )
        gmail = await get_gmail_service(config)
        email_cache = get_email_cache(config)

        email_map = {}
        missing_ids = []
        for message_id in message_ids:
            if cached := email_cache.get(message_id):
                email_map[message_id] = cached
            else:
                missing_ids.append(message_id)

        if missing_ids:
            fetched = await gmail.batch_get_emails(missing_ids)
            for result in fetched:
                if not isinstance(result, tuple):
                    email_map[result.message_id] = email_cache.save(result)

        emails = []
        for message_id in message_ids:
            if email_data := email_map.get(message_id):
                email = email_data.copy()
                keys_to_remove = ['message_id', 'thread_id', 'snippet', 'label_ids', 'has_attachments']
                for key in keys_to_remove:
                    email.pop(key, None)
                emails.append(email)

        system_prompt = dedent(
            """
            You are an inbox digest assistant. Your job is to transform a list of emails into a clean, scannable daily digest that helps the user quickly understand what needs their attention.
            
            # Rules
                * Be concise; each email gets one line, not a paragraph.
                * Preserve names, deadlines, and specific details, do not generalize them away.
                * Do not add information that is not in the emails.
                * If a section has no emails, omit it entirely.
                * Respond only with the digest; no preamble or closing remarks.
            
            # Output Format
                Use exactly this structure:
                    Inbox Digest -- {date or filter}
                    
                    🔴 ACTION REQUIRED
                        * [Sender] -- [What is needed and by when, if stated]
                    
                    🟡 AWAITING RESPONSE
                        * [Sender] -- [What you are waiting on]
                    
                    🔵 FYI / UPDATES
                        * [Sender] -- [One line summary]
                    
                    ⚪ LOW PRIORITY / NEWSLETTERS
                        * [Sender] -- [Topic only]
            
            # Classification guide
                * ACTION REQUIRED — emails where the user must do something (reply, approve, review, sign, submit)
                * AWAITING RESPONSE — emails the user sent or threads where the ball is in someone else's court
                * FYI / UPDATES — informational emails that require no action but are worth knowing
                * LOW PRIORITY / NEWSLETTERS — marketing, newsletters, notifications, automated emails
            """
        )

        llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
        response = await llm.ainvoke([SystemMessage(system_prompt), HumanMessage(json.dumps(emails))])
        return response.content


class ExtractFromEmailInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids to extract data from")
    fields: list[str] = Field(description="A list of fields to extract data from the emails")

class ExtractedDataOutput(BaseModel):
    extracted_data: list[dict] = Field(description="A list of the extracted data")


class ExtractFromEmailTool(BaseGoogleTool):
    name: str = "extract_from_emails"
    description: str = dedent("""
        - Extracts specific structured data from emails.
        - Use when the user wants concrete information pulled out in structured form
        - Requires message_ids and fields to extract
    """)
    args_schema: ArgsSchema = ExtractFromEmailInput

    def _run(self, message_ids: list[str], fields: list[str],
             config: Annotated[RunnableConfig, InjectedToolArg] = None) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_ids: list[str], fields: list[str]) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Extracting Data...", "icon": "📊"}
        )
        gmail = await get_gmail_service(config)
        email_cache = get_email_cache(config)

        email_map = {}
        missing_ids = []
        for message_id in message_ids:
            if cached := email_cache.get(message_id):
                email_map[message_id] = cached
            else:
                missing_ids.append(message_id)

        if missing_ids:
            fetched = await gmail.batch_get_emails(missing_ids)
            for result in fetched:
                if not isinstance(result, tuple):
                    email_map[result.message_id] = email_cache.save(result)

        emails = []
        for message_id in message_ids:
            if email_data := email_map.get(message_id):
                email = email_data.copy()
                del email["snippet"]
                del email["has_attachments"]
                emails.append(email)

        system_prompt = dedent(
            """
            # Role
                * You are a precise data extraction engine for emails. 
                * Your sole job is to extract specific information from email content and return it as valid JSON.
            
            # Rules
                * Return ONLY a valid JSON object. No preamble, explanation or markdown fences.
                * Extract only what is explicitly stated in the email. Do NOT infer, assume, or fill in missing information.
                * If a requested field is not present in the email, set its value to null.
                * If a field appears multiple times, return all occurrences as an array.
            
            # Examples
                Input:
                    email_content: "Hi John, please find the invoice attached. Total due: $4,250.00. Payment deadline is March 15, 2025."
                    extraction_schema: ["total_amount", "deadline", "recipient_name", "invoice_number"]
                Output:
                    ["total_amount": "$4,250.00", "deadline": "March 15, 2025", "recipient_name": "John", "invoice_number": null]
                    
                Input:
                    email_content: [
                        "Hi John, total due: $4,250.00. Payment deadline is March 15, 2025.",
                        "Hi Sarah, total due: $1,800.00. Payment deadline is April 1, 2025. Invoice #882."
                    ]
                    extraction_schema: ["recipient_name", "total_amount", "deadline", "invoice_number"]
                Output:
                    [
                        {"recipient_name": "John", "total_amount": "$4,250.00", "deadline": "March 15, 2025", "invoice_number": null},
                        {"recipient_name": "Sarah", "total_amount": "$1,800.00", "deadline": "April 1, 2025", "invoice_number": "#882"}
                    ]
            """
        )

        llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
        tasks = []

        for i in range(0, len(emails), 10):
            email_batch = emails[i: min(i + 10, len(emails))]

            extraction_prompt = dedent(
                f"""
                    email_content: {json.dumps(email_batch)}
                    
                    extraction_schema: {json.dumps(fields)}
                """
            )

            task = llm.with_structured_output(ExtractedDataOutput).ainvoke([
                SystemMessage(system_prompt),
                HumanMessage(extraction_prompt),
            ])
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        combined = [item for batch in results for item in batch.extracted_data]

        return json.dumps(combined)


class ClassifyEmailInput(BaseModel):
    message_ids: list[str] = Field(description="A list of message_ids to classify")
    classifications: list[str] = Field(description="A list of classification categories to classify emails into")

class EmailClassification(BaseModel):
    message_id: str = Field(description="The message_id of the email being classified")
    category: str = Field(description="The category assigned to the email. Must be one of the categories provided by the user, exactly as written.")

class ClassifyEmailOutput(BaseModel):
    classifications: list[EmailClassification] = Field(description="List of classifications, one per email.")

class ClassifyEmailTool(BaseGoogleTool):
    name: str = "classify_emails"
    description: str = dedent("""
        - Classifies email(s) into one or more categories based on its content.
        - Returns a list of dictionaries with message_id and category as the keys.
        - Requires a list of message_ids to classify and categories to classify the emails into.
    """)
    args_schema: ArgsSchema = ClassifyEmailInput

    def _run(self, message_ids: list[str], classifications: list[str],
             config: Annotated[RunnableConfig, InjectedToolArg] = None,
             include_confidence: Optional[bool] = False) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, message_ids: list[str], classifications: list[str],
                    include_confidence: Optional[bool] = False) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Classifying Emails...", "icon": "🏷️"}
        )
        gmail = await get_gmail_service(config)
        email_cache = get_email_cache(config)

        email_map = {}
        missing_ids = []
        for message_id in message_ids:
            if cached := email_cache.get(message_id):
                email_map[message_id] = cached
            else:
                missing_ids.append(message_id)

        if missing_ids:
            fetched = await gmail.batch_get_emails(missing_ids)
            for result in fetched:
                if not isinstance(result, tuple):
                    email_map[result.message_id] = email_cache.save(result)

        emails = []
        for message_id in message_ids:
            if email_data := email_map.get(message_id):
                email = email_data.copy()
                del email["snippet"]
                emails.append(email)

        system_prompt = dedent(
            """
            # Role
                You are an email classification engine. Your sole job is to assign each email exactly one category from a provided list.
            
            # Rules
                * Assign exactly one category per email — the single best match.
                * Only use categories from the provided classification schema. Do NOT invent, rephrase, or abbreviate them.
                * Base your decision only on the email content. Do NOT infer intent beyond what is explicitly stated.
                * If no category is a strong match, pick the closest one. Never leave an email unclassified.
                * Every email in the input must have a corresponding entry in the output.
            """
        )

        llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
        tasks = []

        for i in range(0, len(emails), 10):
            email_batch = emails[i: min(i + 10, len(emails))]

            classification_prompt = dedent(
                f"""
                    emails: {json.dumps(email_batch)}
                    
                    categories: {json.dumps(classifications)}
                """)

            task = llm.with_structured_output(ClassifyEmailOutput).ainvoke([
                SystemMessage(system_prompt),
                HumanMessage(classification_prompt),
            ])
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        combined = [item.model_dump() for batch in results for item in batch.classifications]

        return json.dumps(combined)