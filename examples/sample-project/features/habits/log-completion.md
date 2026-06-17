---
links:
  persona: [daily-tracker]
  pain_point: [streaks-break-silently]
  entity: [habit]
  constraint: [offline-first-logging]
  feature:
    requires: [create-habit]
---

# Log Completion

As a daily tracker, I want to mark a habit as done for today in a single tap so that my check-in never gets in the way, even when I am offline.

## Requirements

- [ ] REQ-1: A user can mark a habit complete for the current day in one action.
  - [ ] AC-1.1: Tapping the habit toggles today's completion on, and tapping again toggles it off.
  - [ ] AC-1.2: The current streak count updates immediately to reflect the change.
- [ ] REQ-2: A completion logged while offline is preserved and reconciled when connectivity returns.
  - [ ] AC-2.1: Logging a completion with no network connection succeeds and is visible immediately.
  - [ ] AC-2.2: When connectivity returns, locally logged completions are synced with no user action.
  - [ ] AC-2.3: If the same day is logged on two devices, reconciliation keeps a single completion for that day.
- [ ] REQ-3: A user can log a completion for a past day they missed marking.
  - [ ] AC-3.1: The user can mark any day within the last 7 days as complete or incomplete.

## Assumptions

- [ ] AS-1: A completion is a per-day boolean; counting multiple completions in one day is out of scope for v1.

## Questions

- [ ] Q-1: When a past day is backfilled, should a broken streak retroactively heal, or stay broken to reflect what actually happened?
