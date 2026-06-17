---
name: scope-features
description: |
  Decomposes natural-language intent into a plan of LiveSpec features to write or update (and any
  concepts worth extracting), iterates with the user, then writes the feature files. Use when the user
  describes what to build, says "scope this", "plan this work", or wants to break an idea into features.
  Not for specifying a single known feature (/specify-feature), implementation (/implement-feature), or
  framing (/ux-framing, /tech-framing). No delivery batches: sequencing lives in git and your issue tracker.
argument-hint: <natural-language-description>
---

# Scope Features

> **Format reference.** The `§N` citations point to the bundled LiveSpec spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft.2`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Decompose intent into LiveSpec features and write them as files under `features/`. There is no batch or delivery layer: LiveSpec describes the software, not the work on it (`SPEC.md` §1). Ordering a body of work is a git-branch and issue-tracker concern, out of scope here.

**Write nothing until the user approves the decomposition plan.**

## Phase 1: Research

1. Locate the project root (nearest `livespec.yaml`, §3.1) and read its `mode` (§12).
2. Parse `$ARGUMENTS` for intent. If empty, ask the user what they want to build.
3. Find existing coverage so you propose `[UPDATE]` instead of duplicating:
   - `Grep` the project for key terms from the intent (feature bodies, spec-item text, concept summaries).
   - `Glob features/**/*.md` and scan slugs and areas for overlap.
   - `Read` any close matches in full.
4. Load the context that shapes the decomposition:
   - Personas (`product/persona/*.md`), pain points (`product/pain_point/*.md`), goals (`product/goal/*.md`).
   - Constraints (`product/constraint/*.md`) and principles (`product/principle/*.md`) the work must respect.
   - Entities (`product/entity/*.md`) and external systems (`tech/external_system/*.md`) it touches.

Show the user what you found: existing features that overlap, features that partially cover the intent, and the relevant concepts.

## Phase 2: Propose a plan

Decompose the intent into a flat list of entities to write:

- **[NEW]** a new feature file under `features/{area}/{slug}.md`.
- **[UPDATE]** new REQs / ACs (or an `ISS` for a known defect, §8.2) added to an existing feature.
- **[CONCEPT]** a standing rule, domain object, or convention worth extracting as a concept under `product|ux|tech/` and linking from features. Surface these for review; do not assume them.

### What is a feature vs a concept vs a spec item

Apply the format's own decision framework (§6.5), do not invent heuristics:

- **Ships in a PR with verifiable acceptance criteria, and stays conceptually present after delivery → feature** (§6.5, §7).
- **Specific to one feature's behavior → spec item** inside that feature (a REQ or AC).
- **A standing property multiple features must respect → concept** in `product|ux|tech/` (§6.5). If you state a rule while writing a feature that would clearly apply elsewhere, stop and propose it as a `[CONCEPT]`, then link it (the boundary rule, §6.5).

A migration, upgrade, or refactor is not a feature (§7.4). Its durable target state belongs in an existing feature as evolving REQs, or in a `tech` concept; the act of getting there belongs in a PR or ADR.

### Right-sizing

Use the §7.5 smell tests, not numeric thresholds (v1 defines none):

- **One-sentence test**: the feature's opening paragraph holds without "and also" / "as well as".
- **Single-narrative test**: it fits one §7.4 idiom (user-facing or subsystem), not a mix.
- **Shared-audience test**: its REQs serve the same persona or system.
- **Independent-PR test**: it would not naturally split into PRs whose ACs never touch.

When in doubt, **start coarser and split later** (§7.5): adding REQs is cheap, consolidating grown-apart features is painful.

### Present the plan

```
Proposed decomposition:

1. [NEW] features/habits/create-habit.md : Create a habit with a name and schedule
2. [NEW] features/habits/log-completion.md : One-tap, offline-capable daily check-in
3. [UPDATE] features/habits/view-streaks.md : Add a REQ for backfilling missed days
4. [CONCEPT] product/constraint/offline-first-logging.md : Standing rule, logging must work offline

Links to apply: persona:daily-tracker, constraint:offline-first-logging, feature:{log-completion requires create-habit}
```

Ask the user to approve, add, remove, or reshape. Iterate, re-presenting the updated plan each round, until approved.

### Large intents

If the decomposition yields many features, offer to phase it (a coherent first slice now, the rest later) or to narrow scope. This is a presentation choice for the user, not a stored artifact: nothing about phasing is written into the spec.

## Phase 3: Detail the specs

**Only after the plan is approved.** Draft each feature's full content before writing anything, following `/specify-feature` methodology (summary paragraph, REQs with nested ACs, AS, Q). Present them together for review:

```
### features/habits/log-completion.md  [NEW]

Summary: As a daily tracker, I want to mark a habit done in one tap so my check-in never gets in the way, even offline.

Requirements:
- REQ-1: A user can mark a habit complete for the current day in one action.
  - AC-1.1: Tapping toggles today's completion on; tapping again toggles it off.
  - AC-1.2: The streak count updates immediately.
- REQ-2: A completion logged offline is preserved and reconciled when connectivity returns.
  - ...

Links: persona:daily-tracker, constraint:offline-first-logging, entity:habit, feature:{requires:create-habit}
```

### Resolve open questions immediately

Before presenting specs for approval, surface the real decision points and ask them now with `AskUserQuestion` rather than parking them as `Q` items. For each: offer 2-3 concrete answers (recommended first) plus a **"Leave open"** option. Only "Leave open" answers become `Q` spec items in the file. Batch up to 4 questions per call and fold the answers into the specs.

Present all specs together and iterate until approved.

## Phase 4: Write the files

**Only after the detailed specs are approved.** Features are the work product, so write them directly. Concept changes are product decisions, so propose them as a diff for the user to confirm before writing (mirroring the old suggestion queue).

### Features

For each **[NEW]** feature, `Write` `features/{area}/{slug}.md`:

- Slug is kebab-case ASCII (§9.1), unique within `features/`, and MUST NOT collide with a sibling area name (§7.1).
- Frontmatter `links:` only if there are links; never emit an empty frontmatter block (§5).
- H1 title, then the single summary paragraph (§7.4).
- A `## Requirements` section with `- [ ] REQ-N:` items, each AC nested exactly 2 spaces under its REQ as `- [ ] AC-N.M:` (§8.1). `## Assumptions`, `## Questions` as needed. Omit empty sections (§7.3).
- In `strict` mode, use canonical section names in canonical order (§7.3, §12); in `loose`, canonical names are recommended.

For each **[UPDATE]** feature, `Edit` the existing file: append new REQs/ACs (or `ISS` items) with the **next free integer** in that section. IDs are file-scoped and immutable, gaps are valid, never renumber existing items (§8.3). Preserve unknown frontmatter keys and unrecognized sections (losslessness, §14).

### Concepts

For each **[CONCEPT]**, present the proposed file (path, H1, summary paragraph, body) and ask the user to confirm. On approval, `Write` `{product|ux|tech}/{type}/{slug}.md` where `{type}` is the concept type directory (§6.1). Then add the link from the relevant features' frontmatter (`constraint: [slug]`, `entity: [slug]`, etc., §9.2).

### Links

Apply the links from the approved plan. Only auto-link when the connection is unambiguous; if uncertain, raise it rather than guessing.

## Phase 5: Report and offer next steps

Summarize conversationally what was written: which feature files are new, which got new REQs, which concepts you proposed. The diff is the record; the user reviews it.

Then point at the natural next steps without formalizing them: `/ux-framing` for features with UI implications (new screens, user-facing flows), `/tech-framing` before implementation, then `/implement-feature`. If features have clear UI implications, offer to start UX framing now.

---

For large or multi-feature decomposition that benefits from isolated focus, delegate to the `specifier` subagent. It writes feature files directly, operating only on the local files.
