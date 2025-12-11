# Copyright (c) 2025, AgriTheory and contributors
# For license information, please see license.txt

"""
Event document hooks for Public Calendar.

Handles notifications when events are modified or cancelled from the Frappe desk.
"""

import frappe

from public_calendar.public_calendar.notifications import (
	get_host_and_guests,
	get_public_calendar_for_event,
	notify_cancellation,
	send_reschedule_notification,
)


def on_update(doc, method=None):
	"""Handle Event updates - detect cancellation or reschedule."""
	public_calendar = get_public_calendar_for_event(doc)
	if not public_calendar:
		return

	if doc.status == "Cancelled" and doc.has_value_changed("status"):
		_handle_cancellation(doc, public_calendar)

	elif doc.has_value_changed("starts_on") or doc.has_value_changed("ends_on"):
		_handle_reschedule(doc, public_calendar)


def on_trash(doc, method=None):
	"""Handle Event deletion - treat as cancellation."""
	public_calendar = get_public_calendar_for_event(doc)
	if not public_calendar:
		return

	_handle_cancellation(doc, public_calendar)


def _handle_cancellation(doc, public_calendar):
	"""Send cancellation notifications."""
	if not public_calendar.notify_on_cancellation:
		return

	cancelled_by_email = frappe.db.get_value("User", frappe.session.user, "email")

	notify_cancellation(doc, public_calendar, cancelled_by_email)


def _handle_reschedule(doc, public_calendar):
	"""Send reschedule notifications."""
	host, guests = get_host_and_guests(doc, public_calendar)
	print(host)
	if not host:
		return

	# Notify all participants about the reschedule
	rescheduled_by_email = frappe.db.get_value("User", frappe.session.user, "email")
	print(rescheduled_by_email)
	# Notify host if they didn't initiate the change
	if public_calendar.notify_host_on_booking and rescheduled_by_email != host["email"]:
		send_reschedule_notification(doc, public_calendar, host["email"], rescheduled_by_email)

	# Notify guests if host initiated the change
	if public_calendar.notify_guest_on_booking:
		for guest in guests:
			if rescheduled_by_email != guest["email"]:
				send_reschedule_notification(doc, public_calendar, guest["email"], rescheduled_by_email)
