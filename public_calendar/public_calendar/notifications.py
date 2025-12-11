# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

"""
Notification utilities for Public Calendar.

Handles email notifications with ICS attachments for bookings,
cancellations, and reminders. Includes HMAC-based token generation
for secure guest RSVP actions.

Terminology:
- Host: The user linked in Public Calendar.user field (whose calendar is being booked)
- Guest: Any other participant in the event (the person making the booking)
"""

import hashlib
import hmac
from typing import Literal

import frappe
from frappe.query_builder import DocType
from frappe.utils import add_to_date, format_datetime, get_datetime, get_url, now_datetime

from public_calendar.public_calendar.ics import generate_ics_attachment


def generate_rsvp_token(
	event_name: str,
	email: str,
	action: Literal["confirm", "decline", "cancel"],
) -> str:
	"""
	Generate a deterministic HMAC token for RSVP actions.

	Token is derived from event name, email, action, and site secret.
	No database storage required - token can be verified by regenerating.
	"""
	secret = frappe.local.conf.get("secret_key") or frappe.local.site
	message = f"{event_name}:{email}:{action}"
	return hmac.new(
		secret.encode(),
		message.encode(),
		hashlib.sha256,
	).hexdigest()[:32]


def verify_rsvp_token(
	event_name: str,
	email: str,
	action: Literal["confirm", "decline", "cancel"],
	token: str,
) -> bool:
	"""Verify an RSVP token."""
	expected = generate_rsvp_token(event_name, email, action)
	return hmac.compare_digest(expected, token)


def get_rsvp_url(
	event_name: str,
	email: str,
	action: Literal["confirm", "decline", "cancel"],
) -> str:
	"""Generate a full RSVP URL for an action."""
	token = generate_rsvp_token(event_name, email, action)
	base_url = get_url()
	return f"{base_url}/rsvp?event={event_name}&email={email}&action={action}&token={token}"


def get_public_calendar_for_event(event: "frappe.Document") -> "frappe.Document | None":
	"""Get the Public Calendar linked to an event via ref_type/ref_name."""
	if event.get("reference_doctype") == "Public Calendar" and event.get("reference_docname"):
		return frappe.get_doc("Public Calendar", event.reference_docname)
	return None


def get_host_and_guests(
	event: "frappe.Document",
	public_calendar: "frappe.Document",
) -> tuple[dict | None, list[dict]]:
	"""
	Identify host and guests from event participants.

	Host is the participant matching Public Calendar.user.
	Guests are all other participants.

	Returns:
	        tuple of (host_dict, list_of_guest_dicts)
	        Each dict has keys: user, email, full_name
	"""
	host = None
	guests = []

	calendar_user = public_calendar.user

	for p in event.event_participants or []:
		if p.reference_doctype != "User":
			continue

		user_data = frappe.db.get_value(
			"User",
			p.reference_docname,
			["name", "email", "full_name"],
			as_dict=True,
		)
		if not user_data:
			continue

		participant_info = {
			"user": user_data.name,
			"email": user_data.email,
			"full_name": user_data.full_name,
		}

		if p.reference_docname == calendar_user:
			host = participant_info
		else:
			guests.append(participant_info)

	return host, guests


def send_booking_notification(
	event: "frappe.Document",
	public_calendar: "frappe.Document",
	recipient: str,
	recipient_name: str | None = None,
	is_host: bool = False,
) -> None:
	"""
	Send booking confirmation email with ICS attachment.

	Args:
	        event: The booked Event document
	        public_calendar: The Public Calendar document
	        recipient: Email address to send to
	        recipient_name: Display name of recipient
	        is_host: True if recipient is the calendar's user (host)
	"""
	host, guests = get_host_and_guests(event, public_calendar)

	if not host:
		frappe.log_error(
			f"Could not identify host for event {event.name}",
			"Public Calendar Notification Error",
		)
		return

	# Build attendee list for ICS
	attendees = [
		{
			"email": host["email"],
			"name": host["full_name"],
			"status": "ACCEPTED",
			"rsvp": False,
		},
	]
	for guest in guests:
		attendees.append(
			{
				"email": guest["email"],
				"name": guest["full_name"],
				"status": "NEEDS-ACTION",
				"rsvp": True,
			}
		)

	# Generate ICS attachment (sequence 0 for new booking)
	ics_attachment = generate_ics_attachment(
		event=event,
		method="REQUEST",
		organizer_email=host["email"],
		organizer_name=host["full_name"],
		attendees=attendees,
		sequence=0,
	)

	# Build template context
	context = _build_email_context(event, public_calendar, host, guests)
	context["is_host"] = is_host

	# Add RSVP links
	context["confirm_url"] = get_rsvp_url(event.name, recipient, "confirm")
	context["decline_url"] = get_rsvp_url(event.name, recipient, "decline")
	context["cancel_url"] = get_rsvp_url(event.name, recipient, "cancel")

	# Get template
	template_field = "host_booking_template" if is_host else "guest_booking_template"
	template_name = public_calendar.get(template_field) or "Public Calendar - Booking Confirmation"

	_send_templated_email(
		recipient=recipient,
		template_name=template_name,
		context=context,
		attachments=[ics_attachment],
		reference_doctype="Event",
		reference_name=event.name,
	)


def send_cancellation_notification(
	event: "frappe.Document",
	public_calendar: "frappe.Document",
	recipient: str,
	cancelled_by: str,
) -> None:
	"""Send cancellation email with ICS CANCEL attachment."""
	host, guests = get_host_and_guests(event, public_calendar)

	if not host:
		return

	# Build attendee list for cancellation
	attendees = [
		{"email": host["email"], "name": host["full_name"], "status": "CANCELLED", "rsvp": False},
	]
	for guest in guests:
		attendees.append(
			{
				"email": guest["email"],
				"name": guest["full_name"],
				"status": "CANCELLED",
				"rsvp": False,
			}
		)

	# Generate cancellation ICS (sequence 1 for cancellation)
	ics_attachment = generate_ics_attachment(
		event=event,
		method="CANCEL",
		organizer_email=host["email"],
		organizer_name=host["full_name"],
		attendees=attendees,
		sequence=1,
	)

	context = _build_email_context(event, public_calendar, host, guests)
	context["cancelled_by"] = cancelled_by

	template_name = public_calendar.get("cancellation_template") or "Public Calendar - Cancellation"

	_send_templated_email(
		recipient=recipient,
		template_name=template_name,
		context=context,
		attachments=[ics_attachment],
		reference_doctype="Event",
		reference_name=event.name,
	)


def send_reminder(
	event: "frappe.Document",
	public_calendar: "frappe.Document",
	recipient: str,
) -> None:
	"""Send reminder email for upcoming appointment."""
	host, guests = get_host_and_guests(event, public_calendar)

	if not host:
		return

	context = _build_email_context(event, public_calendar, host, guests)
	context["cancel_url"] = get_rsvp_url(event.name, recipient, "cancel")

	template_name = public_calendar.get("reminder_template") or "Public Calendar - Reminder"

	_send_templated_email(
		recipient=recipient,
		template_name=template_name,
		context=context,
		reference_doctype="Event",
		reference_name=event.name,
	)


def send_reschedule_notification(
	event: "frappe.Document",
	public_calendar: "frappe.Document",
	recipient: str,
	rescheduled_by: str,
) -> None:
	"""Send reschedule email with updated ICS attachment."""
	host, guests = get_host_and_guests(event, public_calendar)

	if not host:
		return

	# Build attendee list
	attendees = [
		{"email": host["email"], "name": host["full_name"], "status": "ACCEPTED", "rsvp": False},
	]
	for guest in guests:
		attendees.append(
			{
				"email": guest["email"],
				"name": guest["full_name"],
				"status": "NEEDS-ACTION",
				"rsvp": True,
			}
		)

	# Generate updated ICS (sequence 1 for update)
	ics_attachment = generate_ics_attachment(
		event=event,
		method="REQUEST",
		organizer_email=host["email"],
		organizer_name=host["full_name"],
		attendees=attendees,
		sequence=1,
	)

	context = _build_email_context(event, public_calendar, host, guests)
	context["rescheduled_by"] = rescheduled_by
	context["confirm_url"] = get_rsvp_url(event.name, recipient, "confirm")
	context["decline_url"] = get_rsvp_url(event.name, recipient, "decline")
	context["cancel_url"] = get_rsvp_url(event.name, recipient, "cancel")

	template_name = public_calendar.get("reschedule_template") or "Public Calendar - Reschedule"

	_send_templated_email(
		recipient=recipient,
		template_name=template_name,
		context=context,
		attachments=[ics_attachment],
		reference_doctype="Event",
		reference_name=event.name,
	)


def _build_email_context(
	event: "frappe.Document",
	public_calendar: "frappe.Document",
	host: dict,
	guests: list[dict],
) -> dict:
	"""Build common context dict for email templates."""
	starts_on = get_datetime(event.starts_on)
	ends_on = get_datetime(event.ends_on) if event.ends_on else None

	# For backwards compatibility and simpler templates, expose first guest as primary
	primary_guest = guests[0] if guests else {}

	return {
		"event": event,
		"event_name": event.name,
		"subject": event.subject,
		"description": event.description,
		"starts_on": starts_on,
		"ends_on": ends_on,
		"starts_on_formatted": format_datetime(starts_on, "EEEE, MMMM d, yyyy"),
		"start_time_formatted": format_datetime(starts_on, "h:mm a"),
		"end_time_formatted": format_datetime(ends_on, "h:mm a") if ends_on else None,
		"duration_minutes": int((ends_on - starts_on).total_seconds() / 60) if ends_on else None,
		"calendar": public_calendar,
		"calendar_title": public_calendar.title,
		# Host info
		"host_name": host.get("full_name"),
		"host_email": host.get("email"),
		# Primary guest info (for simple templates)
		"guest_name": primary_guest.get("full_name"),
		"guest_email": primary_guest.get("email"),
		# All guests (for advanced templates)
		"guests": guests,
		"site_url": get_url(),
	}


def _send_templated_email(
	recipient: str,
	template_name: str,
	context: dict,
	attachments: list | None = None,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
) -> None:
	"""Send an email using a Frappe Email Template."""
	if not frappe.db.exists("Email Template", template_name):
		frappe.log_error(
			f"Email template '{template_name}' not found",
			"Public Calendar Notification Error",
		)
		return

	template = frappe.get_doc("Email Template", template_name)

	# Render subject and message
	subject = frappe.render_template(template.subject, context)
	message = frappe.render_template(template.response, context)

	frappe.sendmail(
		recipients=[recipient],
		subject=subject,
		message=message,
		attachments=attachments,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
		now=True,
	)


def notify_booking(event: "frappe.Document", public_calendar: "frappe.Document") -> None:
	"""Send booking notifications based on calendar settings."""
	host, guests = get_host_and_guests(event, public_calendar)

	if not host:
		frappe.log_error(
			f"Could not identify host for event {event.name}",
			"Public Calendar Notification Error",
		)
		return

	if public_calendar.notify_host_on_booking:
		send_booking_notification(
			event=event,
			public_calendar=public_calendar,
			recipient=host["email"],
			recipient_name=host["full_name"],
			is_host=True,
		)

	if public_calendar.notify_guest_on_booking:
		for guest in guests:
			send_booking_notification(
				event=event,
				public_calendar=public_calendar,
				recipient=guest["email"],
				recipient_name=guest["full_name"],
				is_host=False,
			)


def notify_cancellation(
	event: "frappe.Document",
	public_calendar: "frappe.Document",
	cancelled_by: str,
) -> None:
	"""Send cancellation notifications based on calendar settings."""
	if not public_calendar.notify_on_cancellation:
		return

	host, guests = get_host_and_guests(event, public_calendar)

	if not host:
		return

	# Notify all parties except the one who cancelled
	if cancelled_by != host["email"]:
		send_cancellation_notification(event, public_calendar, host["email"], cancelled_by)

	for guest in guests:
		if cancelled_by != guest["email"]:
			send_cancellation_notification(event, public_calendar, guest["email"], cancelled_by)


# Jinja template methods (exposed via hooks.py)
def rsvp_confirm_url(event_name: str, email: str) -> str:
	"""Generate confirm RSVP URL. For use in Jinja templates."""
	return get_rsvp_url(event_name, email, "confirm")


def rsvp_decline_url(event_name: str, email: str) -> str:
	"""Generate decline RSVP URL. For use in Jinja templates."""
	return get_rsvp_url(event_name, email, "decline")


def rsvp_cancel_url(event_name: str, email: str) -> str:
	"""Generate cancel RSVP URL. For use in Jinja templates."""
	return get_rsvp_url(event_name, email, "cancel")


# Scheduled Tasks
# ---------------


def send_appointment_reminders():
	"""
	Send reminder emails for upcoming appointments.

	Runs hourly. Finds events starting within the reminder window
	that haven't had reminders sent yet (checked via Comment).
	"""
	# Get all calendars with reminders enabled
	calendars = frappe.get_all(
		"Public Calendar",
		filters={
			"enabled": 1,
			"send_reminder": 1,
		},
		fields=["name", "user", "reminder_minutes_before"],
	)

	if not calendars:
		return

	now = now_datetime()

	for cal in calendars:
		reminder_minutes = cal.reminder_minutes_before or 60

		# Find events starting between now and now + reminder_minutes
		# that are linked to this calendar via ref_type/ref_name
		window_start = now
		window_end = add_to_date(now, minutes=reminder_minutes)

		Event = DocType("Event")
		events = (
			frappe.qb.from_(Event)
			.select(Event.name)
			.where(
				(Event.ref_type == "Public Calendar")
				& (Event.ref_name == cal.name)
				& (Event.status != "Cancelled")
				& (Event.starts_on >= window_start)
				& (Event.starts_on <= window_end)
			)
			.run(as_dict=True)
		)

		calendar_doc = frappe.get_doc("Public Calendar", cal.name)

		for event_data in events:
			# Check if reminder already sent via Comment
			if _reminder_already_sent(event_data.name):
				continue

			event = frappe.get_doc("Event", event_data.name)
			host, guests = get_host_and_guests(event, calendar_doc)

			if not host:
				continue

			# Send reminder to host
			try:
				send_reminder(event, calendar_doc, host["email"])
			except Exception:
				frappe.log_error(
					f"Failed to send reminder for {event.name} to {host['email']}",
					"Public Calendar Reminder Error",
				)

			# Send reminder to all guests
			for guest in guests:
				try:
					send_reminder(event, calendar_doc, guest["email"])
				except Exception:
					frappe.log_error(
						f"Failed to send reminder for {event.name} to {guest['email']}",
						"Public Calendar Reminder Error",
					)

			# Mark reminder as sent via Comment
			frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Info",
					"reference_doctype": "Event",
					"reference_name": event.name,
					"content": "Reminder sent",
				}
			).insert(ignore_permissions=True)

	frappe.db.commit()


def _reminder_already_sent(event_name: str) -> bool:
	"""Check if a reminder has already been sent for this event."""
	return frappe.db.exists(
		"Comment",
		{
			"reference_doctype": "Event",
			"reference_name": event_name,
			"content": "Reminder sent",
		},
	)
