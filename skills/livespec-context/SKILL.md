---
name: livespec-context
description: |
  Locates the LiveSpec project in the repo, maps its concepts and features from the local
  markdown files, and bridges spec intent against codebase reality during development. Read-only
  orientation. Use at session start, when the user asks "how does X work?", references a feature,
  makes a design or architectural decision, works on UI, or wants product feedback grounded in the
  spec. Not for pure syntax questions, general programming help, or repos with no livespec.yaml.
argument-hint: [path-or-feature-slug]
---

# LiveSpec Context

> **Format reference.** The `§N` citations throughout the LiveSpec skills point to the bundled spec at [`reference/SPEC.md`](../../reference/SPEC.md) (pinned `v1.0.0-draft.2`; condensed: [`reference/CHEATSHEET.md`](../../reference/CHEATSHEET.md)). Read it to resolve anything the skills do not spell out. Since this skill loads first, note that location for the rest of the session.

LiveSpec specs live as plain markdown files in the repository. There is no server and no sync step: you read the files directly. Your job is to locate the project, understand what it says the software should do, and bridge that against what the code actually does.

## Phase 1: Locate the project

A LiveSpec project is the directory containing a `livespec.yaml` manifest (`SPEC.md` §3). Find it before anything else:

1. Search upward from the working directory for the nearest `livespec.yaml`.
2. If none is found upward, search the common locations (`SPEC.md` §3.1): `./livespec.yaml`, `docs/livespec/livespec.yaml`, `.livespec/livespec.yaml`, `specs/livespec.yaml`.
3. A monorepo MAY hold several projects, each `livespec.yaml` is an independent root with its own slug namespace (§3.1). If you find more than one, ask the user which project they mean.
4. If you find none, tell the user there is no LiveSpec project here and offer to scaffold one (a `livespec.yaml` plus the four folders) or to point at an existing one.

Read the manifest. Note `name`, `format_version`, and `mode` (`loose` default, or `strict`, §12). The mode governs how strict later skills are on section names and ordering; carry it forward.

## Phase 2: Map the project

The project root has exactly four meaningful top-level folders (§3): `product/`, `ux/`, `tech/`, `features/`. Everything else (README, code, `node_modules/`) is not LiveSpec and you ignore it.

1. **Concepts.** `Glob` `product/*/*.md`, `ux/*/*.md`, `tech/*/*.md`. The directory name is the concept type slug and the link key (§6.1). The core taxonomy is §6.2: under `product/` you will see `persona`, `pain_point`, `goal`, `principle`, `constraint`, `entity`, `glossary_term`; under `ux/` `ui_component`, `design_principle`, `ux_pattern`; under `tech/` `coding_standard`, `architecture_decision`, `external_system`. Unknown types are valid extensions, not errors (§6.2). For each concept, the opening paragraph after the H1 is its summary (§6.4).
2. **Features.** `Glob` `features/**/*.md`. The slug is the filename; the area is the path between `features/` and the file (§7.1). The opening paragraph is the summary (§7.4). The body carries spec items.
3. **Links.** Read frontmatter `links:` (§9.2), keyed by singular type slug. `feature:` MAY be an untyped list or a typed object with `requires` / `triggers` / `extends` (§7.2). Links are unidirectional in storage but you SHOULD reason about them both ways (§9.3).

Give the user a compact map: project name and mode, concept counts by type, feature list by area, and anything that looks off (a feature whose slug collides with a sibling area is a lint error per §7.1; a link pointing at a missing file is a lint warning per §9.2).

## Phase 3: Read progress from the files

LiveSpec defines no `status` field for features (§10). Do not invent one. Progress is the checkbox state of spec items (§8.1):

- `- [ ]` open / pending, `- [x]` done / closed, `- [-]` cancelled (won't do).
- A `REQ` is implemented when its code exists and its `AC`s pass; you read that from the `[x]` marks, not from any maturity enum.
- A `livespec:` marker in source code (`// livespec: {feature-slug}#{spec-item-id}`, §9.4) anchors a spec item to the code that implements it. `Grep` for `livespec:` to find what is wired up.

When you describe where a body of work stands, describe it as checkbox state plus marker coverage, never as "SPECIFIED" or "IMPLEMENTED".

## The two sources of truth

| | LiveSpec files | Codebase |
|---|---|---|
| **Contain** | Intent: what the software should do and why | Reality: what is actually implemented |
| **Authority on** | Acceptance criteria, personas, constraints | Actual behavior |

Your job is to bridge them: understand intent before building, implement against the spec items, and surface it when reality diverges from intent.

### Answering "how does X work?"

Check both sources and report on both:

1. **In the spec:** find the feature (`Grep`/`Glob` `features/`), read its REQs and ACs.
2. **In the code:** find the implementation (`Grep` for the behavior, or follow `livespec:` markers).
3. **Report on both, and flag gaps:** spec exists but no code (an AC still `[ ]`), code exists with no spec item, or the code does something the spec does not describe.

> **In the spec** (`features/habits/log-completion.md`): REQ-2 says a completion logged offline is preserved and reconciled when connectivity returns, with AC-2.3 requiring two-device reconciliation to keep a single completion per day.
> **In the code** (`src/sync/reconcile.ts`): offline logging and reconciliation exist and carry `livespec: log-completion#REQ-2`. Two-device dedupe (AC-2.3) is not handled: a same-day double log produces two rows. AC-2.3 is still `[ ]`.

### Before implementing

When the user asks you to build something, check whether a feature already covers it (`Grep`/`Glob features/`). If yes, read its ACs, linked constraints, and linked concepts before coding. If no, say so and let the user decide whether to scope it first (`/scope-features`) or build ad hoc.

## Exploring feature relationships

Features do not exist in isolation. When you study one, follow its connections:

- **Typed relations** in `links.feature` (§7.2): `requires` (hard runtime dependency), `triggers` (causes the other to run), `extends` (specialization).
- **Shared concepts**: a `constraint`, `entity`, or `external_system` linked from several features binds them. `constraint: [...]` means the feature must respect that standing rule; `entity: [...]` means it manipulates that domain object; `external_system: [...]` means it integrates with it (§7.2).
- **In-prose `[[type:slug]]`** mentions (§9.5) are reading aids; the frontmatter `links:` is the authoritative relation set.

Answer: where does this feature's responsibility end and a neighbor's begin? Which constraints apply? Does it depend on another feature being built first?

## Grounding product discussions

When the user brainstorms or asks for feedback, ground it in the concept files, not just technical opinion:

- **Personas** (`product/persona/`): who is affected, what they care about.
- **Goals and pain points** (`product/goal/`, `product/pain_point/`): does this serve them?
- **Principles and constraints** (`product/principle/`, `product/constraint/`): what beliefs and standing limits apply.
- **UX and tech concepts** (`ux/`, `tech/`): relevant patterns, decisions, conventions.

## Surfacing gaps

Part of the job is noticing intent and reality drift apart, and saying so rather than silently smoothing it over:

- Spec exists, not implemented: an AC is still `[ ]` and no code matches.
- Implemented, no spec: code with no feature or `livespec:` marker behind it.
- Implementation differs from spec: the AC says one thing, the code does another.
- Spec is stale: a constraint or assumption no longer matches the architecture.

Raise these as observations and, where it is a product decision (a new constraint, a reworded REQ, a new feature), propose the file edit for the user to review as a diff rather than writing it silently. Concept and feature changes are product decisions; surface them.

## What this skill does not do

It reads and reports. It does not write spec files. Hand off to `/scope-features`, `/specify-feature`, `/frame-ux`, `/frame-tech`, `/implement-feature`, or `/sync-spec` for authoring. It also does not reverse-engineer a codebase into a new spec; that is `reverse-livespec`'s job.
