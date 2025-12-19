<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Public Calendar

Public Calendar extends Frappe's Event system to support public-facing calendar views and appointment scheduling. It allows organizations to share availability and accept bookings from authenticated users.

## Overview

The application provides three main capabilities:

1. **Public Calendar View** - Display events from one or more users on a read-only calendar accessible without login
2. **Appointment Scheduling** - Allow visitors to book time slots on a user's calendar
3. **Email Notifications** - Send confirmations, reminders, and cancellation notices with ICS calendar attachments

## Key Concepts

### Public Calendar Document

A Public Calendar record links a Frappe User to public-facing calendar pages. Each Public Calendar defines:

- Which user's events to display
- Whether the calendar is publicly visible
- Whether visitors can book appointments
- Working hours and scheduling constraints
- Notification preferences and email templates

A single user can have multiple Public Calendar records with different settings. For example, one calendar for general meetings and another for specific consultation types.

### Events and Participants

Public Calendar uses Frappe's built-in Event DocType. When a visitor books an appointment, the system creates an Event with both the calendar owner and the booker as participants. This integration means:

- Events appear in the user's standard Frappe calendar
- Changes made in the desk interface trigger appropriate notifications
- Existing Event features like recurrence and reminders remain available

### RSVP System

Email notifications include secure links that allow recipients to confirm, decline, or cancel appointments without logging in. These links use cryptographic tokens tied to the specific event and recipient.

## Installation

Add Public Calendar to an existing Frappe bench:

```shell
bench get-app public_calendar --branch version-15 https://github.com/agritheory/public_calendar.git
bench --site your-site install-app public_calendar
```

The installation process creates default email templates for booking confirmations, cancellations, reschedules, and reminders.

## Quick Start

1. Navigate to Public Calendar in the search bar
2. Create a new Public Calendar record
3. Set the User field to the calendar owner
4. Enter a URL-friendly Route (for example, `john-smith`)
5. Configure Working Hours using the visual editor
6. Enable Is Public to make the calendar visible at `/calendar?name=your-route`
7. Enable Allow Booking to accept appointments at `/schedule?name=your-route`

## Documentation

- [Calendar View](calendar.md) - Displaying public calendars
- [Scheduling](schedule.md) - Appointment booking configuration
- [Notifications](notifications.md) - Email templates and RSVP handling