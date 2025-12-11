# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Coalesce
from pypika import Case


def get_context(context):
	route = frappe.form_dict.get("name")

	schedulable = frappe.get_all(
		"Public Calendar",
		filters={"allow_booking": 1},
		fields=[
			"name",
			"title",
			"route",
			"user",
			"busy_text",
			"slot_duration",
			"max_meeting_duration",
			"buffer_time",
			"min_notice_hours",
			"max_advance_days",
			"working_hours",
			"booking_dialog_title",
		],
	)

	if not schedulable:
		frappe.throw(_("No calendars available for scheduling"), frappe.DoesNotExistError)

	if route:
		calendar = next((c for c in schedulable if c.route == route), None)
		if not calendar:
			frappe.throw(_("Calendar not found"), frappe.DoesNotExistError)
		context.calendar = calendar
		context.parents = [{"name": _("Schedule"), "route": "/schedule"}]
	else:
		context.calendar = None
		context.parents = [{"name": _("Home"), "route": "/"}]

	context.schedulable_calendars = schedulable
	context.no_cache = 1


@frappe.whitelist()
def get_events(start: str, end: str, public_calendar: str):
	Event = DocType("Event")
	EventParticipant = DocType("Event Participants")
	PublicCalendar = DocType("Public Calendar")

	query = (
		frappe.qb.from_(Event)
		.join(EventParticipant)
		.on(EventParticipant.parent == Event.name)
		.join(PublicCalendar)
		.on(
			(PublicCalendar.user == EventParticipant.reference_docname)
			& (EventParticipant.reference_doctype == "User")
		)
		.select(
			Event.name,
			Event.starts_on,
			Event.ends_on,
			Event.all_day,
			Case().when(Event.event_type == "Public", Event.subject).else_("").as_("subject"),
			PublicCalendar.busy_text,
		)
		.where(
			(Event.starts_on <= end)
			& (Coalesce(Event.ends_on, Event.starts_on) >= start)
			& (PublicCalendar.allow_booking == 1)
			& (PublicCalendar.name == public_calendar)
			# & (EventParticipant.status != "Declined")
		)
		.distinct()
	)

	return query.run(as_dict=True)


@frappe.whitelist()
def book_appointment(
	public_calendar: str,
	starts_on: str,
	ends_on: str,
	subject: str,
	description: str = "",
):
	calendar = frappe.get_doc("Public Calendar", public_calendar)

	if not calendar.allow_booking:
		frappe.throw(_("Booking is not enabled for this calendar"))

	# TODO: validate against working_hours, min_notice, max_advance, conflicts

	event = frappe.get_doc(
		{
			"doctype": "Event",
			"subject": subject,
			"description": description,
			"starts_on": starts_on,
			"ends_on": ends_on,
			"event_type": "Private",
		}
	)
	event.append(
		"event_participants",
		{
			"reference_doctype": "User",
			"reference_docname": calendar.user,
		},
	)
	event.append(
		"event_participants",
		{
			"reference_doctype": "User",
			"reference_docname": frappe.session.user,
		},
	)
	event.insert(ignore_permissions=True)

	return event.name
