import json
import logging
from datetime import datetime
from typing import Optional, List, Literal, Union, Annotated

from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import ArgsSchema, InjectedToolArg
from pydantic import BaseModel, Field

from agents.common.tools import BaseGoogleTool
from core.auth import get_calendar_service
from google_client.services.calendar import EventQueryBuilder, Attendee
from google_client.services.calendar.async_query_builder import AsyncEventQueryBuilder

logger = logging.getLogger(__name__)


class ListCalendarsTool(BaseGoogleTool):
    name: str = "list_calendars"
    description: str = "Retrieves all calendars in users calendar list"
    args_schema: ArgsSchema = None

    def _run(self, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Listing Calendars...", "icon": "📅"}
        )
        calendar = await get_calendar_service(config)
        calendars = await calendar.list_calendars()
        calendars = [{'name': calendar.summary, 'id': calendar.id} for calendar in calendars]
        return json.dumps(calendars)


class CreateCalendarInput(BaseModel):
    name: str = Field(description="The name of the calendar")


class CreateCalendarTool(BaseGoogleTool):
    name: str = "create_calendar"
    description: str = "Creates a new calendar in user's calendar list"
    args_schema: ArgsSchema = CreateCalendarInput

    def _run(self, name: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, name: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Creating Calendar...", "icon": "📅"}
        )
        calendar_service = await get_calendar_service(config)
        calendar = await calendar_service.create_calendar(name)
        calendar_data = [{'name': calendar.summary, 'id': calendar.id}]
        return json.dumps(calendar_data)


class DeleteCalendarInput(BaseModel):
    calendar_id: str = Field(description="The id of the calendar to delete")


class DeleteCalendarTool(BaseGoogleTool):
    name: str = "delete_calendar"
    description: str = "Deletes a calendar from the user's calendar list"
    args_schema: ArgsSchema = DeleteCalendarInput

    def _run(self, calendar_id: str, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, calendar_id: str) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Deleting Calendar...", "icon": "🗑️"}
        )
        calendar_service = await get_calendar_service(config)
        await calendar_service.delete_calendar(calendar_id)
        return "Calendar deleted"


class GetEventsInput(BaseModel):
    event_id: str = Field(description="The event_id of the event to retrieve")
    calendar_id: Optional[str] = Field('primary',
                                       description="The calendar_id containing the event. Default is primary")


class GetEventsTool(BaseGoogleTool):
    name: str = "get_event"
    description: str = "Retrieve full event detail"
    args_schema: ArgsSchema = GetEventsInput

    def _run(self, event_id: str, config: Annotated[RunnableConfig, InjectedToolArg],
             calendar_id: str = 'primary') -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, event_id: str,
                    calendar_id: str = 'primary') -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Retrieving Event...", "icon": "📅"}
        )
        calendar_service = await get_calendar_service(config)
        event = await calendar_service.get_event(event_id, calendar_id)
        event_dict = event.to_dict()
        return json.dumps(event_dict)


class ListEventsInput(BaseModel):
    calendar_id: Optional[str] = Field('primary',
                                       description="The calendar_id containing the event. Default is primary")
    max_results: Optional[int] = Field(default=100, description="Maximum number of events to return")
    datetime_min: Optional[str] = Field(default=None,
                                        description="RFC3339 timestamp string to filter events starting from. Defaults to today")
    datetime_max: Optional[str] = Field(default=None,
                                        description="RFC3339 timestamp string to filter events ending by. Defaults to 30 days after datetime_min")
    date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK", "THIS_MONTH"]] = (
        Field(None, description=("Predefined date filters to filter events. "
                                 "Overrides datetime_min and datetime_max if provided. "
                                 "Options are: TODAY, TOMORROW, THIS_WEEK, NEXT_WEEK, THIS_MONTH"
                                 )))
    query: Optional[str] = Field(default=None, description="Free text search terms to filter events")
    by_attendee: Optional[str] = Field(default=None, description="Filter events by attendee writer")


class ListEventsTool(BaseGoogleTool):
    name: str = "list_events"
    description: str = "List events on the user's primary calendar. Can filter by date ranges, free text search terms, and attendee writer."
    args_schema: ArgsSchema = ListEventsInput

    def _run(
            self,
            config: Annotated[RunnableConfig, InjectedToolArg],
            calendar_id: str = 'primary',
            max_results: int = 100,
            datetime_min: str = None,
            datetime_max: str = None,
            date_filter: Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK", "THIS_MONTH"] = None,
            query: str = None,
            by_attendee: str = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            calendar_id: str = 'primary',
            max_results: Optional[int] = 100,
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None,
            date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK", "THIS_MONTH"]] = "THIS_WEEK",
            query: Optional[str] = None,
            by_attendee: Optional[str] = None
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Getting Events...", "icon": "📅"}
        )
        calendar_service = await get_calendar_service(config)
        params = {
            "calendar_id": calendar_id,
            "max_results": max_results,
            "datetime_min": datetime.fromisoformat(datetime_min.replace('Z', '')) if datetime_min else None,
            "datetime_max": datetime.fromisoformat(datetime_max.replace('Z', '')) if datetime_max else None,
            "date_filter": date_filter,
            "search": query,
            "by_attendee": by_attendee
        }
        builder = self.query_builder(calendar_service, params)
        events = await builder.execute()
        events_data = [event.to_dict() for event in events]
        return json.dumps(events_data)

    def query_builder(self, service, params: dict) -> Union[EventQueryBuilder, AsyncEventQueryBuilder]:
        builder = service.query().in_calendar(params["calendar_id"])
        if params.get("max_results"):
            builder = builder.limit(params["max_results"])
        if params.get("datetime_min"):
            builder = builder.from_date(params["datetime_min"])
        if params.get("datetime_max"):
            builder = builder.to_date(params["datetime_max"])
        if params.get("date_filter"):
            match params["date_filter"]:
                case "TODAY":
                    builder = builder.today()
                case "TOMORROW":
                    builder = builder.tomorrow()
                case "THIS_WEEK":
                    builder = builder.this_week()
                case "NEXT_WEEK":
                    builder = builder.next_week()
                case "THIS_MONTH":
                    builder = builder.this_month()
        if params.get("search"):
            builder = builder.search(params["search"])
        if params.get("by_attendee"):
            builder = builder.by_attendee(params["by_attendee"])

        return builder


class CreateEventInput(BaseModel):
    calendar_id: Optional[str] = Field('primary',
                                       description="The calendar_id of where to create the event. Default is primary")
    summary: str = Field(description="The summary or title of the event")
    start_datetime: str = Field(description="RFC3339 timestamp string for the event start time")
    end_datetime: str = Field(description="RFC3339 timestamp string for the event end time")
    description: Optional[str] = Field(default=None, description="The description of the event")
    location: Optional[str] = Field(default=None, description="The location of the event")
    attendees: Optional[List[str]] = Field(default=None, description="List of attendee writer addresses")
    recurrence: Optional[List[str]] = Field(default=None, description="Recurrence rules for the event in RRULE format")


class CreateEventTool(BaseGoogleTool):
    name: str = "create_event"
    description: str = "Create a new event on the user's primary calendar"
    args_schema: ArgsSchema = CreateEventInput

    def _run(
            self,
            summary: str,
            start_datetime: str,
            end_datetime: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            description: Optional[str] = None,
            location: Optional[str] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None,
            calendar_id: str = 'primary'
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            summary: str,
            start_datetime: str,
            end_datetime: str,
            description: Optional[str] = None,
            location: Optional[str] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None,
            calendar_id: str = 'primary'
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Creating Event...", "icon": "📅"}
        )
        if attendees is None:
            attendees = []
        calendar_service = await get_calendar_service(config)
        event = await calendar_service.create_event(
            start=datetime.fromisoformat(start_datetime),
            end=datetime.fromisoformat(end_datetime),
            summary=summary,
            description=description,
            location=location,
            attendees=[Attendee(email=attendee) for attendee in attendees],
            recurrence=recurrence,
            calendar_id=calendar_id
        )
        return f"Event created successfully. event_id: {event.event_id}"


class DeleteEventInput(BaseModel):
    event_id: str = Field(description="The event_id of the event to delete")
    calendar_id: Optional[str] = Field('primary',
                                       description="The calendar_id containing the event. Default is primary")


class DeleteEventTool(BaseGoogleTool):
    name: str = "delete_event"
    description: str = "Delete an event from the user's primary calendar"
    args_schema: ArgsSchema = DeleteEventInput

    def _run(self, event_id: str, config: Annotated[RunnableConfig, InjectedToolArg],
             calendar_id: str = 'primary') -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(self, config: RunnableConfig, event_id: str,
                    calendar_id: str = 'primary') -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Deleting Event...", "icon": "🗑️"}
        )
        calendar_service = await get_calendar_service(config)
        await calendar_service.delete_event(event=event_id, calendar_id=calendar_id)
        return f"Event deleted successfully. event_id: {event_id}"


class UpdateEventInput(BaseModel):
    calendar_id: Optional[str] = Field('primary',
                                       description="The calendar_id containing the event. Default is primary")
    event_id: str = Field(description="The event_id of the event to update")
    summary: Optional[str] = Field(default=None, description="The new summary or title of the event")
    start_datetime: Optional[str] = Field(default=None,
                                          description="New RFC3339 timestamp string for the new event start time")
    end_datetime: Optional[str] = Field(default=None,
                                        description="New RFC3339 timestamp string for the new event end time")
    description: Optional[str] = Field(default=None, description="The new description of the event")
    location: Optional[str] = Field(default=None, description="The new location of the event")
    add_attendees: Optional[List[str]] = Field(default=None, description="List of attendee writer addresses to add")
    remove_attendees: Optional[List[str]] = Field(default=None,
                                                  description="List of attendee writer addresses to remove")
    attendees: Optional[List[str]] = Field(default=None,
                                           description="Full list of attendee writer addresses to replace existing attendees")
    recurrence: Optional[List[str]] = Field(default=None,
                                            description="New recurrence rules for the event in RFC 5545 format")


class UpdateEventTool(BaseGoogleTool):
    name: str = "update_event"
    description: str = "Update an event on the user's primary calendar"
    args_schema: ArgsSchema = UpdateEventInput

    def _run(
            self,
            event_id: str,
            config: Annotated[RunnableConfig, InjectedToolArg],
            calendar_id: str = 'primary',
            summary: Optional[str] = None,
            start_datetime: Optional[str] = None,
            end_datetime: Optional[str] = None,
            description: Optional[str] = None,
            location: Optional[str] = None,
            add_attendees: Optional[List[str]] = None,
            remove_attendees: Optional[List[str]] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            event_id: str,
            calendar_id: str = 'primary',
            summary: Optional[str] = None,
            start_datetime: Optional[str] = None,
            end_datetime: Optional[str] = None,
            description: Optional[str] = None,
            location: Optional[str] = None,
            add_attendees: Optional[List[str]] = None,
            remove_attendees: Optional[List[str]] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Updating Event...", "icon": "📅"}
        )
        calendar_service = await get_calendar_service(config)
        event = await calendar_service.get_event(event_id=event_id, calendar_id=calendar_id)
        if summary:
            event.summary = summary
        if start_datetime:
            event.start = datetime.fromisoformat(start_datetime)
        if end_datetime:
            event.end = datetime.fromisoformat(end_datetime)
        if description:
            event.description = description
        if location:
            event.location = location
        if attendees:
            event.attendees = [Attendee(email=email) for email in attendees]
        if add_attendees:
            existing_emails = {attendee.email for attendee in event.attendees} if event.attendees else set()
            new_attendees = [Attendee(email=email) for email in add_attendees if email not in existing_emails]
            event.attendees = (event.attendees or []) + new_attendees
        if remove_attendees and event.attendees:
            event.attendees = [attendee for attendee in event.attendees if attendee.email not in remove_attendees]
        if recurrence:
            event.recurrence = recurrence

        updated_event = await calendar_service.update_event(event=event)
        return f"Event updated successfully. event_id: {updated_event.event_id}"


class FindFreeSlotsInput(BaseModel):
    duration_minutes: int = Field(description="Minimum duration for free slots in minutes")
    datetime_min: Optional[str] = Field(default=None, description="RFC3339 timestamp string to start searching from")
    datetime_max: Optional[str] = Field(default=None, description="RFC3339 timestamp string to end searching by")
    calendar_ids: Optional[List[str]] = Field(['primary'],
                                              description="A list of calendar_ids where to look for free slots. Default is primary")


class FindFreeSlotsTool(BaseGoogleTool):
    name: str = "find_free_slots"
    description: str = "Find free time slots on the user's calendar"
    args_schema: ArgsSchema = FindFreeSlotsInput

    def _run(
            self,
            duration_minutes: int,
            config: Annotated[RunnableConfig, InjectedToolArg],
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None,
            calendar_ids: Optional[str] = None
    ) -> str:
        raise NotImplementedError("Use async execution.")

    async def _run_google_task(
            self,
            config: RunnableConfig,
            duration_minutes: int,
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None,
            calendar_ids: List[str] = None
    ) -> str:
        await adispatch_custom_event(
            "tool_status",
            {"text": "Finding Free Slots...", "icon": "🕒"}
        )
        calendar_service = await get_calendar_service(config)
        free_slots = await calendar_service.find_free_slots(
            duration_minutes=duration_minutes,
            start=datetime.fromisoformat(datetime_min) if datetime_min else None,
            end=datetime.fromisoformat(datetime_max) if datetime_max else None,
            calendar_ids=calendar_ids
        )

        for key in free_slots:
            free_slots[key] = str(free_slots[key])

        return json.dumps(free_slots)