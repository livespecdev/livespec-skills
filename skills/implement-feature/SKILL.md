---
name: implement-feature
description: |
  Implements a spec feature by working through its acceptance criteria, writing code, placing
  code markers (implements: / see-spec:) that anchor the code to spec items, and checking ACs [x] as they pass. Runs UX and
  tech framing first if the feature lacks a ## UX or ## Tech section. Use when the user says "implement
  this", "code this", "start building", or names a feature slug. Not for specification (/specify-feature),
  scoping (/scope-features), or framing only (/frame-ux, /frame-tech).
argument-hint: <feature-slug>
---

# Implement Feature

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Work through a feature's acceptance criteria, write the code, and anchor it to the spec with `implements:` / `see-spec:` markers (`SPEC.md` §9.4). The format has no feature `status` (§10): progress is the checkbox state of spec items (§8.1). You check ACs `[x]` as they pass; you never flip a status.

**Do not start coding until framing is complete.**

## Mode detection

- **If `$ARGUMENTS` names a feature** (`features/**/{slug}.md` exists) → Single-feature mode.
- **If no argument** → Picker mode.

If the slug matches nothing, say so and run Picker mode.

## Picker mode

1. Locate the project root (nearest manifest, `product-spec.yaml` or `livespec.yaml`, §3.1).
2. `Glob features/**/*.md` and read each feature's spec-item state.
3. Present, via `AskUserQuestion`, the features that are framed (have `## UX` where user-facing, and `## Tech`) and still have open (`- [ ]`) ACs, with their progress (e.g. "log-completion (3/8 ACs done)").
4. If nothing is ready, say so and point at `/scope-features` or `/specify-feature`.
5. Route the selection into Single-feature mode.

## Single-feature mode

### Step 1: Read the feature and its context

`Read` `features/**/{slug}.md`. Pull in what shapes the work: linked personas, the constraints it must respect (`product/constraint/`), entities it manipulates (`product/entity/`), external systems (`tech/external_system/`), and any concepts referenced from `## UX` / `## Tech`. Read the manifest `mode` (§12).

### Step 2: Check readiness

**Spec completeness**: the feature has a summary and at least one REQ with ACs, and its `## Questions` hold no blocker still open (`- [ ] Q-...`). If a blocking question is unresolved, surface it and resolve it (or defer explicitly) before coding.

**UX framing**: if the feature is user-facing and has no `## UX` section, run `/frame-ux` for it and wait for completion. If the skill is unavailable, tell the user and ask whether to proceed without it.

**Tech framing**: if the feature has no `## Tech` section, run `/frame-tech` for it and wait. If unavailable, tell the user and ask whether to proceed without it.

### Step 3: Implement

Only once framing is in place:

1. Create a working task list from the acceptance criteria (`TaskCreate`), one item per AC.
2. Briefly state what you are about to build: the feature, who it serves, the UX and tech approach in one line each, and the AC count.
3. Write the code, AC by AC, following the `UX` and `TECH` directions and respecting linked constraints. A direction you cannot follow is a divergence: surface it (see below), do not silently implement something else.
4. **Place code markers** (§9.4). At each code site that implements a spec item, add a comment in the host language's native syntax carrying `implements: {feature-slug}#{spec-item-id}`:
   - `// implements: log-completion#REQ-2` (JS/TS), `# implements: log-completion#AC-2.1` (Python), `<!-- implements: log-completion#REQ-1 -->` (HTML).
   - Pick the verb from the item type. `implements:` for what the code realizes: `REQ`, `AC`, `UX`, `TECH`. `see-spec:` for what the code depends on without realizing it: an `AS` it relies on (`// see-spec: log-completion#AS-1` above the code that assumes one completion per day), a `LIM` it works around, a `Q` it awaits. Readers accept either verb on any item, but only `implements:` counts toward coverage, so the right verb keeps `/check-drift` accurate.
   - Never write the legacy `livespec:` verb. When you edit a line that carries one, rewrite it with the fitting verb.
   - The payload is the verb, `:`, one or more spaces, then `{slug}#{id}`, no internal whitespace, case-sensitive (§9.4). The slug is the feature slug only; the area is never part of the marker, so markers survive a feature being moved between areas (§9.4).
   - When one code site serves several items **of the same feature**, list their IDs in one marker, comma-separated, no whitespace: `// implements: log-completion#REQ-2,REQ-3,AC-2.1` (§9.4). This avoids repeating the slug; it is equivalent to one marker per ID. Items in different features still take one marker each.
   - A marker on a `REQ` implicitly covers its nested ACs unless a more specific AC-level marker exists (the coverage rule /check-drift applies; §9.4 leaves coverage to tools). Mark at the REQ level for a cohesive implementation, at the AC level when criteria land in different places.
   - A `UX` or `TECH` direction MAY carry a marker where one code site embodies it (`// implements: log-completion#TECH-3` on the upsert handler, §9.4). Skip it when the direction is diffuse (a layout, a label): an unmarked direction is not a gap.
5. **Check ACs as they pass.** When a criterion is implemented and verified, `Edit` the feature to flip that AC `- [ ]` → `- [x]` (§8.1). Mark a REQ `[x]` when its ACs are satisfied; a REQ `[x]` with open ACs is allowed but is a lint warning, so only do it deliberately (§8.2). Flip a `UX` or `TECH` direction to `[x]` once the code applies it. Never renumber or reuse IDs (§8.3); to drop a criterion that turned out wrong, mark it `[-]` with a reason rather than deleting it.
6. Keep edits to the feature file tight: change only the checkboxes (and, where useful, add a resolution note, see below). Preserve the rest of the file (losslessness, §14).

### Step 4: Record what the code answered (optional)

When closing a `Q` the implementation answered, or a `LIM` it lifted, you MAY add a resolution note: a single continuation line starting with `→ ` at the item's indentation (§8.1). On REQ/AC the code itself is the answer via the marker, so a note there is optional commentary.

```markdown
- [x] LIM-2: On a flaky connection, completions logged during a dropout are lost.
  → Lifted by retrying the sync drain with backoff in `src/sync/worker.ts`.
```

## When implementation diverges from the spec

If the code needs to behave differently from an AC, do not silently overwrite intent. Surface it: either the AC body should evolve (bodies are mutable, IDs are not, §8.3) or a new REQ/AC (or a `LIM`, if the gap is accepted for now) captures the reality. The same goes for a direction: a different approach is a new `UX`/`TECH` item superseding the old one, proposed to the user, not a silent edit. Edit the AC body for a clarification; add a new item for genuinely new behavior. Flag product-level changes for the user rather than deciding them.

## Wrap up

Summarize conversationally: the feature, how many ACs are now `[x]`, and which (if any) remain open and why. The diff (code plus the checked spec items plus the code markers) is the record. Then point at `/finalize-feature` (tests, quality gate, commit) and `/sync-spec` (reconcile the spec with what was built). There is no status to set.

---

To check whether the implementation actually meets the spec before finalizing, delegate to the `qa` subagent: it verifies each AC against the code and reports gaps, without changing the spec or the code.
