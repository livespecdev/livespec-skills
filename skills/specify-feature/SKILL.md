---
name: specify-feature
description: |
  Authors or refines a single spec feature file: the summary paragraph, requirements, nested
  acceptance criteria, assumptions, questions, issues, and concept links. Use when the user discusses
  new functionality, mentions a spec, requirements, or acceptance criteria for one feature, or wants an
  existing feature sharpened. Owns the core spec, not UX framing (/frame-ux) or tech framing
  (/frame-tech). Not for multi-feature decomposition (/scope) or implementation.
argument-hint: [feature-description or feature-slug]
---

# Specify Feature

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Write a clear, well-scoped feature as a single markdown file under `features/`, focused on user value and observable behavior. A feature describes **target state**: what the software *is*, not the work to do. It should read the same before and after implementation. Structure matters, agents and humans consume atomic, typed, linked spec items far better than prose (`SPEC.md` §8).

**You own the core spec:** the summary paragraph (§7.4), requirements and acceptance criteria (§8), assumptions, questions, issues, and the concept links in frontmatter (§9.2).

**You do not own:** `## UX` notes (use `/frame-ux`), `## Tech` notes (use `/frame-tech`), or implementation.

## Determine intent

- **Refining** an existing feature: `Read` `features/**/{slug}.md` in full and identify what is weak (missing ACs, vague REQs, unresolved questions).
- **Creating** a new one: understand what problem it solves, who benefits most, and the smallest version that delivers value.

Locate the project root (nearest manifest, `product-spec.yaml` or `livespec.yaml`, §3.1) and read its `mode` (§12) first.

## Is this actually a feature?

A feature ships in a PR with verifiable acceptance criteria and stays conceptually present afterward (§6.5). The litmus test: can you write ACs a PR can satisfy?

- "Full-text search across documents" → feature.
- "We index PDFs" → a REQ within that feature.
- "Results highlight matching terms" → an AC.
- "Search" → an area (a `features/search/` folder), not a feature.

If what was described is really a behavior of an existing feature, add a REQ or AC there instead of creating a new file (the §6.5 feature-vs-spec-item frontier: prefer spec item first, extract later). If it is a standing rule that applies across features, it is a concept (§6.5), propose it under `product|ux|tech/` and link it, do not bury it as a REQ.

## Gather context

- **Personas** (`product/persona/*.md`): who benefits, their goals and pain points.
- **Pain points and goals** (`product/pain_point/`, `product/goal/`): the "why" you will link to.
- **Constraints** (`product/constraint/*.md`): standing limits this feature must respect; link them rather than restating them as REQs.
- **Entities and external systems** (`product/entity/`, `tech/external_system/`): domain objects it manipulates, services it integrates with.
- **Screens** (`ux/screen/*.md`): the surfaces the feature lands on, when the project keeps a screen inventory.
- **Existing features** (`Glob features/**`): overlap or dependencies.

## Right-sizing

Use the §7.5 smell tests, not numeric limits. The feature's summary should hold in one sentence without conjunction-stuffing; its REQs should serve one audience; it should not naturally split into PRs whose ACs never touch. When in doubt, start coarser and split later (§7.5). If a feature is genuinely too big, decompose it into siblings along natural boundaries (different flows, personas, data domains) and relate them via `links.feature` (§7.2); hand off to `/scope` if it is more than a clean split.

## Write the spec

### Summary paragraph (§7.4)

Every feature opens with exactly one paragraph summarizing it in human terms. Its presence is required; its form is your choice. Recommended idioms:

- **User-facing**: `As a {persona}, I want {capability} so that {value}.`
- **Subsystem / integration**: `When {trigger}, the system {action} so that {outcome}.`

Pick the primary persona; describe the capability and its value, not the solution.

- Good: "As a daily tracker, I want to mark a habit done in one tap so that my check-in never gets in the way."
- Weak: "As a user, I want a checkbox button." (no persona specificity, no value)

### Requirements (§8.1, §8.2)

A `REQ` is a top-level checkbox in `## Requirements`, at 0-space indent:

```markdown
## Requirements

- [ ] REQ-1: A user can mark a habit complete for the current day in one action.
  - [ ] AC-1.1: Tapping the habit toggles today's completion on; tapping again toggles it off.
  - [ ] AC-1.2: The current streak count updates immediately.
- [ ] REQ-2: A completion logged offline is preserved and reconciled when connectivity returns.
  - [ ] AC-2.1: Logging with no network connection succeeds and is visible immediately.
```

Each REQ:

- **Captures one distinct functional need**, solution-agnostic (the need, not the implementation).
- **Describes observable behavior.** A business analyst should understand it from outside the system, through the UI, API responses, or observable effects. Internal schemas, class names, and endpoints belong in `## Tech` (via `/frame-tech`), not in a REQ. The exception is infrastructure features where the internal system is the product (e.g. "the API returns 429 when the rate limit is exceeded").

Avoid: "Add a checkbox button" (UI solution), "Use the X library" (implementation), "Make it fast" (not observable, and unmeasurable), "Add a `streak` column" (internal schema).

### Acceptance criteria (§8.1, §8.3)

An `AC` is nested **exactly one level (2 spaces)** under its parent REQ; the parent is determined structurally by indentation, no explicit reference (§8.2). AC IDs follow the nesting: `AC-{req}.{n}` (§8.3). Each AC is outcome-focused and testable (clear pass/fail). Cover the happy path, plus edge cases, validation, and error states as separate ACs where they matter:

- Happy path: "User can download a CSV containing all their data."
- Edge case: "Export works when the user has zero items."
- Validation: "An export with no permission is rejected with a clear message."
- Error: "A failed export explains what went wrong and how to retry."

Deeper nesting (`AC-1.1.1`) is invalid; if a REQ wants sub-structure, split it into multiple REQs (§8.1). AC bodies may use inline formatting but no block constructs (no headings, code fences, tables); elaboration goes to `## Tech` or `## UX` (§8.1).

### Assumptions, questions, issues (§8.2)

- `AS` items in `## Assumptions`: what the spec relies on, to be flagged if invalidated.
- `Q` items in `## Questions`: unresolved questions (but prefer to resolve them now, see below).
- `LIM` items in `## Limitations`: known, accepted gaps between what the feature should do and what it does today, in the present tense. Never a task, never a bug scheduled for a fix (that goes in the issue tracker, §8.2).

### Resolve questions immediately

When you spot a decision that needs resolution, ask it now with `AskUserQuestion` rather than listing it. Offer 2-3 concrete answers (recommended first) plus **"Leave open"**. Only "Leave open" becomes a `Q` item in the file. Batch up to 4 per call and fold answers into the spec.

### Concept links (§9.2)

Link the feature to the concepts that matter in frontmatter, keyed by singular type slug:

```yaml
---
links:
  persona: [daily-tracker]
  constraint: [offline-first-logging]
  entity: [habit]
  screen: [habit-list]
  feature:
    requires: [create-habit]
---
```

`constraint: [...]` already means "respects", `entity: [...]` "manipulates", `external_system: [...]` "integrates with", `screen: [...]` "lands on" (§7.2); no explicit relation typing needed for concepts. Link the relations that structurally matter; in-prose mentions are reading aids, not a substitute (§9.5). Write them as relative Markdown links to the target file, with link text that reads naturally in the sentence (`respects [offline-first logging](../../product/constraint/offline-first-logging.md)`); keep `[[type:slug]]` only in a project that already uses it throughout. Never emit an empty frontmatter block (§5).

## Validate before writing

- Not a feature: it is really a REQ/AC on an existing feature, or a concept → put it there instead.
- Solution-first REQ: "Add a dropdown" → "System supports multiple formats".
- Epic in disguise: re-check the §7.5 smell tests; split if they confirm.
- Orphaned AC: every AC sits under a REQ by indentation.
- Implementation leaking in: schema, endpoints, class names in REQs/ACs → move to `## Tech`.
- Vague AC: "Works well" → a specific observable outcome.
- Missing "why": link a persona or pain point.

## Write or propose

Features are the work product: **write the file directly** when the user asked for the feature.

- **New feature**: `Write` `features/{area}/{slug}.md`. Start from the H1 (with frontmatter above it only if there are links). Assign `REQ-1`, `REQ-2`, ... and ACs in sequence.
- **Refining**: `Edit` the file. Append new items with the **next free integer** in their section; never reuse or renumber existing IDs, even cancelled ones (§8.3). To drop an item, mark it `[-]` with a reason rather than deleting it (§8.3). Preserve unknown frontmatter and unrecognized sections (losslessness, §14).

When the change is really a product decision (a new concept, or a brand-new feature the user only hinted at), present it first and let the user confirm via the diff before writing.

## Present and hand off

Show the spec in a clean, scannable form for review (summary, REQs as numbered lines with ACs as nested bullets, no ID noise), iterate until the user is satisfied, then note the next steps: `/frame-ux` if UI is involved, `/frame-tech` before implementation, `/review-spec` for an independent critical read, then `/implement`.
