# Habit

A recurring intention the user wants to perform on a schedule (e.g. "meditate", "no soda", "run"). The durable object around which completions and streaks are organized.

## Identity and attributes

A habit belongs to exactly one user and has a name, a schedule (which days it is expected), and a creation date. Its current streak is derived from its completions, not stored as an independent fact.

## Invariants

- A habit name is non-empty and unique per user.
- A habit always has a schedule; "every day" is the default, not the absence of one.
- Archiving a habit preserves its history; completions are never deleted when a habit is archived.
