import json
from datetime import datetime
from typing import Optional, List, Literal

from google_client.api_service import APIServiceLayer
from google_client.services.calendar import EventQueryBuilder, Attendee
from google_client.services.calendar.async_query_builder import AsyncEventQueryBuilder
from langchain_core.tools import ArgsSchema
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from google_agent.shared.exceptions import ToolException
from google_agent.shared.response import ToolResponse


class ListCalendarsTool(BaseTool):
    name: str = "list_calendars"
    description: str = "Retrieves all calendars in users calendar list"
    args_schema: ArgsSchema = None

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self) -> ToolResponse:
        try:
            calendars = self.google_service.calendar.list_calendars()
            calendars = [{'name': calendar.summary, 'id': calendar.id} for calendar in calendars]
            return ToolResponse(
                status="success",
                message=json.dumps(calendars)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list calendars: {str(e)}"
            )

    async def _arun(self) -> ToolResponse:
        try:
            calendars = await self.google_service.async_calendar.list_calendars()
            calendars = [{'name': calendar.summary, 'id': calendar.id} for calendar in calendars]
            return ToolResponse(
                status="success",
                message=json.dumps(calendars)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to list calendars: {str(e)}"
            )


class CreateCalendarInput(BaseModel):
    name: str = Field(description="The name of the calendar")


class CreateCalendarTool(BaseTool):
    name: str = "create_calendar"
    description: str = "Creates a new calendar in user's calendar list"
    args_schema: ArgsSchema = CreateCalendarInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, name: str) -> ToolResponse:
        try:
            calendar = self.google_service.calendar.create_calendar(name)
            calendar = [{'name': calendar.summary, 'id': calendar.id}]
            return ToolResponse(
                status="success",
                message=json.dumps(calendar)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to create calendar: {str(e)}"
            )

    async def _arun(self, name: str) -> ToolResponse:
        try:
            calendar = await self.google_service.async_calendar.create_calendar(name)
            calendar = [{'name': calendar.summary, 'id': calendar.id}]
            return ToolResponse(
                status="success",
                message=json.dumps(calendar)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to create calendar: {str(e)}"
            )


class DeleteCalendarInput(BaseModel):
    calendar_id: str = Field(description="The id of the calendar to delete")


class DeleteCalendarTool(BaseTool):
    name: str = "delete_calendar"
    description: str = "Deletes a calendar from the user's calendar list"
    args_schema: ArgsSchema = DeleteCalendarInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, calendar_id: str) -> ToolResponse:
        try:
            self.google_service.calendar.delete_calendar(calendar_id)
            return ToolResponse(
                status="success",
                message="Calendar deleted"
            )
        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete calendar: {str(e)}"
            )

    async def _arun(self, calendar_id: str) -> ToolResponse:
        try:
            await self.google_service.async_calendar.delete_calendar(calendar_id)
            return ToolResponse(
                status="success",
                message="Calendar deleted"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete calendar: {str(e)}"
            )


class GetEventsInput(BaseModel):
    event_id: str = Field(description="The event_id of the event to retrieve")
    calendar_id: Optional[str] = Field('primary',
                                       description="The calendar_id containing the event. Default is primary")


class GetEventsTool(BaseTool):
    name: str = "get_event"
    description: str = "Retrieve full event detail"
    args_schema: ArgsSchema = GetEventsInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, event_id: str, calendar_id: str = 'primary') -> ToolResponse:
        try:
            event = self.google_service.calendar.get_event(event_id, calendar_id)
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

    async def _arun(self, event_id: str, calendar_id: str = 'primary') -> ToolResponse:
        try:
            event = await self.google_service.async_calendar.get_event(event_id, calendar_id)
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


class ListEventsTool(BaseTool):
    name: str = "list_events"
    description: str = "List events on the user's primary calendar. Can filter by date ranges, free text search terms, and attendee writer."
    args_schema: ArgsSchema = ListEventsInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(
            self,
            calendar_id: str = 'primary',
            max_results: int = 100,
            datetime_min: str = None,
            datetime_max: str = None,
            date_filter: Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK", "THIS_MONTH"] = None,
            query: str = None,
            by_attendee: str = None
    ) -> ToolResponse:
        try:
            params = {
                "calendar_id": calendar_id,
                "max_results": max_results,
                "datetime_min": datetime.fromisoformat(datetime_min) if datetime_min else None,
                "datetime_max": datetime.fromisoformat(datetime_max) if datetime_max else None,
                "date_filter": date_filter,
                "search": query,
                "by_attendee": by_attendee
            }
            builder = self.query_builder(params, is_async=False)
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

    async def _arun(
            self,
            calendar_id: str = 'primary',
            max_results: Optional[int] = 100,
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None,
            date_filter: Optional[Literal["TODAY", "TOMORROW", "THIS_WEEK", "NEXT_WEEK", "THIS_MONTH"]] = "THIS_WEEK",
            query: Optional[str] = None,
            by_attendee: Optional[str] = None
    ) -> ToolResponse:
        try:
            params = {
                "calendar_id": calendar_id,
                "max_results": max_results,
                "datetime_min": datetime.fromisoformat(datetime_min) if datetime_min else None,
                "datetime_max": datetime.fromisoformat(datetime_max) if datetime_max else None,
                "date_filter": date_filter,
                "search": query,
                "by_attendee": by_attendee
            }
            builder = self.query_builder(params, is_async=True)
            events = await builder.execute()
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

    def query_builder(self, params: dict, is_async: bool = False) -> EventQueryBuilder | AsyncEventQueryBuilder:
        service = self.google_service.async_calendar if is_async else self.google_service.calendar
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


class CreateEventTool(BaseTool):
    name: str = "create_event"
    description: str = "Create a new event on the user's primary calendar"
    args_schema: ArgsSchema = CreateEventInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(
            self,
            summary: str,
            start_datetime: str,
            end_datetime: str,
            description: Optional[str] = None,
            location: Optional[str] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None,
            calendar_id: str = 'primary'
    ) -> ToolResponse:
        try:
            if attendees is None:
                attendees = []
            event = self.google_service.calendar.create_event(
                start=datetime.fromisoformat(start_datetime),
                end=datetime.fromisoformat(end_datetime),
                summary=summary,
                description=description,
                location=location,
                attendees=[Attendee(email=attendee) for attendee in attendees],
                recurrence=recurrence,
                calendar_id=calendar_id
            )
            return ToolResponse(
                status="success",
                message=f"Event created successfully. event_id: {event.event_id}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to create event: {str(e)}"
            )

    async def _arun(
            self,
            summary: str,
            start_datetime: str,
            end_datetime: str,
            description: Optional[str] = None,
            location: Optional[str] = None,
            attendees: Optional[List[str]] = None,
            recurrence: Optional[List[str]] = None,
            calendar_id: str = 'primary'
    ) -> ToolResponse:
        try:
            if attendees is None:
                attendees = []
            service = self.google_service.async_calendar or self.google_service.calendar
            event = await service.create_event(
                start=datetime.fromisoformat(start_datetime),
                end=datetime.fromisoformat(end_datetime),
                summary=summary,
                description=description,
                location=location,
                attendees=[Attendee(email=attendee) for attendee in attendees],
                recurrence=recurrence,
                calendar_id=calendar_id
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
    calendar_id: Optional[str] = Field('primary',
                                       description="The calendar_id containing the event. Default is primary")


class DeleteEventTool(BaseTool):
    name: str = "delete_event"
    description: str = "Delete an event from the user's primary calendar"
    args_schema: ArgsSchema = DeleteEventInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(self, event_id: str, calendar_id: str = 'primary') -> ToolResponse:
        try:
            self.google_service.calendar.delete_event(event=event_id, calendar_id=calendar_id)
            return ToolResponse(
                status="success",
                message=f"Event deleted successfully. event_id: {event_id}"
            )
        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete event: {str(e)}"
            )

    async def _arun(self, event_id: str, calendar_id: str = 'primary') -> ToolResponse:
        try:
            await self.google_service.async_calendar.delete_event(event=event_id, calendar_id=calendar_id)
            return ToolResponse(
                status="success",
                message=f"Event deleted successfully. event_id: {event_id}"
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to delete event: {str(e)}"
            )


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


class UpdateEventTool(BaseTool):
    name: str = "update_event"
    description: str = "Update an event on the user's primary calendar"
    args_schema: ArgsSchema = UpdateEventInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(
            self,
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
    ) -> ToolResponse:
        try:
            event = self.google_service.calendar.get_event(event_id=event_id, calendar_id=calendar_id)
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

            updated_event = self.google_service.calendar.update_event(event=event)
            return ToolResponse(
                status="success",
                message=f"Event updated successfully. event_id: {updated_event.event_id}",
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to update event: {str(e)}"
            )

    async def _arun(
            self,
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
    ) -> ToolResponse:
        try:
            event = await self.google_service.async_calendar.get_event(event_id=event_id, calendar_id=calendar_id)
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

            updated_event = await self.google_service.async_calendar.update_event(event=event)
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
    calendar_ids: Optional[List[str]] = Field(['primary'],
                                              description="A list of calendar_ids where to look for free slots. Default is primary")


class FindFreeSlotsTool(BaseTool):
    name: str = "find_free_slots"
    description: str = "Find free time slots on the user's calendar"
    args_schema: ArgsSchema = FindFreeSlotsInput

    google_service: APIServiceLayer

    def __init__(self, google_service: APIServiceLayer):
        super().__init__(google_service=google_service)

    def _run(
            self,
            duration_minutes: int,
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None,
            calendar_ids: Optional[str] = None
    ) -> ToolResponse:
        try:
            free_slots = self.google_service.calendar.find_free_slots(
                duration_minutes=duration_minutes,
                start=datetime.fromisoformat(datetime_min) if datetime_min else None,
                end=datetime.fromisoformat(datetime_max) if datetime_max else None,
                calendar_ids=calendar_ids
            )

            for key in free_slots:
                free_slots[key] = str(free_slots[key])

            return ToolResponse(
                status="success",
                message=json.dumps(free_slots)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to find free slots: {str(e)}"
            )

    async def _arun(
            self,
            duration_minutes: int,
            datetime_min: Optional[str] = None,
            datetime_max: Optional[str] = None,
            calendar_ids: List[str] = None
    ) -> ToolResponse:
        try:
            service = self.google_service.async_calendar or self.google_service.calendar
            free_slots = await service.find_free_slots(
                duration_minutes=duration_minutes,
                start=datetime.fromisoformat(datetime_min) if datetime_min else None,
                end=datetime.fromisoformat(datetime_max) if datetime_max else None,
                calendar_ids=calendar_ids
            )

            for key in free_slots:
                free_slots[key] = str(free_slots[key])

            return ToolResponse(
                status="success",
                message=json.dumps(free_slots)
            )

        except Exception as e:
            raise ToolException(
                tool_name=self.name,
                message=f"Failed to find free slots: {str(e)}"
            )
