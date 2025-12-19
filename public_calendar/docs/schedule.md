<!-- Copyright (c) 2025, AgriTheory and contributors
For license information, please see license.txt-->

# Scheduling

The scheduling feature allows visitors to book appointments on a user's calendar. Unlike the read-only calendar view, scheduling provides an interactive interface for selecting available time slots.

## Accessing the Scheduler

The scheduler is available at two URLs:

| URL | Description |
| :-- | :---------- |
| `/schedule` | Lists all calendars that accept bookings |
| `/schedule?name=route` | Opens the booking interface for a specific calendar |

Only calendars with Allow Booking enabled appear in the scheduler.

## Configuration

### Scheduling Settings

| Field | Description | Default |
| :---- | :---------- | ------: |
| Allow Booking | Enables the scheduling interface for this calendar | Off |
| Slot Duration | Length of each bookable time slot in minutes | 30 |
| Max Meeting Duration | Maximum appointment length visitors can request | Slot Duration |
| Buffer Time | Required gap between appointments in minutes | 0 |
| Min Notice Hours | How far in advance appointments must be booked | 0 |
| Max Advance Days | How far into the future appointments can be booked | 30 |

### Working Hours

The Working Hours editor defines when appointments can be scheduled. Each day of the week can have:

- No time blocks (shown as "Closed")
- One or more time blocks defining available hours

To configure working hours:

1. Open the Public Calendar record
2. Locate the Working Hours section
3. Click the + button under a day to add a time block
4. Set the start and end times for each block
5. Click the × button to remove a block

Time blocks cannot overlap within the same day.

### Display Options

| Field | Description |
| :---- | :---------- |
| Busy Text | Text shown for existing events on the calendar |
| Booking Dialog Title | Header text for the booking popup |

## Booking Process

When a visitor selects an available time slot:

1. A dialog appears with the selected date and time
2. If Max Meeting Duration exceeds Slot Duration, a duration dropdown appears
3. The visitor enters a subject (required) and optional notes
4. Clicking "Confirm" creates the appointment

The system validates the selection before showing the dialog. Invalid slots (outside working hours, too soon, too far ahead, or conflicting with buffer time) cannot be selected.

## Slot Availability Rules

A time slot is available when all of these conditions are met:

| Rule | Description |
| :--- | :---------- |
| Within working hours | Slot falls entirely within a configured time block |
| Sufficient notice | Slot starts at least Min Notice Hours from now |
| Within booking window | Slot starts no more than Max Advance Days from now |
| No conflicts | No existing events within Buffer Time of the slot |
| Not in past | Slot has not already started |

## Created Events

When a visitor books an appointment, the system creates an Event with:

- Subject and description from the booking dialog
- Start and end times based on the selected slot and duration
- Event Type set to "Public"
- Reference to the Public Calendar record
- Two participants: the calendar owner and the booking visitor

If the visitor has a Contact record with a matching email, the system also links any associated parties (Customer, Supplier, Lead) as additional participants.

## Authentication

The scheduling interface requires authentication. Visitors must log in before they can book appointments. This ensures:

- The system knows who is booking
- Contact and party linking works correctly
- Notifications reach the correct email address

Guest booking is not currently supported.