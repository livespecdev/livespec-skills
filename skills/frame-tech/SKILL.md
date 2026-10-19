---
name: frame-tech
description: |
  Frames the technical approach for a spec feature and records it in the feature's `## Tech`
  section: architecture, data model, API shape, key decisions, constraints applied, testing strategy.
  Explores the codebase and reads tech/ concepts. Use when framing the technical approach before
  implementation. Not for the core spec (/specify-feature) or UX (/frame-ux).
argument-hint: [feature-slug]
---

# Tech Framing

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Frame the technical approach for a feature and write it into the feature's `## Tech` section (`SPEC.md` §7.3). Each durable technical decision is a `TECH` spec item (§8.2): a checkbox line `- [ ] TECH-N: ...`, written declaratively as target state. Free-form prose under `## Tech` carries what items cannot: the rationale, diagrams, the testing strategy.

## Identify the feature

If `$ARGUMENTS` names a feature, `Read` `features/**/{slug}.md`. Otherwise `Glob features/**/*.md` and ask. Locate the project root (nearest manifest, `product-spec.yaml` or `livespec.yaml`, §3.1) and read its `mode` (§12).

## Check prerequisites

If the feature has no `## UX` section and is user-facing, warn that tech framing without UX may cause rework, and offer to run `/frame-ux` first. The user may choose to proceed anyway.

## Gather context

1. **The feature**: summary, REQs, ACs, assumptions, and the `## UX` section if present.
2. **Tech concepts** under `tech/` (§6.2): `coding_standard`, `architecture_decision`, `external_system`, plus any `*_convention` extension types (§6.2). These are standing rules the approach must respect; apply and link them rather than restating them.
3. **Constraints** (`product/constraint/*.md`) and **entities** (`product/entity/*.md`) linked from the feature.
4. **The codebase**: where will this live, what does it touch, are there similar implementations to follow? Use `Grep`/`Glob`/`Read` to ground the approach in what actually exists.

## Analyze and propose

### Step 1: Quick direction check

Present the high-level approach briefly: the architecture overview (where it fits, main components), the key patterns you will follow, and any obvious constraint or risk. Use `AskUserQuestion` to confirm before detailed work, folding clarifying questions in.

### Step 2: Gap analysis (internal checklist)

- **Data model**: new entities/fields/types, relationships, migrations.
- **API design**: endpoints, request/response shapes, auth, error responses.
- **Business logic**: where core logic lives, validation, authorization, state transitions.
- **Integration points**: existing services, events/webhooks, external systems, background jobs.
- **Security**: auth/authz model, input validation, data exposure, rate limiting.
- **Error handling**: failure modes, recovery, rollback for partial operations.
- **Performance**: expected scale, bottlenecks, caching.
- **Testing**: unit coverage, integration tests, edge cases.

### Step 3: Synthesize

Pull it into a coherent plan: architecture overview, main components/modules/layers affected (not individual source files), data model changes, API shape, key decisions, testing strategy. Surface decisions that need user input with `AskUserQuestion` (batch up to 4, recommended option first, "Leave open" available). Prioritize decisions that affect the data model (hard to change later), have security implications, or impact other features.

## Review before writing

Present the full proposed `## Tech` section (the `TECH` items, then the supporting prose) and any concepts you intend to propose. Use `AskUserQuestion` to confirm: approve, adjust, or rethink. Iterate until approved.

## Write the `## Tech` section

**Describe target state, not work to do** (§1, §7). The spec should still read correctly six months after implementation, as a description of what the feature is, not a stale to-do list.

- "Completions are stored locally in an append-only log and reconciled server-side by `(habit_id, day)`."
- "Input validation happens server-side in the API route handler."
- Avoid: "Extract the sync logic into a new module", "Add a `synced_at` column" (imperative, work-shaped).

`Edit` the feature to add or update `## Tech` (§7.3). In `strict` mode it comes last in canonical order (§7.3, §12); in `loose` it MAY sit anywhere. Preserve the rest of the file (losslessness, §14); do not touch REQ/AC IDs.

```markdown
## Tech

- [ ] TECH-1: Completions live in an append-only local log keyed by `(habit_id, day)`, the source of truth while offline.
- [ ] TECH-2: A sync worker drains the log to the server when connectivity returns, idempotent per `(habit_id, day)`.
- [ ] TECH-3: `PUT /habits/{id}/completions/{day}` is an idempotent upsert: repeated calls for the same day converge to one completion.
- [ ] TECH-4: Streaks are derived from the log on read, never stored as an independent value.

The log keeps logging fully offline-capable (respects [offline-first logging](../../product/constraint/offline-first-logging.md)). The idempotent upsert makes reconciliation order-independent, which is how two devices logging the same day end with a single completion ([AC-2.3]). Derived streaks cannot drift out of sync with the log.

### Testing strategy

- Unit: streak derivation across gaps, backfill within the 7-day window ([REQ-3]).
- Integration: offline log then reconcile; same-day double log on two devices yields one completion.

### Out of scope

- Multiple completions per day ([AS-1]): single boolean per day in v1.
```

**What becomes an item.** Each choice the implementation must follow is a `TECH` item: a module boundary, a data shape, an API contract, a storage location, a library, an integration path. Apply the substitution test (§6.5, *Requirement vs. direction*): if another implementation could satisfy every REQ and AC while contradicting the statement, it is a direction and belongs here. If contradicting it would make an observable behavior wrong (a latency budget, an error the user sees), it is an AC: note it for `/specify-feature` instead.

**Items and IDs.** One decision per item, top-level only (no nested children, §8.1), no block constructs in the body: a schema or a snippet goes in the prose, and the item names it. Extend the existing `TECH-N` sequence; never renumber (§8.3). New items start `[ ]`: they turn `[x]` when the implementation applies them (`/implement-feature`, `/sync-spec`). To change an existing direction, do not rewrite it: mark it `[-]` with a resolution note (`→ Superseded by [TECH-5]: ...`) and add the new direction as a new item (§8.1).

**What stays prose.** The rationale that ties the items together, the constraints they satisfy, diagrams, the testing strategy, what is out of scope. Prose explains the items; it does not carry decisions of its own.

## Propose new concepts, do not impose

If framing established something reusable, that is a concept, not a feature note (§6.5):

- A standing architectural choice → `architecture_decision` under `tech/`.
- A cross-cutting engineering rule → a `*_convention` type (e.g. `api_convention`, `testing_convention`, §6.2), using the recommended namespace so projects interoperate.
- A coding rule → `coding_standard`.
- A newly integrated third-party service → `external_system` under `tech/`.

Propose the file under `tech/{type}/{slug}.md` and let the user confirm via the diff before writing. Then link it from the feature (`architecture_decision: [slug]`, `external_system: [slug]`, §9.2). Distinguish three things (§6.5): a feature-specific behavior is a REQ or AC, owned by `/specify-feature`; a feature-specific implementation choice is a `TECH` item; a rule that applies elsewhere is a concept, linked from the feature. A `TECH` item MAY still say how this feature applies a concept, when that involves a choice of its own.

## Wrap up

Summarize the key decisions, the main components affected, and any risks or deferred items. Then offer one next step: if `## UX` is missing and the feature is user-facing, offer `/frame-ux`; otherwise the feature is framed, so offer to start `/implement-feature`. There is no status to flip (§10).

---

For large architectural changes, multiple integration points, or heavy codebase exploration, delegate to the `tech-framer` subagent, which writes the `## Tech` section directly, operating only on the local files.
