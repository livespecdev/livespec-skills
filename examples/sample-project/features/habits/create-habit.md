---
links:
  persona: [daily-tracker]
  goal: [build-lasting-habits]
  entity: [habit]
---

# Create Habit

As a daily tracker, I want to create a habit with a name and a schedule so that I have something concrete to check in against every day.

## Requirements

- [ ] REQ-1: A user can create a habit by giving it a name and a schedule.
  - [ ] AC-1.1: A habit name between 1 and 60 characters is accepted and the habit appears in the user's list immediately.
  - [ ] AC-1.2: An empty name is rejected with an inline message and no habit is created.
  - [ ] AC-1.3: The schedule defaults to "every day" when the user does not choose one.
- [ ] REQ-2: A user can pick which days of the week a habit is expected.
  - [ ] AC-2.1: The user can select any non-empty subset of the seven weekdays.
  - [ ] AC-2.2: Deselecting every day is prevented; at least one day must remain selected.
- [ ] REQ-3: Habit names are unique per user.
  - [ ] AC-3.1: Creating a habit whose name matches an existing active habit (case-insensitive) is rejected with a message pointing to the existing one.

## Assumptions

- [ ] AS-1: A user manages a modest number of habits (under 50), so the habit list needs no pagination in v1.

## Questions

- [ ] Q-1: Should archived habit names free up for reuse, or stay reserved to keep history unambiguous?
