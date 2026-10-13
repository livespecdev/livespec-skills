---
name: check-spec
description: |
  Reports internal inconsistencies across a spec project: features with no requirements,
  duplicate or misnumbered IDs, ACs not nested under a REQ, REQs checked off with open ACs, broken
  frontmatter links and in-prose references, orphan concepts, and open questions or issues. Use when
  the user asks about spec quality, wants a health pass over the specs, or before a spec review.
  Read-only diagnostic. Not for spec-to-code coherence (/check-drift) or authoring (/specify-feature).
argument-hint: "[feature-slug]"
---

# Check Spec

> **Format reference.** The `§N` citations point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v0.1.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything this skill does not spell out.

Do the specs hold together? This skill reads the spec files and only those: no codebase involved. It answers whether the documents are coherent among themselves, well formed, and fully linked.

**This is not the deferred format validator.** Level-3 conformance (§14) asks whether a file is a valid document under the format; that validator is constitutive of the format and belongs in the format's own repository. This skill is an editorial diagnostic: it flags things that are conformant but probably not what the author meant, alongside a few outright format errors. Everything it reports carries a `§N` citation so you can always show the user what rule is behind a finding.

## Run the script

The diagnostic is deterministic, so a script does it, not a reading pass. It lives at `scripts/check_spec.py` relative to the plugin root; this file is `skills/check-spec/SKILL.md`, so the script sits two levels up in `../../scripts/`. Resolve that to an absolute path from the location of this SKILL.md before running (`${CLAUDE_PLUGIN_ROOT}` does not expand in skill prose). If the path is not obvious, `Glob` for `**/scripts/check_spec.py`.

```bash
python3 <plugin-root>/scripts/check_spec.py [PROJECT_ROOT] [--feature SLUG] [--only CHECKS] [--skip CHECKS] [--json]
```

Python 3 stdlib only, no install step. Notes on the arguments:

- **`PROJECT_ROOT`** is optional: the script locates the manifest (`product-spec.yaml` or `livespec.yaml`) itself, honoring the §3.1 patterns. If it reports several projects (monorepo), ask the user which one. Never assume a fixed path.
- **`--feature SLUG`** narrows to one feature and skips the project-wide checks (orphan concepts, cross-file references).
- **`--only` / `--skip`** take comma-separated check names; `--list-checks` prints them. Reach for `--only` when the user asks a targeted question ("which features have no requirements?") instead of filtering a full report by hand.
- **`--json`** gives you the findings as data. Prefer it when you intend to group, rank, or cross-reference.

The script exits 0 even when it finds things. It is a diagnostic, not a quality gate.

## What each check means

**Structure of spec items (§8)**

| Check | Severity | Reading |
|---|---|---|
| `duplicate-id` | error | The same ID twice in one section. IDs are file-scoped and immutable (§8.3); inbound references become ambiguous. Fix by extending the sequence, never by renumbering. |
| `ac-orphan` | error | An AC with no parent REQ above it. An AC's parent is determined structurally by nesting (§8.2). |
| `ac-nesting` | error | An AC nested more than 2 spaces deep. Sub-trees under an AC are invalid (§8.1); decompose into several REQs. |
| `item-nesting` | error | A non-AC item (REQ, AS, Q, LIM, UX, TECH) indented under another item. Only ACs nest, one level under their REQ (§8.1). |
| `ac-id-mismatch` | warning | `AC-3.1` sitting under `REQ-2`. The AC number should mirror its parent's index (§8.3). Renumbering breaks references, so weigh the fix. |
| `malformed-item` | warning | A checkbox line in a spec section that does not parse as a spec item: missing type prefix, missing ID, or missing `:`. |
| `unknown-item-type` | warning | Items using a type outside the seven defined in §8.2 (REQ, AC, AS, Q, LIM, UX, TECH), most often `TE-` (now `TECH`) or `ISS-` (now `LIM`) from projects that predate those types. Reported once per file and per type, with a count. |
| `resolution-note` | error/warning | More than one `→ ` note on an item (error), or a note on an item still open (warning). See §8.1. |
| `req-done-open-ac` | warning | A REQ `[x]` with ACs still `[ ]`. Permitted, and worth surfacing (§8.2). Cancelled `[-]` ACs do not count. |
| `req-open-all-ac-done` | info | Every AC is `[x]` but the REQ is not. Usually just an unchecked box. |

**Completeness**

| Check | Severity | Reading |
|---|---|---|
| `feature-no-requirements` | warning | The feature states intent but nothing testable. Either it needs specifying (`/specify-feature`), or it is really a concept (§6.5). |
| `feature-no-summary` | warning | No summary paragraph between the H1 and the first section (§7.4). |
| `missing-title` | warning | No H1. |
| `empty-frontmatter` | warning | An empty `---` block; omit it entirely (§5). |
| `invalid-slug` | warning | Filename is not kebab-case ASCII (§9.1). |
| `concept-placement` | error | A concept sitting directly under `product/`, `ux/`, or `tech/` instead of in a `{type}/` subdirectory (§6.1). It cannot be linked at all. |
| `duplicate-manifest` | error | The project root holds both `product-spec.yaml` and `livespec.yaml` (§4). The two names are equivalent and only one is allowed; the script reads `livespec.yaml`. Ask the user which to keep. |

**Links (§9)**

| Check | Severity | Reading |
|---|---|---|
| `broken-link` | warning | A `links:` entry resolving to no file (§9.2). Usually a renamed or not-yet-written concept. |
| `unknown-link-type` | warning | A `links:` key that is neither a core type (§6.2) nor a directory present in the project. Likely a typo or a plural (`personas` for `persona`); type slugs are always singular. |
| `broken-item-ref` | warning | `[REQ-9]` or `[other-feature#REQ-3]` in a body pointing at an ID that does not exist (§8.1). |
| `broken-prose-ref` | warning | A `[[type:slug]]` or `[[slug]]` resolving to nothing (§9.5). |
| `ambiguous-prose-ref` | warning | A bare `[[slug]]` matching several entities. Disambiguate with the typed form (§9.5). |
| `orphan-concept` | info | A concept no feature and no concept references. Not a defect: it may be context that stands on its own. Worth a look if the project has many. |

**Open items**

`open-question` and `open-limitation` list every `[ ]` Q and LIM. They are an inventory, not findings. Surface them when the user wants to know what is unresolved.

## Interpret, do not dump

The script produces facts. Your job is to say which ones matter, and the framing matters: the format describes the software, not the work on it (§1). Report coherence problems, never a to-do list, a maturity score, or a readiness assessment.

Lead with errors, group warnings by kind, and give counts instead of exhaustive lists once a category runs long. A finding is a question to the author, not a verdict:

> Three features under `features/billing/` have no REQ. Two of them (`invoice-numbering`, `dunning-policy`) read like standing rules that several features must respect, so they may belong in `product/constraint/` rather than in `features/` (§6.5). The third, `refund-request`, looks like a real feature that was scoped but never specified.

Three categories deserve caution before you propose a fix:

- **`unknown-item-type`**: `TE-` items usually mean the project adopted tech directions before §8.2 defined them as `TECH`. Renaming `TE-N` to `TECH-N` keeps the numbers but breaks every inbound `[TE-N]` reference and code marker marker, so propose it as one migration covering the feature file, its in-prose references, and the code markers, and let the user decide. Do not convert them to REQs on your own: that changes the meaning of the spec. `ISS-` items need a read before any rename: those that describe a gap the software still has become `LIM-N`, stated in the present tense; those that record a fixed bug or a task were work tracking (§8.2) and are candidates for removal, which the user decides after checking that no marker or reference points at them.

- **`ac-id-mismatch`**: renumbering breaks inbound references, and IDs are immutable (§8.3). Often the honest fix is to leave the ID alone and live with the cosmetic mismatch.
- **`orphan-concept`**: absence of links is not a defect. §9.5 is explicit that a missing reference must not be treated as one.

## Then hand off

This skill reports and stops. It writes nothing.

- Missing requirements, malformed items, weak ACs: `/specify-feature`.
- Features that should be concepts, or an intent covering several features: `/scope-features`.
- Broken links to concepts worth writing: propose the concept file and let the user review the diff. Edits to `product/`, `ux/`, and `tech/` are product decisions.

In `strict` mode (§12.2) the manifest enforces section names, order, and placement. This script does not check those; say so rather than implying the project is clean. Warn on strict violations you notice while reading, do not silently rewrite.

## What this skill does not do

It never reads the codebase: spec-to-code coherence, marker coverage, and dangling code markers are `/check-drift`. It does not validate conformance to the format (§14). It does not judge whether a requirement is *good*, only whether the documents are consistent: editorial quality is `/specify-feature` and the `specifier` agent.
