---
name: spec-context
description: |
  Locates the spec project in the repo, maps its concepts and features from the local
  markdown files, and bridges spec intent against codebase reality during development. Read-only
  orientation. Use at session start, when the user asks "how does X work?" or what the spec says
  about something, or wants product feedback grounded in the spec. Authoring and framing have their
  own skills. Not for pure syntax questions, general programming help, or repos with no spec manifest.
argument-hint: "[path or feature-slug]"
---

# Spec Context

> **Format reference.** The `§N` citations throughout these skills point to the bundled format spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything the skills do not spell out. Since this skill loads first, note that location for the rest of the session.

Specs live as plain markdown files in the repository. There is no server and no sync step: you read the files directly. Your job is to locate the project, understand what it says the software should do, and bridge that against what the code actually does.

## Phase 1: Locate the project

A spec project is the directory containing a manifest, `product-spec.yaml` or `livespec.yaml` (`SPEC.md` §3, §4). Find it before anything else:

1. Search upward from the working directory for the nearest manifest, `product-spec.yaml` or `livespec.yaml`.
2. If none is found upward, search the common locations (`SPEC.md` §3.1), each with either manifest name: `./`, `docs/spec/`, `.spec/`, `specs/`, and the older `docs/livespec/`, `.livespec/`.
3. A monorepo MAY hold several projects, each manifest is an independent root with its own slug namespace (§3.1). If you find more than one, ask the user which project they mean.
4. If you find none, tell the user there is no spec project here and ask whether one exists elsewhere. This skill writes nothing, so it does not create one.

Read the manifest. Note `name`, `format_version`, and `mode` (`loose` default, or `strict`, §12). The mode governs how strict later skills are on section names and ordering; carry it forward.

## Phase 2: Map the project

The project root has exactly four meaningful top-level folders (§3): `product/`, `ux/`, `tech/`, `features/`. Everything else (README, code, `node_modules/`) is not part of the spec and you ignore it.

1. **Concepts.** `Glob` `product/*/*.md`, `ux/*/*.md`, `tech/*/*.md`. The directory name is the concept type slug and the link key (§6.1). The core taxonomy is §6.2: under `product/` you will see `persona`, `pain_point`, `goal`, `principle`, `constraint`, `entity`, `glossary_term`; under `ux/` `ui_component`, `design_principle`, `ux_pattern`, `screen`; under `tech/` `coding_standard`, `architecture_decision`, `external_system`. Unknown types are valid extensions, not errors (§6.2). For each concept, the opening paragraph after the H1 is its summary (§6.4).
2. **Features.** `Glob` `features/**/*.md`. The slug is the filename; the area is the path between `features/` and the file (§7.1). The opening paragraph is the summary (§7.4). The body carries spec items.
3. **Links.** Read frontmatter `links:` (§9.2), keyed by singular type slug. `feature:` MAY be an untyped list or a typed object with `requires` / `triggers` / `extends` (§7.2). Links are unidirectional in storage but you SHOULD reason about them both ways (§9.3).

Give the user a compact map: project name and mode, concept counts by type, feature list by area, and anything that looks off (a feature whose slug collides with a sibling area is a lint error per §7.1; a link pointing at a missing file is a lint warning per §9.2).

## Phase 3: Read progress from the files

The format defines no `status` field for features (§10). Do not invent one. Progress is the checkbox state of spec items (§8.1):

- `- [ ]` open / pending, `- [x]` done / closed, `- [-]` cancelled (won't do).
- A `REQ` is implemented when its code exists and its `AC`s pass; you read that from the `[x]` marks, not from any maturity enum.
- A code marker (§9.4) anchors a spec item to the code: `// implements: {feature-slug}#{spec-item-id}` where the code realizes it, `// see-spec: ...` where the code depends on it (an assumption, a limitation, an open question). Older code may carry the legacy `livespec:` verb, read as `implements:`. `Grep` for `implements:|see-spec:|livespec:` to find what is wired up.

When you describe where a body of work stands, describe it as checkbox state plus marker coverage, never as "SPECIFIED" or "IMPLEMENTED".

## The two sources of truth

| | Spec files | Codebase |
|---|---|---|
| **Contain** | Intent: what the software should do and why | Reality: what is actually implemented |
| **Authority on** | Acceptance criteria, personas, constraints | Actual behavior |

Your job is to bridge them: understand intent before building, implement against the spec items, and surface it when reality diverges from intent.

### Answering "how does X work?"

Check both sources and report on both:

1. **In the spec:** find the feature (`Grep`/`Glob` `features/`), read its REQs and ACs.
2. **In the code:** find the implementation (`Grep` for the behavior, or follow `implements:` markers).
3. **Report on both, and flag gaps:** spec exists but no code (an AC still `[ ]`), code exists with no spec item, or the code does something the spec does not describe.

> **In the spec** (`features/habits/log-completion.md`): REQ-2 says a completion logged offline is preserved and reconciled when connectivity returns, with AC-2.3 requiring two-device reconciliation to keep a single completion per day.
> **In the code** (`src/sync/reconcile.ts`): offline logging and reconciliation exist and carry `implements: log-completion#REQ-2`. Two-device dedupe (AC-2.3) is not handled: a same-day double log produces two rows. AC-2.3 is still `[ ]`.

### Before implementing

When the user asks you to build something, check whether a feature already covers it (`Grep`/`Glob features/`). If yes, read its ACs, linked constraints, and linked concepts before coding. If no, say so and let the user decide whether to scope it first (`/scope`) or build ad hoc.

## Exploring feature relationships

Features do not exist in isolation. When you study one, follow its connections:

- **Typed relations** in `links.feature` (§7.2): `requires` (hard runtime dependency), `triggers` (causes the other to run), `extends` (specialization).
- **Shared concepts**: a `constraint`, `entity`, or `external_system` linked from several features binds them. `constraint: [...]` means the feature must respect that standing rule; `entity: [...]` means it manipulates that domain object; `external_system: [...]` means it integrates with it (§7.2).
- **In-prose references** (§9.5), relative Markdown links to a spec file or `[[type:slug]]`, are reading aids; the frontmatter `links:` is the authoritative relation set.

Answer: where does this feature's responsibility end and a neighbor's begin? Which constraints apply? Does it depend on another feature being built first?

## Grounding product discussions

When the user brainstorms or asks for feedback, ground it in the concept files, not just technical opinion:

- **Personas** (`product/persona/`): who is affected, what they care about.
- **Goals and pain points** (`product/goal/`, `product/pain_point/`): does this serve them?
- **Principles and constraints** (`product/principle/`, `product/constraint/`): what beliefs and standing limits apply.
- **UX and tech concepts** (`ux/`, `tech/`): relevant patterns, decisions, conventions, including any extension types the project defines beyond the core taxonomy (§6.2). A project-specific type often carries the axis that matters most for the question at hand, so name it when it applies rather than falling back on the core types alone.

## Surfacing gaps

Part of the job is noticing intent and reality drift apart, and saying so rather than silently smoothing it over:

- Spec exists, not implemented: an AC is still `[ ]` and no code matches.
- Implemented, no spec: code with no feature or code marker behind it.
- Implementation differs from spec: the AC says one thing, the code does another.
- Spec is stale: a constraint or assumption no longer matches the architecture.

Raise these as observations and, where it is a product decision (a new constraint, a reworded REQ, a new feature), propose the file edit for the user to review as a diff rather than writing it silently. Concept and feature changes are product decisions; surface them.

This is the narrative version, scoped to whatever you are currently looking at. For an exhaustive sweep of the whole project, hand off rather than reading every file: `/check-drift` for intent against code (unanchored `[x]` items, dangling code markers), `/check-spec` for the specs against each other (features with no REQ, broken links, duplicate IDs). Both are read-only and script-backed.

## What this skill does not do

It reads and reports. It does not write spec files. Hand off to `/scope`, `/specify`, `/frame-ux`, `/frame-tech`, `/implement`, or `/sync` for authoring. It also does not reverse-engineer a codebase into a new spec; that is `reverse-livespec`'s job.
