<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Calendar View

The calendar view displays events from Public Calendar records on a read-only calendar. Visitors can see when a user is busy without viewing event details.

## Accessing the Calendar

The calendar is available at two URLs:

| URL | Description |
| :-- | :---------- |
| `/calendar` | Shows all public calendars with a dropdown selector |
| `/calendar?name=route` | Shows a specific calendar filtered by its Route field |

Only calendars with Is Public enabled appear in the public view.

## Configuration

### Basic Settings

| Field | Description |
| :---- | :---------- |
| Title | Display name shown in the calendar selector and page header |
| User | The Frappe User whose events appear on this calendar |
| Route | URL-safe identifier used in the `name` query parameter |
| Is Public | When enabled, the calendar appears at `/calendar` |
| Enabled | Master toggle to activate or deactivate the calendar |

### Display Options

| Field | Description |
| :---- | :---------- |
| Busy Text | Text shown for events instead of their actual subject (default: "Unavailable") |
| Holiday List | Optional link to a Holiday List to mark non-working days |

The Busy Text setting helps protect privacy. Instead of showing "Meeting with Client X", visitors see the configured text.

## How Events Are Selected

The calendar displays events where:

1. The Public Calendar's User is listed as a participant on the Event
2. The Event status is not "Cancelled"
3. The Event falls within the currently visible date range

Events are matched through the Event Participants child table. The participant's Reference DocType must be "User" and Reference DocName must match the Public Calendar's User field.

## User Interface

The calendar uses FullCalendar with month, week, and day views. The interface includes:

- Navigation buttons to move between time periods
- View switchers for month, week, and day
- A "Today" button to return to the current date
- A dropdown to switch between available public calendars

When viewing a specific calendar, the page displays the calendar's Title and the system timezone.

## Sharing a Calendar

To share a calendar link with others, use the full URL with the route parameter:

```
https://your-site.com/calendar?name=john-smith
```

The calendar respects Frappe's guest access settings. If your site requires login for web pages, visitors must authenticate before viewing the calendar.

## Timezone Handling

The calendar displays times in the server's system timezone. The timezone label appears below the calendar title so visitors understand which timezone applies. Events store their times in the database without timezone conversion.