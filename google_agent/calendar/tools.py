import json
from datetime import datetime
from typing import Optional, List, Literal

from google_client.services.calendar import EventQueryBuilder, Attendee
from google_client.services.calendar.api_service import CalendarApiService
from langchain.tools.base import BaseTool
from langchain_core.tools import ArgsSchema
from pydantic import BaseModel, Field

from google_agent.shared.exceptions import ToolException
from google_agent.shared.response import ToolResponse


def parse_rfc3339(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str.replace("Z", ""))
    except ValueError as e:
        raise ValueError(f"Invalid RFC3339 date string: {e}")


class GetEventsInput(BaseModel):
    event_id: str = Field(description="The event_id of the event to retrieve")


class GetEventsTool(BaseTool):
    name: str = "get_event"
    description: str = "Retrieve full event detail"
    args_schema: ArgsSchema = GetEventsInput

    calendar_service: CalendarApiService

    def __init__(self, calendar_service: CalendarApiService):
        super().__init__(calendar_service=calendar_service)

    def _run(self, event_id: str) -> ToolResponse:
        try:
            event = self.calendar_service.get_event(event_id=event_id)
            event_dict = event.to_dict()
            return ToolResponse(
                status="success",
                message=json.dumps(event_dict)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to find event: {str(e)}"
            )


class ListEventsInput(BaseModel):
    max_results: Optional[int] = Field(default=10, description="Maximum number of events to return")
    datetime_min: Optional[str] = Field(default=None,
                                        description="RFC3339 timestamp string to filter events starting from. Defaults to today")
    datetime_max: Optional[str] = Field(default=None,
                                        description="RFC3339 timestamp string to filter events ending by. Defaults to 30 days after datetime_min")
    date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK", "THIS_MONTH"]] = (
        Field(None, description=("Predefined date filters to filter events. "
                                 "Overrides datetime_min and datetime_max if provided. "
                                 "Options are: TODAY, TOMORROW, THIS_WEEK, NEXT_WEEK, THIS_MONTH"
                                 )
              )
    )
    query: Optional[str] = Field(default=None, description="Free text search terms to filter events")
    by_attendee: Optional[str] = Field(default=None, description="Filter events by attendee writer")


class ListEventsTool(BaseTool):
    name: str = "list_events"
    description: str = (
        "List events on the user's primary calendar. "
        "Can filter by date ranges, free text search terms, and attendee writer."
    )
    args_schema: ArgsSchema = ListEventsInput

    calendar_service: CalendarApiService

    def __init__(self, calendar_service: CalendarApiService):
        super().__init__(calendar_service=calendar_service)

    def _run(
            self,
            max_results: Optional[int] = 10,
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None,
            date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK", "THIS_MONTH"]] = "THIS_WEEK",
            query: Optional[str] = None,
            by_attendee: Optional[str] = None
    ) -> ToolResponse:
        try:
            params = {
                "max_results": max_results,
                "datetime_min": datetime_min,
                "datetime_max": datetime_max,
                "date_filter": date_filter,
                "thread": query,
                "by_attendee": by_attendee
            }
            builder = self.query_builder(params)
            events = builder.execute()
            events_data = [event.to_dict() for event in events]
            return ToolResponse(
                status="success",
                message=json.dumps(events_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list events: {str(e)}"
            )

    def query_builder(self, params: dict) -> EventQueryBuilder:
        builder = self.calendar_service.query()
        if params.get("max_results"):
            builder = builder.limit(params["max_results"])
        if params.get("datetime_min"):
            builder = builder.from_date(parse_rfc3339(params["datetime_min"]))
        if params.get("datetime_max"):
            builder = builder.to_date(parse_rfc3339(params["datetime_max"]))
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
        if params.get("thread"):
            builder = builder.search(params["thread"])
        if params.get("by_attendee"):
            builder = builder.by_attendee(params["by_attendee"])

        return builder


class CreateEventInput(BaseModel):
    summary: str = Field(description="The summary or title of the event")
    start_datetime: str = Field(description="RFC3339 timestamp string for the event start time")
    end_datetime: str = Field(description="RFC3339 timestamp string for the event end time")
    description: Optional[str] = Field(default=None, description="The description of the event")
    location: Optional[str] = Field(default=None, description="The location of the event")
    attendees: Optional[List[str]] = Field(default=None, description="List of attendee writer addresses")
    recurrence: Optional[List[str]] = Field(default=None, description="Recurrence rules for the event in RRULE format")


class CreateEventTool(BaseTool):
    name: str = "create_event"
    description: str = "Create a new event on the user's primary calendar"
    args_schema: ArgsSchema = CreateEventInput

    calendar_service: CalendarApiService

    def __init__(self, calendar_service: CalendarApiService):
        super().__init__(calendar_service=calendar_service)

    def _run(
            self,
            summary: str,
            start_datetime: str,
            end_datetime: str,
            description: Optional[str] = None,
            location: Optional[str] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None
    ) -> ToolResponse:
        try:
            event = self.calendar_service.create_event(
                start=parse_rfc3339(start_datetime),
                end=parse_rfc3339(end_datetime),
                summary=summary,
                description=description,
                location=location,
                attendees=attendees,
                recurrence=recurrence
            )
            return ToolResponse(
                status="success",
                message=f"Event created successfully. event_id: {event.event_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to create event: {str(e)}"
            )


class DeleteEventInput(BaseModel):
    event_id: str = Field(description="The event_id of the event to delete")


class DeleteEventTool(BaseTool):
    name: str = "delete_event"
    description: str = "Delete an event from the user's primary calendar"
    args_schema: ArgsSchema = DeleteEventInput

    calendar_service: CalendarApiService

    def __init__(self, calendar_service: CalendarApiService):
        super().__init__(calendar_service=calendar_service)

    def _run(self, event_id: str) -> ToolResponse:
        try:
            if self.calendar_service.delete_event(event=event_id):
                return ToolResponse(
                    status="success",
                    message=f"Event deleted successfully. event_id: {event_id}"
                )
            else:
                return ToolResponse(
                    status="error",
                    message=f"Failed to delete event: {event_id}"
                )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete event: {str(e)}"
            )


class UpdateEventInput(BaseModel):
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


class UpdateEventTool(BaseTool):
    name: str = "update_event"
    description: str = "Update an event on the user's primary calendar"
    args_schema: ArgsSchema = UpdateEventInput

    calendar_service: CalendarApiService

    def __init__(self, calendar_service: CalendarApiService):
        super().__init__(calendar_service=calendar_service)

    def _run(
            self,
            event_id: str,
            summary: Optional[str] = None,
            start_datetime: Optional[str] = None,
            end_datetime: Optional[str] = None,
            description: Optional[str] = None,
            location: Optional[str] = None,
            add_attendees: Optional[List[str]] = None,
            remove_attendees: Optional[List[str]] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None
    ) -> ToolResponse:
        try:
            event = self.calendar_service.get_event(event_id=event_id)
            if summary:
                event.summary = summary
            if start_datetime:
                event.start = parse_rfc3339(start_datetime)
            if end_datetime:
                event.end = parse_rfc3339(end_datetime)
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

            updated_event = self.calendar_service.update_event(event=event)
            return ToolResponse(
                status="success",
                message=f"Event updated successfully. event_id: {updated_event.event_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to update event: {str(e)}"
            )


class FindFreeSlotsInput(BaseModel):
    duration_minutes: int = Field(description="Minimum duration for free slots in minutes")
    datetime_min: Optional[str] = Field(default=None, description="RFC3339 timestamp string to start searching from")
    datetime_max: Optional[str] = Field(default=None, description="RFC3339 timestamp string to end searching by")


class FindFreeSlotsTool(BaseTool):
    name: str = "find_free_slots"
    description: str = "Find free time slots on the user's primary calendar"
    args_schema: ArgsSchema = FindFreeSlotsInput

    calendar_service: CalendarApiService

    def __init__(self, calendar_service: CalendarApiService):
        super().__init__(calendar_service=calendar_service)

    def _run(
            self,
            duration_minutes: int,
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None
    ) -> ToolResponse:
        try:
            free_slots = self.calendar_service.find_free_slots(
                duration_minutes=duration_minutes,
                start=parse_rfc3339(datetime_min) if datetime_min else None,
                end=parse_rfc3339(datetime_max) if datetime_max else None
            )
            slots_data = [str(slot) for slot in free_slots]

            self.calendar_service.list_events()

            return ToolResponse(
                status="success",
                message=json.dumps(slots_data)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to find free slots: {str(e)}"
            )

