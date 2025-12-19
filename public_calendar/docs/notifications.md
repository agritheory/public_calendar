<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Notifications

Public Calendar sends notifications for appointment lifecycle events using Frappe's Notification DocType. This approach supports multiple channels including Email, Slack, System Notification, and SMS. Email notifications include ICS calendar attachments that recipients can add to their calendar application.

## Notification Types

| Type | Trigger | Recipients |
| :--- | :------ | :--------- |
| Booking Confirmation | New appointment created | Host and/or guest based on settings |
| Cancellation | Appointment cancelled or declined | All participants except the person who cancelled |
| Reschedule | Appointment time changed | All participants except the person who rescheduled |
| Reminder | Scheduled time before appointment | Host and guest |

## Configuration

### Notification Toggles

| Field | Description |
| :---- | :---------- |
| Notify Host on Booking | Send confirmation to the calendar owner when someone books |
| Notify Guest on Booking | Send confirmation to the person who booked |
| Notify On Cancellation | Send cancellation notices when appointments are cancelled |
| Send Reminder | Enable reminder notifications before appointments |
| Reminder Minutes Before | How many minutes before the appointment to send reminders |

### Notification Selection

Each notification type can use a custom Notification record. If no notification is specified, the system uses default notifications created during installation.

| Field | Default Notification |
| :---- | :------------------- |
| Host Booking Notification | Public Calendar - Booking Confirmation |
| Guest Booking Notification | Public Calendar - Booking Confirmation |
| Cancellation Notification | Public Calendar - Cancellation |
| Reschedule Notification | Public Calendar - Reschedule |
| Reminder Notification | Public Calendar - Reminder |

## Channels

Frappe's Notification DocType supports multiple delivery channels. Public Calendar works with all of them, with special handling for email.

| Channel | ICS Attachment | Notes |
| :------ | :------------: | :---- |
| Email | Yes | Full support with calendar attachments |
| Slack | No | Message only, no attachments |
| System Notification | No | Appears in Frappe's notification tray |
| SMS | No | Short message, consider template length |

For email channel notifications, the system automatically attaches an ICS calendar file. Other channels receive the notification message without attachments.

### Channel Configuration

To use a non-email channel:

1. Navigate to the Notification record
2. Change the Channel field to the desired option
3. For Slack, configure the Slack Webhook URL in the notification
4. Adjust the message content as needed for the channel

A single Public Calendar can mix channels. For example, configure the host booking notification to use Slack while the guest notification uses email with ICS attachments.

## Template Variables

Notification templates have access to these variables through Jinja templating.

### Event Information

| Variable | Description |
| :------- | :---------- |
| `subject` | Event subject line |
| `description` | Event description or notes |
| `starts_on` | Start datetime object |
| `ends_on` | End datetime object |
| `starts_on_formatted` | Formatted start date (for example, "Monday, January 15, 2025") |
| `start_time_formatted` | Formatted start time (for example, "2:30 PM") |
| `end_time_formatted` | Formatted end time |
| `duration_minutes` | Appointment length in minutes |

### Participant Information

| Variable | Description |
| :------- | :---------- |
| `host_name` | Full name of the calendar owner |
| `host_email` | Email address of the calendar owner |
| `guest_name` | Full name of the primary guest |
| `guest_email` | Email address of the primary guest |
| `guests` | List of all guest participants |
| `is_host` | Boolean indicating if recipient is the host |
| `recipient_email` | Email address of the current recipient |

### Action URLs

| Variable | Description |
| :------- | :---------- |
| `confirm_url` | Link to confirm attendance |
| `decline_url` | Link to decline the invitation |
| `cancel_url` | Link to cancel the appointment |

### Context Variables

| Variable | Description |
| :------- | :---------- |
| `calendar` | The Public Calendar document |
| `calendar_title` | Title of the Public Calendar |
| `event` | The Event document |
| `event_name` | Event document name |
| `site_url` | Base URL of the site |
| `cancelled_by` | Email of person who cancelled (cancellation only) |
| `rescheduled_by` | Email of person who rescheduled (reschedule only) |

## Creating Custom Notifications

To create a custom notification:

1. Navigate to Notification List
2. Click New
3. Set Document Type to "Event"
4. Set Event to "Custom" (notifications are triggered programmatically)
5. Choose the desired Channel
6. Write the Subject and Message using Jinja variables
7. Save the notification
8. Link it to the appropriate field on the Public Calendar

### Example: Slack Booking Notification

```
Subject: New Booking: {{ subject }}

Message:
📅 *New Appointment Booked*

*{{ subject }}*
Date: {{ starts_on_formatted }}
Time: {{ start_time_formatted }} - {{ end_time_formatted }}
Guest: {{ guest_name }} ({{ guest_email }})

Calendar: {{ calendar_title }}
```

## RSVP System

Notification messages can include action links that allow recipients to respond without logging in. These links point to `/rsvp` with secure query parameters.

### RSVP Actions

| Action | Effect |
| :----- | :----- |
| Confirm | Sets participant RSVP status to "Accepted" |
| Decline | Sets participant RSVP status to "Declined" and notifies others |
| Cancel | Sets participant RSVP to "Cancelled", marks Event as "Cancelled", and notifies others |

### Security

RSVP links use HMAC tokens generated from:

- The event name
- The recipient's email address
- The action type
- The site's secret key

Tokens are deterministic and do not require database storage. Each combination of event, email, and action produces a unique token. Invalid or tampered tokens are rejected.

### RSVP Page

The `/rsvp` page displays the result of the action:

- Green confirmation box for successful confirms
- Yellow notice for declines
- Red notice for cancellations
- Error message for invalid links

## ICS Attachments

Email notifications include an ICS (iCalendar) file attachment. Calendar applications like Outlook, Google Calendar, and Apple Calendar can import these files to add or update events.

### ICS Methods

| Method | Usage |
| :----- | :---- |
| REQUEST | New invitation or update (booking, reschedule) |
| CANCEL | Appointment cancellation |

The ICS file includes:

- Event UID derived from the Frappe Event name
- Sequence number (0 for new, 1 for updates/cancellations)
- Organizer set to the calendar host
- Attendees with their participation status
- Event times, subject, and description

### Sequence Numbers

ICS sequence numbers help calendar applications track changes:

| Sequence | Meaning |
| -------: | :------ |
| 0 | Initial booking |
| 1 | Reschedule or cancellation |

Calendar applications use the sequence number to determine if an ICS file contains newer information than what they already have.

## Desk Integration

When events are modified through the Frappe desk interface, the system detects changes and sends appropriate notifications:

- Changing Event status to "Cancelled" triggers cancellation notifications
- Modifying `starts_on` or `ends_on` triggers reschedule notifications
- Deleting an Event triggers cancellation notifications

This integration ensures all participants stay informed regardless of how changes are made.

## Reminders

The reminder system runs as a scheduled task. To enable reminders:

1. Set Send Reminder to enabled on the Public Calendar
2. Configure Reminder Minutes Before (for example, 60 for one hour)
3. Ensure the Frappe scheduler is running

The system checks hourly for events starting within the reminder window and sends notifications to both host and guest. Each event only receives one reminder, tracked via a Comment on the Event.