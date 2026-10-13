---
name: sync-spec
description: |
  Reconciles spec files with what was actually built: checks resolved acceptance criteria, adds
  resolution notes, updates ## Tech / ## UX notes, captures new behavior as REQs or LIM items, and
  promotes standing rules discovered during development to concepts for review. Presents a summary
  before editing. Use when the user signals completion ("done", "ship it", "looks good"), wants to sync
  what was built, or update the spec. Not for active debugging or repos with no spec manifest.
argument-hint: <feature-slug>
---

# Sync Spec

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v0.1.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Reconcile the spec files with the reality of what was built. There is no server: this is `Edit` on local `features/` and concept files, surfaced as a git diff the user reviews. Work in this order: **summarize → confirm → edit → report → discover**.

**Never edit silently.** Present the planned changes and get confirmation first, so the developer reviews without leaving the CLI.

## Step 1: Analyze what changed

`Read` the feature (`features/**/{slug}.md`) and compare it against the implementation (the code, the `implements:` / `see-spec:` markers, §9.4). Determine:

- **Acceptance criteria**: which ACs are now satisfied and should be `[x]`; which were dropped and should be `[-]` with a reason (§8.1, §8.3). Never renumber or delete IDs.
- **Resolution notes**: which `Q` items the implementation answered and which `LIM` items it lifted, to record with a `→ ` note (§8.1).
- **`UX` / `TECH` directions**: which open directions the implementation applied (`[x]`), which it abandoned (`[-]` with a `→ ` note naming the replacement), and which durable choices it made that no item records yet (new `UX-N` / `TECH-N`, §8.2). Supporting rationale goes in the `## UX` / `## Tech` prose.
- **New behavior**: did the implementation add behavior the spec never described? That is a new REQ/AC (evolution) or a new feature (genuinely new capability), see the framework below.
- **Discoveries**: standing rules, patterns, or constraints that emerged and belong as concepts (§6.5).

## Step 2: Present the plan

Show a short, readable summary, grouped by what you will edit directly versus what you will propose for review:

```
Reconcile features/habits/log-completion.md:

Direct edits (the work product):
  - AC-1.1, AC-1.2, AC-2.1, AC-2.2 → [x] (implemented, markers placed)
  - AC-2.3 → [x], resolution note: idempotent upsert by (habit_id, day)
  - Q-1 → [x], resolution note: backfill heals the streak (decided this session)
  - ## Tech: add the append-only-log + idempotent-reconcile approach

Propose for review (product decisions):
  - New concept tech/architecture_decision/idempotent-completion-sync.md
  - Link it from this feature
```

## Step 3: Confirm or adjust

Wait for confirmation. Use `AskUserQuestion` where a specific decision needs the user (especially marking a REQ `[x]` while ACs remain open, §8.2, or whether something is evolution vs a new feature). Apply requested changes; skip what the user wants omitted.

## Step 4: Edit the files

Only after confirmation:

**Direct edits** (features are the work product):
- `Edit` checkboxes `- [ ]` → `- [x]` / `- [-]` (§8.1). One `→ ` resolution note per closed item at most (§8.1).
- `Edit` `## Tech` / `## UX`: flip applied directions to `[x]`; record a changed direction as a new item, with the old one `[-]` and `→ Superseded by [TECH-N]: ...` (never rewrite a closed direction to say the opposite); add new directions declaratively (target state, not "what I did").
- Append new REQs/ACs/LIM/UX/TECH items with the **next free integer** in their section; immutable IDs, gaps valid, never renumber (§8.3).
- Preserve unknown frontmatter keys and unrecognized sections (losslessness, §14). Keep the diff tight.

**Proposed edits** (product decisions, reviewed via diff):
- New or changed concepts under `product|ux|tech/{type}/{slug}.md`: present the file, write on approval.
- A genuinely new feature: present it, write on approval (or hand to `/specify-feature`).

## Step 5: Report

Summarize what was reconciled: which ACs are now `[x]`, which notes were added, which concepts you proposed. The diff is the record.

## Step 6: Surface discovered standing rules

Reflect on the implementation and identify reusable rules that emerged (§6.5):

- A technical pattern other features should follow → `architecture_decision` or a `*_convention` type under `tech/`.
- A limit or quantitative rule that constrains multiple features → `constraint` under `product/`.
- A coding or API rule not yet documented → `coding_standard` / `api_convention`.
- A new page, route, or full-screen flow the implementation introduced, in a project that keeps `ux/screen/` → a `screen` under `ux/` (§6.2), following the sections its sibling screen files already use (a concept body is free-form, §6.4), plus `links.screen` on the feature. A durable change to an existing surface is a proposed edit to its screen file; the acceptance criteria stay in the feature.

For each, propose the concept file and let the user approve via the diff before writing (this mirrors the old human-review queue: product-level decisions are proposed, not imposed). Also check whether the feature should link an existing concept it relied on, and propose adding that link (§9.2).

If nothing reusable emerged, end the skill without asking.

---

## Evolution vs new functionality

Before planning, classify each change. The deciding question: **is this the same user problem, solved differently?**

### Evolution → edit the existing feature

The intent is unchanged; the approach evolved. Examples: a better technical approach for the same outcome, edge cases discovered during implementation, a UX refinement for the same goal, a bug that revealed a spec gap.

- Functional clarifications → edit the REQ/AC body (bodies are mutable, §8.3) or add a new AC.
- UX changes → `UX` items (a changed direction supersedes the old item, §8.1).
- Technical changes → `TECH` items, same rule.
- Newly discovered edge cases → new ACs under the relevant REQ.

### New functionality → a new feature

The product's functional coverage expanded: a capability that did not exist, a different user problem, a user story the original feature never intended to cover. Propose a new feature (hand to `/specify-feature`).

**Avoid feature sprawl**: implementation details, technical improvements, and edge-case handling are not new features. They are notes and ACs on the existing one.

### What goes where

| Change | Where | How |
|---|---|---|
| Implementation choice | `TECH` item in `## Tech` (+ prose for rationale) | `Edit` the feature |
| UI/UX choice | `UX` item in `## UX` (+ prose for rationale) | `Edit` the feature |
| Changed direction | old item `[-]` + `→ Superseded by [...]`, new item | `Edit` the feature |
| Functional clarification | REQ/AC body | `Edit` the feature |
| Resolved AC | `[x]` (+ optional `→` note) | `Edit` the feature |
| Answered Q / lifted LIM | `[x]` + `→` resolution note | `Edit` the feature |
| Dropped criterion | `[-]` + reason | `Edit` the feature |
| Missing edge case | new AC under its REQ | `Edit` the feature |
| Reusable pattern / rule | concept under `tech/` or `product/` | propose, write on approval |
| Genuinely new capability | new feature | propose, then `/specify-feature` |
