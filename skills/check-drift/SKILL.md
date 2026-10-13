---
name: check-drift
description: |
  Reports where spec intent and codebase reality disagree: spec items marked done with no
  implements: marker anchoring them, markers pointing at features or IDs that no longer exist, code
  anchored to items still open or cancelled, and what carries no code yet. Use when the user asks
  what is actually built, whether the spec matches the code, to check marker coverage, or before a
  review. Read-only diagnostic: fixes belong to /sync-spec (spec side) or /implement-feature (code
  side). Not for internal spec consistency (/check-spec).
argument-hint: "[feature-slug]"
---

# Check Drift

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v0.1.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Two sources of truth: the spec files hold intent, the codebase holds reality (§1). This skill compares them mechanically, using the one bridge the format defines: the code marker `implements: {feature-slug}#{spec-item-id}` and its companion `see-spec:` (§9.4). The legacy `livespec:` verb is read as `implements:`.

The format defines the marker syntax and nothing more. Coverage rules, drift detection, and verification semantics are explicitly left to tooling (§9.4, "Scope of this section"). This skill is that tooling. It does not extend the format, and a project that ignores it stays perfectly conformant.

## Run the script

The diagnostic is deterministic, so a script does it, not a reading pass. It lives at `scripts/check_drift.py` relative to the plugin root; this file is `skills/check-drift/SKILL.md`, so the script sits two levels up in `../../scripts/`. Resolve that to an absolute path from the location of this SKILL.md before running (`${CLAUDE_PLUGIN_ROOT}` does not expand in skill prose). If the path is not obvious, `Glob` for `**/scripts/check_drift.py`.

```bash
python3 <plugin-root>/scripts/check_drift.py [PROJECT_ROOT] [--feature SLUG] [--code-root DIR] [--json]
```

Python 3 stdlib only, no install step. Notes on the arguments:

- **`PROJECT_ROOT`** is optional: the script locates the manifest (`product-spec.yaml` or `livespec.yaml`) itself, honoring the §3.1 patterns. If it reports several projects (monorepo), ask the user which one, or pass the one the current work belongs to. Never assume a fixed path.
- **`--code-root`** defaults to the git repo root. Pass it when the spec lives in a repo separate from the application, otherwise the scan finds no markers and every item looks unanchored.
- **`--feature SLUG`** narrows the report to one feature. Use it when the user is working on a single feature; run the full sweep otherwise.
- **`--json`** gives you the findings as data. Prefer it when you intend to group, rank, or cross-reference; the plain output is for showing the user directly.

The script exits 0 even when it finds things. It is a diagnostic, not a quality gate.

## What each check means

| Check | Severity | Reading |
|---|---|---|
| `marker-unknown-feature` | error | The code points at a feature slug with no file. Almost always a renamed or deleted feature file; the marker is now dangling. |
| `marker-unknown-id` | error | The feature exists, the ID does not. Someone deleted a spec item instead of cancelling it with `[-]` (§8.3), or mistyped the ID. |
| `marker-on-cancelled` | warning | Code is anchored to an item marked `[-]`. Either the item was cancelled but the code stayed, or the cancellation was wrong. On an `AS`, the assumption was invalidated: the code that relies on it needs a second look. |
| `marker-on-open` | warning | An `implements:` marker on a `REQ`, `AC`, `UX` or `TECH` still `[ ]`. Usually the spec was not checked off after the work landed. |
| `marker-on-closed` | info | Code points at a `Q` now answered or a `LIM` now lifted. The code was written around the open state and may keep a workaround or a guess that no longer holds. |
| `marker-legacy-verb` | info | Markers written with the legacy `livespec:` verb, one finding per file with a count. They still resolve (as `implements:`); the fix is a rewrite to `implements:`, or `see-spec:` for AS, Q, LIM. |
| `marker-verb-fit` | info | Markers whose verb does not fit the item type (`implements:` on an AS, `see-spec:` on a REQ), one finding per file. They resolve anyway (§9.4); only `implements:` counts toward coverage, so a `see-spec:` on a REQ leaves it unanchored. |
| `done-unmarked` | warning | An item is `[x]` but nothing in the code is anchored to it. Either the marker was never placed, or the item was checked off optimistically. |
| `open-unmarked` | info | An item is `[ ]` with no code behind it. Consistent, and the normal state of unbuilt work. Inventory, not a defect. |
| `feature-unmarked` | info | No marker anywhere for that feature. Expected before implementation starts; notable once items are `[x]`. |

Coverage follows §9.4 and counts `implements:` markers only (and legacy `livespec:` ones): a marker on a REQ implicitly covers its nested ACs, so an AC counts as anchored when its parent REQ carries a marker. A REQ counts as anchored when every one of its non-cancelled ACs is. `UX` and `TECH` directions are resolved and checked when a marker points at them (`marker-on-open`, `marker-on-cancelled`), but they are not coverage targets: a direction with no marker is not reported, since many have no single code site.

## Report it as a divergence, not as a backlog

The script produces facts. Your job is to say what they mean, and the framing matters: the format describes the software, not the work on it (§1). Report **where intent and reality disagree**, never as a prioritized to-do list, a completion percentage, or a delivery forecast. Sequencing lives in git and in the user's issue tracker.

Lead with what is genuinely wrong (the errors and warnings: dangling markers, unanchored `[x]` items), and keep the `open-unmarked` inventory short unless the user asked for it. On a large sweep, group by feature and give counts rather than listing every open item.

> `log-completion`: AC-2.1 and AC-2.2 are `[x]` but nothing anchors them; `src/sync/queue.ts` looks like the implementation and carries no marker. Two markers in `src/sync/reconcile.ts` point at `log-completion#REQ-4`, an ID that no longer exists in the feature file: it was deleted rather than cancelled `[-]` (§8.3), so those anchors are dangling.

Do not treat every finding as a defect to fix. A `done-unmarked` item on code written before the spec existed is a marker to add, not a bug. Say which reading you are applying.

## Then hand off

This skill reports and stops. It writes nothing, neither spec files nor code.

- Spec is behind reality (items to check off, resolution notes, new REQs or LIM discovered): `/sync-spec`.
- Code is behind the spec (items still open, markers to place): `/implement-feature`.
- Dangling markers: the fix is a judgment call. A renamed feature means the marker needs updating; a deleted spec item means the item should have been `[-]` cancelled and probably needs restoring, since IDs are immutable (§8.3). Propose it, let the user decide.

## What this skill does not do

It does not check the specs against each other (feature without REQ, broken links, duplicate IDs): that is `/check-spec`. It does not validate conformance to the format (Level-3, §14); that validator is constitutive of the format and belongs in the format's own repository. It does not judge whether the implementation is *correct*, only whether it is *anchored*: verifying that code actually satisfies an AC is the `qa` agent's job.
