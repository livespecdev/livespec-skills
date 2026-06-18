# LiveSpec: Format Specification

**Version:** `v1.0.0-draft`
**Status:** Draft (open for comments)
**Canonical home:** https://livespec.dev

> LiveSpec is a file format for product specifications that stay current with the code they describe. It is designed to be readable by humans, parseable by tools, and consumable by AI coding agents, without lock-in to any specific application.

---

## Table of Contents

1. [Philosophy](#1-philosophy)
2. [Conventions & Conformance Language](#2-conventions--conformance-language)
3. [Repository Layout](#3-repository-layout)
4. [The Project Manifest](#4-the-project-manifest-livespecyaml)
5. [Entities](#5-entities)
6. [Concepts](#6-concepts)
7. [Features](#7-features)
8. [Spec Items](#8-spec-items)
9. [Linking System](#9-linking-system)
10. [Status Lifecycle](#10-status-lifecycle)
11. [Assets](#11-assets)
12. [Modes](#12-modes)
13. [Format Versioning](#13-format-versioning)
14. [Conformance Levels](#14-conformance-levels)
15. [Open Questions](#15-open-questions-rfc-candidates)

---

## 1. Philosophy

LiveSpec exists to solve a single problem: **product specifications drift away from reality the moment they are written.** Traditional spec formats (Word docs, Jira tickets, Notion pages) assume specs are written once and discarded. LiveSpec assumes specs are *continuously maintained alongside code*, by humans and AI agents working together.

The format optimizes for:

- **Human readability**: plain markdown, no proprietary editor required
- **Machine parseability**: strict, validated frontmatter; conventional body sections
- **Agent consumption**: structured enough for LLMs to reason about, compact enough to keep token budgets sane
- **Git-native workflow**: files, folders, diffs, pull requests
- **Tool independence**: any LiveSpec-conformant tool can read or write any LiveSpec project
- **Code-anchored**: a minimal, interoperable syntax (§9.4) links spec items to the source code that implements them, so the "live" in *LiveSpec* is backed by an actual mechanism, not just a workflow expectation

### Spec-anchored, not spec-first or spec-as-source

Following Birgitta Böckeler's framing ([Martin Fowler, *SDD: 3 Tools*](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)), LiveSpec targets the **spec-anchored** position on the spectrum:

- **Spec-first** treats the spec as a phase: write it, generate code, move on. The spec drifts or is abandoned once code exists.
- **Spec-anchored** treats spec and code as two first-class, independently authored artifacts kept in sync by explicit linkage (§9.4).
- **Spec-as-source** treats the spec as *the* artifact and code as regenerable on demand.

The §9.4 `livespec:` markers exist precisely to make anchoring **mechanical**: any tool can resolve a spec item back to the code that implements it, and any code site back to the intent it serves. LiveSpec does not assume code is generated from the spec, nor that the spec is reconstructed from the code, both are authored by humans and agents, and linked. Workflow concerns that follow from this stance (drift detection, coverage rules, regeneration semantics) are deliberately left to tooling (§9.4, §15 #014).

### Core principle: the software, not the work

LiveSpec describes **the software**: what it should do, why, who it serves, how it relates to other parts of the system. It does NOT describe **the work on the software**: who is doing it, when, in what state, or how the work is progressing.

That second concern belongs to project-management tools, code-review workflows, and the developer's own task system. Conflating the two is exactly what made past spec formats drift into staleness (Notion pages that nobody updates) or noise (Confluence trees of half-finished tickets). LiveSpec stays on the *software* side of that line on purpose; every design decision in this document can be cross-checked against it.

This principle is the rationale behind several explicit exclusions: no `status` enum on features (§10), no implementation notes, no assignees or due dates, no kanban states. Anything that answers *"how is the work going?"* lives outside the spec, typically referenced from the spec via `x-*` extension fields if a tool needs the bridge.

It does **not** try to be:

- A project management system (see the principle above)
- A documentation generator (no rendering opinions beyond markdown)
- A verification engine: v1 defines how to *express* spec ↔ code links, but leaves coverage, drift detection, and validation entirely to tools (§9.4)
- A policy engine: the format lets you *express* principles, constraints, and conventions as concepts (§6.2), but *enforcing* them across the corpus (e.g. raising warnings when a feature violates a constraint, or requiring features tagged with a given persona to satisfy a checklist) is a tooling concern, not a format concern
- A specific application

---

## 2. Conventions & Conformance Language

This document uses RFC 2119 / RFC 8174 keywords: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.

- **MUST** / **MUST NOT**: absolute requirements for conformance.
- **SHOULD** / **SHOULD NOT**: strong recommendations with allowed exceptions for justified cases.
- **MAY**: optional features.

Tools claiming LiveSpec conformance MUST satisfy all **MUST** requirements at the conformance level they target (see §14).

---

## 3. Repository Layout

A LiveSpec project is a directory tree rooted at a folder containing a `livespec.yaml` manifest. The canonical layout:

```
my-project/
├── livespec.yaml              # Project manifest (required)
├── product/                   # Product context: why, who, what
│   └── {type}/{slug}.md
├── ux/                        # User experience context
│   └── {type}/{slug}.md
├── tech/                      # Technical context
│   └── {type}/{slug}.md
└── features/                  # Feature specifications
    ├── {slug}.md               # Feature with no area
    └── {area}/{slug}.md        # Feature grouped under an area
```

**Rules:**

- The directory containing `livespec.yaml` is the **project root**.
- All paths in this spec are relative to the project root unless stated otherwise.
- The four semantically-meaningful top-level directories are **exhaustive and fixed**: `product/`, `ux/`, `tech/`, `features/`. LiveSpec defines **no mechanism** for adding new top-level directories with LiveSpec semantics. Concerns that span audiences (e.g. developer experience), or that look like sub-domains (e.g. ops, security, compliance, data, business), MUST be modeled as extension types **within the existing four**, never as new top-level folders. This constraint is deliberate: it preserves cross-tool interoperability and prevents the format from fragmenting.
- A project MAY contain additional top-level files and directories (e.g. `README.md`, `.git/`, `compiled/`, `node_modules/`). These have no semantic meaning to LiveSpec; conformant tools MUST ignore them unless explicitly opted in.

### 3.1 Project location patterns

A LiveSpec project can live anywhere, at the root of a repository, or nested inside a wider codebase. The presence of `livespec.yaml` is what defines the project root; everything else is convention. Common patterns:

| Pattern                          | Use case                                                              |
|----------------------------------|-----------------------------------------------------------------------|
| `./livespec.yaml`                | Repository dedicated to a product spec (e.g. `acme/product-spec`).    |
| `docs/livespec/livespec.yaml`    | Spec colocated with code inside an application repository.            |
| `.livespec/livespec.yaml`        | Spec kept as "infra" in a hidden top-level folder (`.github/` style). |
| `specs/livespec.yaml`            | Alternative when a `specs/` folder already exists by convention.      |

A single repository MAY contain multiple LiveSpec projects (e.g. one per app in a monorepo), each with its own `livespec.yaml` defining its own root. They are treated as independent projects with independent slug namespaces.

---

## 4. The Project Manifest (`livespec.yaml`)

Every LiveSpec project MUST contain a `livespec.yaml` at its root:

```yaml
format_version: "1.0"
name: My Project
```

A manifest activating strict mode:

```yaml
format_version: "1.0"
name: Acme Banking Domain
description: Spec for the Account Domain replatforming
mode: strict
```

| Field            | Type   | Required | Description                                              |
|------------------|--------|----------|----------------------------------------------------------|
| `format_version` | string | Yes      | LiveSpec spec version this project conforms to (semver). |
| `name`           | string | Yes      | Human-readable project name.                             |
| `description`    | string | No       | Short project description.                               |
| `mode`           | enum   | No       | `loose` (default) or `strict`. See §12.                  |

Additional fields MAY be added by tools as `x-{tool}-{key}` (e.g. `x-territory-project-id`). Conformant tools MUST preserve unknown `x-*` fields on write.

> **Future:** Mechanisms for shared configuration (presets, manifest inheritance) are under consideration for a future minor version. See §15.

---

## 5. Entities

LiveSpec defines two primary entity kinds:

| Kind             | Purpose                                      | Location              |
|------------------|----------------------------------------------|-----------------------|
| **Concept**      | Stable product/UX/tech knowledge             | `product/`, `ux/`, `tech/`     |
| **Feature**      | Specification of a capability being built    | `features/`           |

Each entity is exactly one markdown file. Each file MUST contain:
1. An H1 heading matching the entity's title
2. Body content (sections defined per entity kind)

A file MAY optionally begin with a YAML frontmatter block (delimited by `---` on its own line, at the very start of the file) carrying typed metadata such as `tags`, `links`, or `assets` (see entity-specific contracts in §6 and §7). The frontmatter MUST be omitted when it would contain no fields: tools MUST NOT emit empty frontmatter blocks (`---` immediately followed by `---`), and writers SHOULD strip a frontmatter block that becomes empty after editing.

A `---` line at the start of a file is ALWAYS interpreted as a frontmatter delimiter, never as a markdown horizontal rule.

---

## 6. Concepts

### 6.1 Directory mapping rule

**Rule:** Inside `product/`, `ux/`, and `tech/`, each concept type lives in a subdirectory whose name **is** the type slug. The same slug is used as the key in `links` (see §9). No mapping table: the slug is canonical everywhere.

```
product/{type}/{item-slug}.md
ux/{type}/{item-slug}.md
tech/{type}/{item-slug}.md
```

Example: a concept of type `persona` with slug `the-product-engineer` lives at `product/persona/the-product-engineer.md`, and is referenced as `links: { persona: [the-product-engineer] }`.

### 6.2 Core taxonomy

This is the minimal **core taxonomy** of v1. Tools claiming Level 2+ conformance MUST support these types.

**Under `product/`:**
- `persona`: A user archetype.
- `pain_point`: A user or business pain the product addresses.
- `goal`: An outcome the product aims to deliver.
- `principle`: A guiding belief or rule for product decisions.
- `constraint`: A limit or quantitative rule imposed on the product. Covers scope, business, regulatory, and operational rules (e.g. *"daily transfer limit = €3,000"*, *"GDPR retention ≤ 90 days"*, *"the product never stores plaintext credentials"*). A constraint is a *standing rule* that multiple features must respect, distinct from a feature-specific `REQ` (§8) and from a `principle` (a belief; constraints are limits).
- `entity`: A durable object of the business domain (e.g. `User`, `Order`, `Invoice`, `Policy`). Captures the entity's role in the product, its identity, its notable attributes, and its invariants, at the editorial level the domain warrants, not as a database schema. Features link to entities they manipulate via `links.entity` (§9.2).
- `glossary_term`: A defined term used consistently across specs.

**Under `ux/`:**
- `ui_component`: A UI component (button, modal, input) with its usage rules.
- `design_principle`: A guiding belief or rule for UX decisions.
- `ux_pattern`: A reusable interaction or layout pattern.

**Under `tech/`:**
- `coding_standard`: A coding rule or convention.
- `architecture_decision`: An architectural choice and its rationale.
- `external_system`: A third-party system or service the product integrates with (e.g. a payment provider, a CRM, a mainframe, a partner API, a managed message broker). Captures what the system is, the integration boundary, and the failure model, not its internal implementation. Features link to external systems they integrate with via `links.external_system` (§9.2).

#### Naming convention for type slugs

Two rules govern type slug naming:

1. **Globally unique.** A type slug MUST be unique across the entire taxonomy. The resolver determines a concept's location from its type slug alone: no two types may share a slug, even across different top-level directories.
2. **Self-disambiguating.** A type slug SHOULD make sense on its own, without relying on its containing directory for meaning. Types whose bare name could plausibly belong to a different domain MUST be prefixed (e.g. `ui_component`, not `component`, because "component" is ambiguous with software components; `ux_pattern`, not `pattern`, because patterns exist in tech too).

Conversely, types whose bare name is already unambiguous (`persona`, `coding_standard`, `architecture_decision`) do not need a prefix.

**The product layer is the implicit default domain.** When a concept exists at both the product level and a more specific domain level, the unprefixed slug is reserved for the product-level variant. Example: `principle` is a product principle in `product/`; `design_principle` is its UX specialization in `ux/`. The same convention would apply if a future `tech_constraint` were introduced, `constraint` (unprefixed) would remain the product-level constraint in `product/`.

#### Recommended extension namespaces

To prevent fragmentation when teams introduce extension types for common technical concerns, LiveSpec recommends a shared naming convention:

- **`{concern}_convention`** for cross-cutting engineering rules: `api_convention`, `testing_convention`, `logging_convention`, `error_handling_convention`, `i18n_convention`, `data_convention`, `security_convention`, `performance_convention`.
- **`{concern}_pattern`** in `ux/` for design-system or interaction patterns scoped to a concern: `form_pattern`, `navigation_pattern`, `feedback_pattern`.

These are **not core types**: tools are not required to support them. But teams adding any of these SHOULD use the slug listed here so that LiveSpec projects and tools can interoperate consistently across organizations.

> **Extensions:** Tools MAY define additional types as subdirectories of `product/`, `ux/`, or `tech/`. Custom type slugs MUST follow both naming rules above. Unknown types MUST NOT cause parse failure in Level 1+ readers. A future RFC will formalize the extension registration mechanism (including the recommended namespaces above). See §15.

### 6.3 Frontmatter contract

```yaml
---
tags: [optional, comma-separated, labels]
links:
  {other-type-slug}: [slug-1, slug-2]
---
```

| Field   | Type             | Required | Description                          |
|---------|------------------|----------|--------------------------------------|
| `tags`  | string[]         | No       | Free-form classification labels.     |
| `links` | object           | No       | Cross-references; see §9.            |

All fields are optional. A concept with neither `tags` nor `links` MUST omit the frontmatter block entirely (per §5), the file begins directly with the H1 title.

**Concepts MAY link to other concepts.** The `links` field is symmetric: it works the same way in concepts as in features (§7.2). A `persona` may link to relevant `pain_point`s, a `goal` may link to the `persona`s it serves, an `entity` may link to other entities it relates to. The resolution rules in §9.2 apply uniformly. Example:

```yaml
---
links:
  pain_point: [forgetting-recurring-tasks]
  goal: [stay-on-top-of-personal-tasks]
---
```

Concept↔concept links are unidirectional in storage but SHOULD be presented bidirectionally by tools (§9.3). Only the **typed feature relations** (`requires` / `triggers` / `extends`, §7.2) are restricted to feature↔feature, they do not apply between concepts.

### 6.4 Body contract

```markdown
# {Title}

{One-paragraph summary: MUST be present, MUST be a single paragraph}

## {Author-defined section}

{Free-form markdown content}

## {Another author-defined section}

{Free-form markdown content}
```

- The H1 title MUST match the file's intended display name.
- The opening paragraph immediately following the H1 is the **summary**: it MUST be present, MUST be a single paragraph, and is what tools display in lists / link previews.
- Any content after the summary is OPTIONAL and is organized as free-form H2 sections (with H3+ sub-headings as needed).
- H2 section names are chosen by the author. Tools MUST NOT impose constraints on H2 (or deeper) section names in a concept body, and MUST NOT require any specific section to be present.

### 6.5 Choosing: concept, feature, or spec item

LiveSpec offers three places to record a given piece of product knowledge: as a **concept** in `product/`, `ux/`, or `tech/`; as a **feature** under `features/`; or as a **spec item** (REQ, AC, AS, Q, ISS) inside a feature. The choice is editorial, not mechanical: the format won't stop you from putting a cross-cutting rule inside a single feature, or from declaring a deliverable as a concept. But the wrong choice produces silent duplication, ownership confusion, and drift. This section gives you the editorial rule for *when* to use each.

**One question, three answers.** The same deciding question applies across all three frontiers:

| Question                                                          | Answer points to |
|-------------------------------------------------------------------|------------------|
| Does it **ship** in a PR with verifiable acceptance criteria?     | feature          |
| Is it **specific** to one feature's behavior?                     | spec item        |
| Is it a **standing property** that multiple features must respect?| concept          |

The three frontiers that follow apply this question pairwise.

#### Concept vs. spec item

A rule like *"all logs must include a `trace_id`"* could plausibly live as a `logging_convention` concept in `tech/`, or as a `REQ` inside every feature that emits logs. **A concept captures a standing rule; a spec item captures a specific behavior of one feature.**

Symptoms that point to **concept**:

- The rule pre-existed this feature and will survive after it ships.
- The rule applies to other features without needing to be restated.
- The rule evolves at its own pace, not in lockstep with any single feature.
- The rule is owned by a transverse team or domain authority, not by the feature's author.

If symptoms conflict, prefer **promote + link**: extract the rule as a concept, and let each feature reference it via `links` (§9). Promoting is cheap; un-duplicating later is not.

#### Concept vs. feature

A capability like *"two-factor authentication"* could plausibly live as `tech/security_pattern/two_factor.md` (concept) or as `features/auth/two-factor.md` (feature). **A feature ships; a concept informs.** The litmus test: can you write acceptance criteria a PR can satisfy? If yes, it's a feature.

Symptoms that point to **feature**:

- It has a clear deliverable scope and verifiable behavior.
- Its progress is meaningful (`[ ]` AC turning into `[x]`).
- A user, an integrator, or a system observably gains something when it lands.
- It has a beginning and an end in delivery terms: once shipped, it's "done"; subsequent changes are new features or new REQs.
- **It remains conceptually present in the software after delivery.** A new joiner reading the spec a year later sees it as part of *what the software is*, not as a record of work that happened.

Symptoms that point to **concept**:

- It describes *how* something works rather than *that* it is being built.
- It is referenced by features that *implement* or *respect* it, but isn't itself built.
- It can be true of the system at any moment, independently of any active delivery.

A common confusion: a feature MAY be *named after* a concept. `features/auth/two-factor.md` ships the capability; `tech/security_pattern/two_factor.md` describes the standing pattern the codebase follows. The two MAY coexist: the feature references the concept via `links`. But a single document MUST NOT try to be both.

#### Feature vs. spec item

A behavior like *"export user data as CSV"* could plausibly be its own feature (`features/data/export-csv.md`) or a single `REQ` inside a broader feature (`features/data/user-data-management.md`). **A feature is a deliverable; a spec item is a fragment of a deliverable.** The deciding question is **independent shippability**: does this stand on its own (with its own AC, persona links, and assets), or does it only make sense inside a larger capability?

Symptoms that point to **feature**:

- Shippable independently of other items in its parent context.
- Distinct user value or system effect that warrants its own narrative.
- Worth linking to from outside (other features, concepts) by name.
- Has its own persona, pain point, or goal linkage beyond the parent's.

Symptoms that point to **spec item**:

- Only meaningful as a behavior of an already-existing capability.
- Would be a sentence of body text, not a paragraph plus AC.
- No linkage of its own beyond what the parent feature already declares.

When in doubt, prefer **spec item first, extract later**: a REQ is cheap to add and easy to promote to a sibling feature once scope justifies it. Premature feature splitting fragments the spec; consolidating later is harder than splitting later.

#### Illustrative examples

| Statement                                                                  | Goes as                          | Why                                                                                       |
|----------------------------------------------------------------------------|----------------------------------|-------------------------------------------------------------------------------------------|
| *"All public APIs accept JSON and XML."*                                   | `api_convention` (concept)       | Pre-existing, applies to every API endpoint, evolves at platform pace.                    |
| *"All logs include a `trace_id`."*                                         | `logging_convention` (concept)   | Cross-cutting, no single feature owns it.                                                 |
| *"Telemetry events are opt-in."*                                           | `principle` in `product/`        | Standing product belief that shapes every feature emitting telemetry.                     |
| *"Two-factor authentication."*                                             | feature under `features/auth/`   | Ships, has AC, observable user-facing capability.                                         |
| *"The system uses TOTP, FIDO2, and recovery codes as second factors."*     | `security_pattern` (concept)     | Describes the standing approach the codebase respects; many features reference it.        |
| *"The `/checkout` endpoint accepts an `idempotency_key` header."*          | `REQ` in the checkout feature    | Specific to this endpoint and feature; not a general convention.                          |
| *"On checkout error, retry up to 3 times with exponential backoff."*       | `REQ` in the checkout feature    | Feature-specific behavior, unless retry policy is uniform, then promote to a convention. |
| *"Export user data as CSV."*                                               | feature *or* `REQ`               | Standalone feature if delivered with its own narrative; `REQ` if one capability of a broader `data-export`. |
| *"An `Order` has a customer, line items, and a status."*                   | `entity` in `product/`           | Domain object multiple features manipulate; lives independently of any one feature.                       |
| *"Daily transfer limit is €3,000."*                                        | `constraint` in `product/`       | Standing quantitative rule that multiple features must respect.                                            |
| *"Payments go through Stripe."*                                            | `external_system` in `tech/`     | A third-party system the product integrates with, referenced by every feature that touches payment.        |

**Boundary rule (both directions).** If, while writing a feature, you state a rule that *would clearly apply elsewhere*, stop and write it as a concept first, then link from the feature. Conversely, if a "concept" you're writing has acceptance criteria, a deliverable scope, and would observably advance the product when implemented, you're writing a feature: move it to `features/`.

---

## 7. Features

A feature represents a **durable part of the software**: a capability, integration, or subsystem that remains conceptually present after delivery and that other parts of the spec can refer to by name. It is not a unit of work, a migration, an upgrade, or a one-time change. Per §1 ("the software, not the work"), the act of building, migrating, or refactoring belongs to PRs, ADRs, runbooks, and task trackers; only the resulting durable capabilities belong in `features/`.

If a candidate document would lose all readers' attention the day after merge, it is not a feature. Either its outcome belongs in an existing feature or a concept, or it has no place in LiveSpec at all.

### 7.1 Directory layout

A feature lives either directly under `features/{slug}.md` (no area) or under `features/{area}/{slug}.md` (grouped under an area). The `{area}` segment is an organizational grouping for related features (e.g. `features/authentication/sign-in-with-google.md`); it is OPTIONAL and carries no semantic meaning to LiveSpec: it only shapes how features are presented and located on disk.

A feature's area is derived from its file path: the path segments between `features/` and the file, joined by `/`, or empty if the file sits directly under `features/`.

Areas MAY nest one level (e.g. `features/billing/invoicing/generate-pdf.md`). Deeper nesting is reserved for a future RFC.

**Slug-area collision.** A feature slug MUST NOT collide with the name of a sibling area. For example, `features/billing.md` and `features/billing/invoice.md` MUST NOT coexist: to a human reader, `billing` is ambiguously both a feature and an area. This rule is mechanical (a linter can check it without judgment) and the fix is trivial (rename one or the other). Tools MUST report this as a lint error.

### 7.2 Frontmatter contract

```yaml
---
links:
  persona: [slug-1, slug-2]
  pain_point: [slug-3]
  goal: [slug-4]
  entity: [order, customer]
  external_system: [stripe]
  constraint: [daily-transfer-limit]
  feature:
    requires: [auth-sign-in]
    triggers: [send-reminder]
    extends: [export-csv]
assets:
  - id: {uuid-or-stable-id}
    type: wireframe | mockup | diagram | screenshot | reference
    title: {Human-readable title}
    description: {Short description}
    path: assets/{feature-slug}/{filename}
---
```

| Field    | Type     | Required | Description                                              |
|----------|----------|----------|----------------------------------------------------------|
| `links`  | object   | No       | Cross-references; see §9.                                |
| `assets` | object[] | No       | Asset metadata; see §11.                                 |

All fields are optional. A feature with neither `links` nor `assets` MUST omit the frontmatter block entirely (per §5), the file begins directly with the H1 title.

#### Typed feature relations

The `feature` key MAY take two forms:

- **Untyped list**: `feature: [slug-a, slug-b]`. The listed features are related, without saying how. Use sparingly, as a "see also": most real relationships are typed.
- **Typed object**: `feature: { requires: [...], triggers: [...], extends: [...] }`. The listed features are related by the named relation.

A single `feature` key MUST take one form or the other: list **or** object, not both. To mix typed and untyped links for the same feature, prefer the typed form throughout.

The three relations defined in v1:

| Relation   | Meaning                                                                              |
|------------|--------------------------------------------------------------------------------------|
| `requires` | This feature does not function without the listed feature (hard runtime dependency). |
| `triggers` | This feature causes the listed feature to run (often asynchronously).                |
| `extends`  | This feature is a specialization of the listed feature.                              |

Relations are **unidirectional in storage** (declared on the source feature) but tools SHOULD present them bidirectionally (see §9.3).

Relations are restricted to feature↔feature. Relations from a feature to a concept (e.g. *"this feature respects this constraint"*, *"this feature manipulates this entity"*) are carried by the **concept type itself** in the `links` object: `constraint: [...]` already means *"respects"*, `entity: [...]` already means *"manipulates"*, `external_system: [...]` already means *"integrates with"*, and so on. No explicit typing needed.

> **Note:** v1 intentionally does not define a `status` field for features. Capturing spec maturity and implementation state in a structured way is deferred (see §10 and §15).

### 7.3 Body contract

A feature body MUST contain:
- An H1 heading matching the feature title
- An opening summary paragraph (see §7.4)

The body MAY contain free-form markdown content: prose, H2/H3 headings, lists, code, and inline spec items (see §8). Spec items are recognized by their syntax, not by their containing section.

**Canonical section names.** LiveSpec defines a set of canonical H2 section names whose semantics are universally understood:

| Section                   | Intended contents                                                            |
|---------------------------|------------------------------------------------------------------------------|
| `## Requirements`         | `REQ` items (with nested `AC` items)                                         |
| `## Assumptions`          | `AS` items                                                                   |
| `## Questions`            | `Q` items                                                                    |
| `## Issues`               | `ISS` items                                                                  |
| `## UX`                   | Free-form UX notes (and future `UX_DIRECTION` items, §15 #005)               |
| `## Tech`                 | Free-form technical notes (and future `TECH_DIRECTION` items, §15 #005)      |

> **Ephemeral implementation context** (decisions in progress, handoff state, "I'm here, next step is X") belongs in git commits, PR descriptions, or external task trackers, not in the spec. This follows from the core principle (§1): LiveSpec describes the software, not the work on it. Durable architectural decisions go to `## Tech` or to an `architecture_decision` concept.

**Behavior by mode** (see §12):

- **Loose mode (default):** Writers SHOULD use canonical section names where applicable, but MAY use any H2 name. Spec items are identified by their inline syntax wherever they appear. Tools MUST preserve unrecognized sections on write (losslessness).
- **Strict mode:** H2 section names MUST be drawn from the canonical set above. Each spec item type MUST appear only in its intended section (e.g. an `ISS` item inside `## Requirements` is a lint error). Section ordering MUST follow the canonical order: Requirements → Assumptions → Questions → Issues → UX → Tech.

**Empty sections:** H2 sections with no content SHOULD be omitted rather than left empty. A missing section is the canonical way to say "nothing here."

**Section content:** Within any section (canonical or otherwise), free-form prose, H3 sub-headings, and inline spec items can intermix freely. H3 sub-headings are visual organizers and carry no semantic meaning for the parser. AC nesting (§8) is determined by markdown list indentation, not by section structure.

### 7.4 Opening paragraph conventions

Every feature MUST begin with a single opening paragraph that summarizes the feature in human terms. Its **presence** is required; its **form** is the author's choice. Tools display this paragraph in lists and link previews.

The user-story format remains the recommended idiom for user-facing features, but it is one form among several. Common idiomatic openings:

- **User-facing**: `As a {role}, I want {capability} so that {value}.`
- **Subsystem / integration**: `When {trigger}, the system {action} so that {outcome}.` (for durable non-user-facing components: auth subsystem, job scheduler, webhook delivery, payment integration). The opening describes the **standing behavior** of the component, not the act of building it.

These are not a closed taxonomy and v1 does not enforce a specific signature. The intent is to normalize the fact that **several legitimate forms exist**, so authors aren't tempted to contort a subsystem feature into an `As a {role}` template that doesn't fit. A future RFC may promote one or more of these into a structured frontmatter field if a clear need emerges.

> **Migrations, upgrades, and refactors are not features.** Their target state, if durable, belongs in an existing feature (as evolving REQs) or a concept (as a standing tech property). The act of getting there belongs in PR descriptions, ADRs, or runbooks. *"Migrate search from Postgres FTS to Meilisearch"* is task-shaped; *"Search uses Meilisearch with sub-200ms p95"* is a durable REQ in the `search` feature (or a `tech` concept describing the standing engine choice). See §1 and the §7 preamble.

### 7.5 Feature granularity

"Is this one feature or two?" is the hardest editorial question in practice. v1 deliberately defines **no numeric thresholds**: no max REQs, no max ACs per REQ, no max body length. Domains differ too widely for any number to hold (a regulated payment feature legitimately has many more REQs than a UI toggle), and any number becomes a target rather than a guide. Instead, v1 provides qualitative smell tests that surface the same intuition without becoming arbitrary rules.

When deciding whether to split a feature, ask:

- **One-sentence test.** Can the feature be summarized in a single opening paragraph (§7.4) without conjunction-stuffing ("and also", "as well as", "plus")? If the natural summary needs two sentences with different subjects, two features are hiding.
- **Single-narrative test.** Does the opening paragraph fit *one* of the §7.4 idioms cleanly, or does it mix user-facing AND subsystem framings? Mixed framings usually mean two features serving two audiences.
- **Shared-audience test.** Do the REQs serve the same persona, integrator, or system? If different ACs target disjoint audiences with no overlap, the feature is probably a bundle.
- **Independent-PR test.** Would the feature naturally ship in two or more PRs whose ACs don't touch each other? If yes, the slicing is already telling you.
- **External-reference test.** Would other features or concepts want to link to *part* of this feature by name? If a sub-capability deserves to be referenced from outside, it deserves to be its own feature.

When deciding whether to merge two features into one, ask the same questions in reverse: if both fail (one paragraph holds, one narrative, one audience, AC interdependent, no external reference to either half), the split was premature.

**Length is a symptom, not a criterion.** A `## Requirements` section that becomes uncomfortable to read in one pass is a *signal*: check the smell tests above. If they confirm, split. If they don't (e.g. regulated domains where every REQ legitimately belongs), the length is acceptable and tooling can paginate the view.

**Default heuristic.** When in doubt, **start coarser and split later**. Adding REQs to an existing feature is cheap; extracting them into a sibling feature is straightforward (REQ IDs are file-scoped, see §8.3); but consolidating two features that have grown independent links, assets, and external references is painful. Premature splitting fragments the spec and dilutes each feature's narrative.

---

## 8. Spec Items

Spec items are atomic, addressable units inside a feature: requirements, acceptance criteria, assumptions, questions, issues, and design directions.

### 8.1 Inline syntax

Spec items appear as GitHub-flavored checkbox list items:

```markdown
- [x] REQ-1: User can sign in with email and password
  - [x] AC-1.1: Email field accepts standard RFC 5322 addresses
  - [ ] AC-1.2: Whitespace-only input is rejected with inline error
  - [-] AC-1.3: Network failure retry banner: dropped in favor of generic toast
- [ ] REQ-2: Failed login shows error message
  - [ ] AC-2.1: Error appears within 200ms of submit
```

| Field        | Format                                                       | Required |
|--------------|--------------------------------------------------------------|----------|
| Indent       | 0 spaces (REQ/AS/Q/ISS), 2 spaces (AC under its parent REQ)  | Yes      |
| Checkbox     | `- [ ]`, `- [x]`, or `- [-]` (see "Checkbox states" below)   | Yes      |
| Type prefix  | `REQ`, `AC`, `AS`, `Q`, `ISS`                                | Yes      |
| ID           | See §8.3                                                     | Yes      |
| Body         | After `:` (may span multiple lines, see below)               | Yes      |

#### Checkbox states

| Token  | Generic meaning            | Per-type interpretation                                                    |
|--------|----------------------------|----------------------------------------------------------------------------|
| `[ ]`  | Open / pending             | REQ/AC: not yet done. AS: not yet validated. Q: unanswered. ISS: unresolved.  |
| `[x]`  | Done / closed              | REQ/AC: implemented. AS: validated / confirmed. Q: answered. ISS: resolved.   |
| `[-]`  | Cancelled / won't do       | Explicitly decided not to pursue. Body SHOULD state the reason.             |

The `[-]` state preserves the historical record of a dropped item without removing it (which would lose decision context) or falsely checking it. GitHub renders `[-]` with strikethrough.

#### Multi-line bodies

A spec item body MAY span multiple lines via standard markdown list-item continuation: text indented under the item, before any nested children:

```markdown
- [ ] REQ-3: User can export their data as CSV.
  The export includes all fields visible in the UI, plus internal
  IDs. Computed fields are flattened to their displayed string form.
  - [ ] AC-3.1: Export button visible in user menu
```

#### Resolution notes

When a spec item is closed (`[x]` or `[-]`), authors MAY record **why** or **how** it was closed using a body continuation line that starts with `→ `. Such a line is a *resolution note*: semantically distinct from the item's original content.

```markdown
- [x] Q-1: Does the export need pagination beyond 100 results?
  → Yes, paginate by 50 with an opaque cursor. Decided 2026-03-12.

- [x] ISS-2: [AC-2.1] currently fails on Safari 16.
  → Fixed by `structuredClone` polyfill in 2c4a9f1.

- [-] AC-3.2: Retry banner on network failure.
  → Dropped in favor of the generic toast (see [feature-error-handling#REQ-1]).
```

Rules:

- A resolution note is a single continuation line starting with the literal prefix `→ ` (U+2192 followed by one space), at the item's body indentation level. It MAY wrap onto subsequent indented lines using standard list-item continuation.
- An item MAY have **at most one** resolution note. Multiple `→ ` lines on the same item are a lint error.
- A resolution note is meaningful only on closed items (`[x]` or `[-]`). On an open item (`[ ]`) it is a lint warning: the note is preserved as-is by the parser, but tools SHOULD flag it.
- The note MAY appear anywhere in the body (before or after other continuation lines), but writers SHOULD place it last for readability.
- The `→ ` prefix is part of the syntax, not the note content: tools extracting the note MUST strip it.

Resolution notes are particularly valuable on `Q` (the answer), `ISS` (how resolved or workaround), and `AS` (what was validated or invalidated). On `REQ`/`AC`, the code itself is usually the answer (via `livespec:` markers, §9.4): a resolution note here is optional commentary, not a substitute for anchoring.

A parser that does not recognize the `→ ` convention will read the line as ordinary body prose; the document remains valid. Resolution notes are therefore a **Level 1** feature: writing them is OPTIONAL, recognizing them is OPTIONAL, and ignoring them is conforming.

#### Inline formatting

Bodies MAY contain **inline** markdown formatting: `**bold**`, `*italic*`, `` `code` ``, `[link](url)`, etc.

Bodies MUST NOT contain **block-level** constructs (headings, fenced code blocks, tables, blockquotes). If a requirement needs that level of elaboration, the prose belongs in `## Tech` or `## UX` notes, with the REQ referencing it by name.

#### Nesting depth

ACs MUST be nested exactly **one indentation level** (2 spaces) below their parent REQ. Deeper nesting is invalid:

```markdown
- [ ] REQ-1: ...
  - [ ] AC-1.1: ...      ← valid
    - [ ] AC-1.1.1: ...  ← INVALID; split into multiple REQs instead
```

If a REQ would naturally produce sub-structure, decompose it into multiple REQs rather than introducing AC sub-trees. This keeps the parsing model simple and the document scannable.

#### Visual spacing

Writers SHOULD insert a blank line between top-level spec items when a section contains more than three of them, to improve scannability. The blank line is semantically meaningless to LiveSpec parsers: both tight and loose markdown lists are valid.

#### Inline references to other spec items

Within a spec item body, references to other spec items use bracketed-ID syntax:

| Reference target               | Syntax                          |
|--------------------------------|---------------------------------|
| Same-feature spec item         | `[REQ-3]`, `[AC-3.2]`, `[Q-1]`  |
| Spec item in another feature   | `[feature-slug#REQ-3]`          |

Example:

```markdown
- [ ] Q-1: Does [REQ-3] need pagination when the result list exceeds 100 entries?
- [ ] ISS-2: [AC-2.1] currently fails on Safari 16 (works on Chrome and Firefox).
```

Tools MAY render these as navigable links and use them to build a reverse-reference index ("where is REQ-3 referenced?").

### 8.2 Spec item types

| Type  | Name                  | Position                            | Purpose                                              |
|-------|-----------------------|-------------------------------------|------------------------------------------------------|
| `REQ` | Requirement           | Top-level in `## Requirements`      | Functional/behavioral requirement of the feature.    |
| `AC`  | Acceptance Criterion  | Nested under a REQ (2-space indent) | Specific testable condition for its parent REQ.      |
| `AS`  | Assumption            | Top-level in `## Assumptions`       | Assumption the spec relies on; flag if invalidated.  |
| `Q`   | Question              | Top-level in `## Questions`         | Unresolved question that blocks or shapes the spec.  |
| `ISS` | Issue                 | Top-level in `## Issues`            | Known issue, defect, or limitation affecting this feature. |

**AC linkage.** An AC's parent REQ is determined **structurally** by markdown list nesting: no explicit reference is needed. An AC that is not nested under a REQ is a lint error.

**REQ done semantics.** A REQ marked `[x]` while one or more of its ACs are still `[ ]` is permitted but SHOULD trigger a lint warning. Teams may legitimately consider a REQ "done enough" when non-critical ACs remain open, but the discrepancy is worth surfacing. ACs in the `[-]` (cancelled) state do not contribute to this warning.

> **Future:** `UX_DIRECTION` and `TECH_DIRECTION` will be formalized as block-level (not inline) spec items. See §15 #005.

### 8.3 Identifiers

**REQ / AS / Q / ISS IDs** use the form `{TYPE}-{N}` where `N` is a positive integer, scoped to its parent H2 section. Example: `REQ-1`, `REQ-2`, `AS-1`, `Q-1`, `ISS-1`.

**AC IDs** use the form `AC-{parent_req_index}.{ac_index}` reflecting structural nesting:

```markdown
- [x] REQ-1: ...
  - [x] AC-1.1: ...
  - [x] AC-1.2: ...
- [x] REQ-2: ...
  - [x] AC-2.1: ...
```

**IDs are file-scoped and human-assigned.** `REQ-1` in feature A is unrelated to `REQ-1` in feature B. Cross-feature references use the form `{feature-slug}#REQ-3` or `{feature-slug}#AC-3.2`.

#### Immutability

Once assigned, an ID MUST never be reused or renumbered, even if its spec item is deleted or cancelled. This guarantee is what makes inline references (`[REQ-3]`) and cross-feature references (`{slug}#REQ-3`) reliable. Tools that mutate LiveSpec files MUST preserve existing IDs and MUST assign new IDs only by extending the sequence.

To remove a spec item without breaking inbound references, mark it `[-]` (cancelled) rather than deleting it.

**Bodies are mutable; IDs are not.** A spec item's body MAY evolve freely over time (typo fixes, clarifications, scope adjustments) while keeping the same ID. Tracking the substantive history of a body change (e.g. "this AC originally said X, now says Y") is **out of scope for v1**: the canonical history is `git`. See §15 #019.

#### Gaps are valid

Gaps in numbering are conformant. A file containing `REQ-1, REQ-3, REQ-7` is valid: it simply means earlier IDs were assigned and later removed (or the sequence was never contiguous). Tools MUST NOT reject gapped numbering, MUST NOT renumber to close gaps, and MUST NOT require IDs to appear in numeric order within the file.

> **Known limitation:** Manual numbering can still produce merge conflicts when two parallel changes assign the same next integer. Resolution is mechanical (the second-merged change takes the next free integer) but currently manual. Opaque IDs (e.g. `REQ-7f3a`) as an alternative scheme are under consideration for a future RFC. See §15.

---

## 9. Linking System

### 9.1 Slug rules

All entities are identified by a **slug**: the filename without the `.md` extension.

- Slugs MUST match the regex `^[a-z0-9]+(-[a-z0-9]+)*$` (kebab-case ASCII).
- Slugs MUST be unique within their type's directory.
- Slugs SHOULD be stable; renaming a file is a breaking change for inbound links.

### 9.2 Link resolution

Links appear in frontmatter under the `links` field, keyed by **target type slug** (always singular):

```yaml
links:
  persona: [the-product-engineer]
  pain_point: [decisions-get-lost, context-gap-for-ai-coding-tools]
  entity: [user, document]
  external_system: [stripe]
  feature:
    requires: [auth-sign-in]
    triggers: [send-reminder]
```

Resolution algorithm:
1. The key (e.g. `persona`) is the type slug.
2. For concept types, the file is resolved to `{product|ux|tech}/{key}/{slug}.md`: the resolver determines the containing top-level directory by looking up the type in the core taxonomy (§6.2) or in registered extensions.
3. For the special key `feature`, the value MAY be either a list of slugs or an object whose keys are typed relation names (§7.2). In both cases each slug resolves to `features/**/{slug}.md` (searched across feature areas; slugs are globally unique within `features/`). The relation name is preserved for tools but does not change resolution.
4. A link to a non-existent file is a **lint warning**, not a parse error (see §14).

### 9.3 Bidirectional links

Links are unidirectional in the file format but SHOULD be presented bidirectionally by tools. Tools MAY maintain an index for reverse lookup. The source of truth is always the forward link in the writing entity.

### 9.4 Spec ↔ Code Linking

A LiveSpec project describes software that exists (or is being built) in a codebase. To make that relationship explicit and machine-discoverable (without locking the format to a specific verification workflow), v1 defines a single convention: an inline marker placed in source files, pointing back to a spec item.

#### Marker format

```
livespec: {feature-slug}#{spec-item-id}(,{spec-item-id})*
```

The marker MUST appear inside a comment using the host language's native comment syntax. The format defines the **payload**, not the comment delimiter:

```js
// livespec: full-text-search#REQ-3
```
```python
# livespec: full-text-search#AC-1.2
```
```html
<!-- livespec: idempotency#REQ-1 -->
```

A single marker MAY point to several spec items **of the same feature** by listing their IDs after the `#`, separated by commas with no surrounding whitespace:

```js
// livespec: analyze-current-page#REQ-1,REQ-2,AC-3.2
```

This list form exists to avoid repeating the feature slug when one code site serves several items of the same feature. It is exactly equivalent to one single-item marker per ID. The feature slug appears once and scopes every ID in the list; an ID in the list MUST NOT carry its own `feature-slug#` prefix. To reference items across **different** features, a source file uses one marker per feature (a file MAY carry many markers).

A source file MAY carry zero, one, or many markers. A marker pointing to a `REQ` implicitly covers its nested `AC`s unless more specific AC-level markers exist elsewhere; this applies per listed ID.

The payload grammar is `livespec:` followed by one or more spaces, then `{feature-slug}#{spec-item-id}`, optionally followed by one or more `,{spec-item-id}` with no internal whitespace anywhere in the payload. Tools MUST match case-sensitively. Tools MUST recognize the list form and resolve every listed ID. Feature slugs are globally unique within `features/` (§9.2), so the area is not part of the marker: markers remain stable when a feature is moved between areas.

#### Resolution

A `livespec:` marker resolves by:
1. Locating the feature file by searching `features/**/{feature-slug}.md`.
2. Finding, for each listed ID, the spec item with the matching ID inside that file (per §8.3).

A marker whose feature file is missing is a **broken link**. In the list form, each listed ID resolves independently: an ID that does not exist in the feature file is a broken link for that ID alone, leaving the other IDs in the same marker valid. Tools SHOULD report broken links as a lint warning at Level 3+.

#### Scope of this section: what v1 does and does not define

LiveSpec v1 defines **the syntax of the link, and only the syntax**. The format does NOT define:

- **Coverage rules**: which spec items must carry a marker, or how many markers a spec item should have.
- **Drift detection**: what to do when code changes without spec changes, or vice-versa.
- **Verification semantics**: running the marked code as a test of the spec item, computing coverage reports, blocking merges on missing markers, or invoking agents to re-validate conformance.

These are **tooling concerns**, not format concerns. A CI hook, an IDE plugin, or an agent-driven verifier MAY implement any of them on top of the marker syntax; doing so is out of scope for the format itself. Standardizing any subset of these semantics is tracked in §15 #014.

The format guarantees one thing: **if a `livespec:` marker is present in source code, any conformant LiveSpec tool will recognize it and resolve it to a spec item**. That minimum is what makes spec↔code linking interoperable across tools and workflows.

### 9.5 In-prose references

Inside the body of a concept or feature, authors MAY reference other entities using a wiki-style bracketed syntax. This complements but does not replace the frontmatter `links:` field (§9.2); see "Relation to `links:` frontmatter" below.

#### Syntax

Two forms are defined:

| Form                     | Meaning                                                              | Example                                |
|--------------------------|----------------------------------------------------------------------|----------------------------------------|
| `[[type:slug]]`          | Typed reference. Always valid.                                       | `[[persona:solo-organizer]]`           |
| `[[slug]]`               | Shorthand. Valid only when `slug` is unambiguous across the project. | `[[remind-on-due-date]]`               |

For features, the type prefix is `feature`. For concepts, the type is the concept's type slug (§6.2). The literal characters `[[` and `]]` MUST appear without whitespace around the payload. Tools MUST match case-sensitively.

#### Resolution

1. For `[[type:slug]]`: look up `type` against the taxonomy (§6.2 + extensions) to find the containing directory, then resolve to `{dir}/{type}/{slug}.md`. For `type = feature`, resolve to `features/**/{slug}.md`.
2. For `[[slug]]`: search across all features and all concept types in the project.
   - **Exactly one match** → resolved.
   - **Zero matches** → broken reference; lint warning at Level 3 (§14).
   - **Two or more matches** → ambiguous; lint warning at Level 3. The author MUST disambiguate using the typed form.

A broken or ambiguous in-prose reference does NOT invalidate the document: readers without a resolver simply read the literal `[[...]]` text. The format degrades gracefully.

#### Where in-prose references are allowed

In-prose references MAY appear in:

- Concept body prose (anywhere after the H1).
- Feature body prose (anywhere after the H1, in any section).
- Spec item bodies (§8.1), alongside same-file `[REQ-3]` and cross-feature `[feature-slug#REQ-3]` references.

They MUST NOT appear in frontmatter values (which use structured `links:` per §9.2), in slugs themselves, or in `livespec:` code markers (which use the unambiguous `feature-slug#spec-item-id` form per §9.4).

#### Relation to `links:` frontmatter

In-prose references are **reading aids**, not a substitute for the frontmatter `links:` field. The two have distinct purposes:

- **`links:` frontmatter** carries the *significant* relations of the entity: the ones a tool indexes, presents in a graph, or audits for coverage. It SHOULD be exhaustive on relations that *structurally matter*.
- **In-prose `[[ ]]`** are *contextual mentions*: naming another entity while describing the current one, to keep prose navigable for human readers. They are not exhaustive and are not required to mirror the frontmatter.

A reference MAY appear in prose without being declared in `links:`, and a relation MAY be declared in `links:` without being mentioned in prose. Tools building a project-wide reference graph SHOULD index both, but MUST NOT treat a missing prose mention as a defect, nor a missing `links:` entry as one (absent explicit coverage configuration).

When a relation is structurally meaningful (a feature requiring another, an entity composing another, a feature integrating with an external system), authors SHOULD declare it in `links:` regardless of whether they also mention it in prose. When a relation is a passing mention, in-prose alone is sufficient.

---

## 10. Status Lifecycle

**Deferred to a future version.** v1 does not define a structured status for features. Earlier drafts proposed a single `status` enum (`idea | specified | implemented`), but it conflated two orthogonal axes, *spec maturity* (is the intent captured and validated?) and *implementation state* (does the code exist?), and crowded into project-management territory that LiveSpec deliberately stays out of (§1).

Until a future RFC settles the model:

- Features MUST NOT carry a `status` field in their frontmatter.
- Teams that need to express workflow state SHOULD use external tooling (issue tracker, project board) and MAY reference it from the feature via tool-specific `x-*` extensions.
- The progress of work *inside* a feature is expressed by the checkbox states of its spec items (§8.1).

See §15 #015 for the design question being deferred.

---

## 11. Assets

Assets (images, wireframes, diagrams) are stored on disk and referenced from the feature's frontmatter.

### 11.1 Storage layout

A feature's assets live in an `assets/{feature-slug}/` subdirectory **next to the feature file**: at the same directory level, whether the feature sits directly under `features/` or under an area:

```
features/
├── {feature-slug}.md                 # Feature with no area
├── assets/{feature-slug}/
│   ├── wireframe.svg
│   └── flow-diagram.png
└── {area}/
    ├── {feature-slug}.md             # Feature grouped under an area
    └── assets/{feature-slug}/
        └── mockup.png
```

Asset files MAY be any media format.

### 11.2 Frontmatter declaration

Each asset MUST be declared in the feature's frontmatter:

```yaml
assets:
  - id: 019c5325-d453-760e-a970-396b261743b2
    type: wireframe
    title: Sign-in flow wireframe
    description: First draft of the sign-in modal interaction
    path: assets/sign-in/wireframe.svg
```

| Field         | Type   | Required | Description                                        |
|---------------|--------|----------|----------------------------------------------------|
| `id`          | string | Yes      | Stable identifier (UUID recommended).              |
| `type`        | enum   | Yes      | `wireframe`, `mockup`, `diagram`, `screenshot`, `reference` |
| `title`       | string | Yes      | Human-readable title.                              |
| `description` | string | No       | Short description for accessibility and search.    |
| `path`        | string | Yes      | Project-root-relative path to the asset file.      |

> **Future:** External asset URLs (Figma, Loom, Miro) are not in v1. See §15.

---

## 12. Modes

LiveSpec defines two modes of operation, declared by the `mode` field in `livespec.yaml` (see §4). The mode tightens (or relaxes) a set of conformance rules applied by linters and writers without changing the underlying grammar.

### 12.1 `loose` (default)

The default mode, optimized for individual contributors, small teams, and projects in active discovery. Designed to feel frictionless to newcomers.

- H2 section names MAY be anything; canonical names (Requirements, Assumptions, Questions, Issues, UX, Tech) are RECOMMENDED but not enforced.
- Spec items are identified by their inline syntax wherever they appear. An `ISS` item inside `## Requirements` is permitted (lint warning at most).
- User story format (§7.4) is SHOULD.
- Section ordering is unconstrained.
- Tools MUST preserve unrecognized H2 sections and their content on write (losslessness).

### 12.2 `strict`

Optimized for larger teams, enterprise contexts, and regulated environments where predictability and audit-readiness matter more than authoring flexibility. Strict mode is a **superset** of loose mode: every strict file is also a valid loose file, but not the inverse.

In strict mode, the following rules are upgraded:

| Rule                                                     | Loose      | Strict     |
|----------------------------------------------------------|------------|------------|
| H2 section names limited to canonical set                | SHOULD     | **MUST**   |
| Spec item type must match its containing section's type  | SHOULD     | **MUST**   |
| Section ordering follows canonical order                 | MAY        | **MUST**   |
| Every REQ has at least one AC                            | MAY        | **SHOULD** (warning) |

**Design rule.** Strict-mode rules MUST be *mechanical*: a writer or linter can decide compliance without judgment by inspecting the document's structure. Rules that require the author to interpret meaning (taxonomic choices, semantic classification, "right label" decisions) MUST NOT be promoted to MUST in strict mode: they generate bikeshedding and degrade to default-value reflexes, losing the signal they were meant to capture. Future additions to the strict-mode table above MUST satisfy this criterion.

### 12.3 Compatibility

Loose and strict are not separate dialects. A strict-mode project is always readable by a loose-mode reader (and vice-versa for read-only operations). The mode only affects **what tools enforce on write**.

A project MAY change mode over its lifetime (e.g. starting in loose, migrating to strict as the team matures). Tools migrating a project to strict mode SHOULD report all violations as a single batch rather than refusing the migration.

---

## 13. Format Versioning

LiveSpec follows semantic versioning at the format level:

- **Major** (`2.0.0`): breaking changes to file structure, frontmatter shape, or required fields.
- **Minor** (`1.1.0`): additive: new optional fields, new entity types, new spec item types.
- **Patch** (`1.0.1`): clarifications, typo fixes, no semantic change.

The `format_version` field in `livespec.yaml` declares the version a project targets. Tools MUST refuse to write files in a version they don't support and SHOULD warn (not refuse) when reading a newer minor version.

---

## 14. Conformance Levels

Tools claim conformance at one of three levels:

### Level 1: Reader
- MUST parse all required frontmatter fields without error
- MUST preserve unknown fields on read
- MAY ignore unknown spec item types

### Level 2: Writer
- All Level 1 requirements
- MUST preserve unknown frontmatter fields on write (round-trip safety)
- MUST emit valid markdown that other Level 1 tools can re-read
- MUST validate against the canonical JSON schemas
- MUST recognize the core concept taxonomy (§6.2): type slugs (`persona`, `pain_point`, `goal`, `principle`, `constraint`, `entity`, `glossary_term`, `ui_component`, `design_principle`, `ux_pattern`, `coding_standard`, `architecture_decision`, `external_system`), their canonical containing directories, and link resolution
- MUST preserve both forms of `links.feature` on write, untyped list and typed object (§7.2), without lossy conversion between them
- MUST recognize `livespec:` code markers (§9.4) when scanning source files and resolve them to spec items, including the multi-ID list form (`#REQ-1,REQ-2`)

### Level 3: Linter
- All Level 2 requirements
- MUST emit diagnostics for: broken links, invalid slugs, duplicate IDs, missing required fields, unknown spec item types, malformed checkboxes
- MUST emit diagnostics for broken `livespec:` code markers (feature file missing, or a listed spec item ID does not exist), and for malformed list payloads (whitespace inside the payload, or a listed ID carrying its own `feature-slug#` prefix)
- SHOULD emit diagnostics for resolution-note misuses (§8.1): multiple `→ ` lines on one item, or a `→ ` line on an open (`[ ]`) item
- SHOULD emit diagnostics for unknown relation names under `links.feature` (anything other than `requires`, `triggers`, `extends` in v1)
- SHOULD emit diagnostics for broken or ambiguous in-prose `[[ ]]` references (§9.5): unresolved slug, or shorthand slug matching two or more entities

A conformance test suite is published alongside this spec (TBD; see §15 #001).

---

## 15. Open Questions (RFC Candidates)

These are known limitations or undecided design points. Each will be addressed in a numbered RFC before v2.

| #   | Topic                                                                                          |
|-----|------------------------------------------------------------------------------------------------|
| 001 | Conformance test suite: fixtures and validation tooling                                       |
| 002 | Concept extension mechanism: how third parties register new types                             |
| 003 | Spec-item ID strategy: opaque IDs vs positional vs current human IDs                          |
| 004 | Bidirectional AC ↔ REQ linking: formal frontmatter or inline?                                 |
| 005 | UX_DIRECTION and TECH_DIRECTION as first-class block spec items                                |
| 006 | External assets: Figma, Loom, Miro URL support                                                |
| 007 | i18n: multilingual specs, translatable section names                                          |
| 008 | Deprecation lifecycle: `deprecated` status, archival conventions                              |
| 009 | Deeper feature-area nesting (>1 level)                                                         |
| 010 | Cross-project links: referencing entities in other LiveSpec repos                             |
| 011 | Slug-aliasing for safe renames                                                                 |
| 012 | Decision records: should ADRs be a first-class entity kind?                                   |
| 013 | Presets and manifest inheritance (`presets`, `extends`): packaging shared types and config    |
| 014 | Spec ↔ code verification semantics: standardizing coverage rules, drift detection, and agent-driven re-validation on top of the §9.4 marker syntax |
| 015 | Feature status: structured representation of spec maturity vs implementation state, if any     |
| 016 | Spec-item tagging mechanism: should LiveSpec introduce a typed tagging system for spec items (multi-axis: domain, concern, test-class, priority…), with controlled vocabularies declared in `livespec.yaml`? v1 deliberately ships without any tagging syntax to avoid locking in a single-slot design |
| 017 | Compiled artifacts: should LiveSpec standardize how tools generate aggregated views (per-type aggregations, AI-consumption bundles), or leave this entirely to tools? |
| 018 | Evolution-oriented feature relations: `requires`, `triggers`, `extends` are now in v1 (§7.2). Should `replaces` / `supersedes` (which describe evolution *over time*) be added in a future minor version, or are they project-management concerns excluded by §1? |
| 019 | Spec item body change tracking: should LiveSpec define a substantive-vs-editorial diff convention for spec item bodies, beyond what `git` provides? |

---

## Appendix A: Minimal Example

A complete minimal LiveSpec project:

```
my-app/
├── livespec.yaml
├── product/
│   └── persona/
│       └── power-user.md
└── features/
    └── search/
        └── full-text-search.md
```

**`livespec.yaml`**
```yaml
format_version: "1.0"
name: My App
```

**`product/persona/power-user.md`**
```markdown
---
tags: [primary]
---

# Power User

Heavy daily user who knows the product deeply and pushes its edges.
```

**`features/search/full-text-search.md`**
```markdown
---
links:
  persona: [power-user]
---

# Full-text Search

As a power user, I want to search across all my documents so that I can find content without remembering where I put it.

## Requirements

- [ ] REQ-1: Search bar visible in main navigation
  - [ ] AC-1.1: Search input renders in header on all pages
  - [ ] AC-1.2: Search remains accessible on mobile via icon-only collapsed mode
- [ ] REQ-2: Results returned within 300ms for queries under 50 chars
  - [ ] AC-2.1: P95 latency under 300ms measured against 10k-document corpus
  - [ ] AC-2.2: Query timeout shows fallback message after 2s
- [ ] REQ-3: Index updated within 5s of document creation

## Assumptions

- [ ] AS-1: Document corpus stays under 1M entries for v1: re-evaluate indexing strategy beyond that.

## Questions

- [ ] Q-1: Do we need search history per user, or is recent-results enough?

## UX

Search input uses inline autocomplete. Results show in a dropdown panel with keyboard navigation.

## Tech

Use PostgreSQL full-text search (tsvector) for v1. Reconsider with Meilisearch if latency budget is exceeded.
```

---

*This document is itself a living spec. See `rfcs/` for proposals in progress.*
