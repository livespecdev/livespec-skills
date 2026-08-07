# LiveSpec Cheatsheet

Condensed reference for humans and agents. The normative source is `SPEC.md`.

---

## Project structure

```
my-project/
├── livespec.yaml          # Manifest (required)
├── product/{type}/{slug}.md
├── ux/{type}/{slug}.md
├── tech/{type}/{slug}.md
└── features/[{area}/]{slug}.md
```

The four top-level folders are **fixed and exhaustive**. Extensions go through sub-types, never new top-level folders.

## Manifest

```yaml
format_version: "1.0"
name: My Project
description: optional
mode: loose      # or strict
```

## Concept types (core taxonomy)

| Location    | Type slug              | Purpose                                                    |
|-------------|------------------------|------------------------------------------------------------|
| `product/`  | `persona`              | User archetype.                                            |
| `product/`  | `pain_point`           | User or business pain the product addresses.               |
| `product/`  | `goal`                 | Outcome the product aims to deliver.                       |
| `product/`  | `principle`            | Guiding belief.                                            |
| `product/`  | `constraint`           | Standing limit or quantitative rule (incl. regulatory).    |
| `product/`  | `entity`               | Durable domain object (User, Order, Invoice…).             |
| `product/`  | `glossary_term`        | Term used consistently across specs.                       |
| `ux/`       | `ui_component`         | UI component with usage rules.                             |
| `ux/`       | `design_principle`     | Guiding belief for UX decisions.                           |
| `ux/`       | `ux_pattern`           | Reusable interaction or layout pattern.                    |
| `ux/`       | `screen`               | Durable interface surface (route, regions, states).        |
| `tech/`     | `coding_standard`      | Coding rule or convention.                                 |
| `tech/`     | `architecture_decision`| Architectural choice and rationale.                        |
| `tech/`     | `external_system`      | Third-party system the product integrates with.            |

Recommended extension namespaces: `{concern}_convention` (e.g. `api_convention`), `{concern}_pattern` for UX.

## Concept file anatomy

```markdown
---
tags: [optional]
links:
  {other-type-slug}: [slug-1, slug-2]
---

# Title

Single-paragraph summary (required).

## Author-defined section (optional)
Free-form markdown.
```

Frontmatter is optional. Omit entirely if empty.

## Feature file anatomy

```markdown
---
links:
  persona: [solo-user]
  pain_point: [forgetting-tasks]
  goal: [stay-organized]
  entity: [todo, list]
  constraint: [max-list-size]
  external_system: [stripe]
  feature:
    requires: [auth-sign-in]
    triggers: [send-reminder]
    extends: [export-csv]
assets:
  - id: 019c5325-d453-760e-a970-396b261743b2
    type: wireframe        # or mockup, diagram, screenshot, reference
    title: Sign-in flow
    description: Optional
    path: assets/sign-in/wireframe.svg
---

# Feature Title

Opening paragraph (required). Common idioms:
- User-facing: "As a {role}, I want {capability} so that {value}."
- Subsystem: "When {trigger}, the system {action} so that {outcome}."

## Requirements
- [ ] REQ-1: ...
  - [ ] AC-1.1: ...
## Assumptions
- [ ] AS-1: ...
## Questions
- [ ] Q-1: ...
## Issues
- [ ] ISS-1: ...
## UX
Free-form notes.
## Tech
Free-form notes.
```

In **loose mode** (default), section names and order are flexible. In **strict mode**, only the canonical sections above are allowed, in the listed order.

## Spec items

| Type  | Where                       | Form                                       |
|-------|-----------------------------|--------------------------------------------|
| `REQ` | top-level in `## Requirements` | `- [ ] REQ-1: body`                      |
| `AC`  | nested under its REQ (2 sp)  | `  - [ ] AC-1.1: body`                    |
| `AS`  | top-level in `## Assumptions`| `- [ ] AS-1: body`                        |
| `Q`   | top-level in `## Questions`  | `- [ ] Q-1: body`                          |
| `ISS` | top-level in `## Issues`     | `- [ ] ISS-1: body`                        |

Checkbox states: `[ ]` open, `[x]` done, `[-]` cancelled. AC nesting is **exactly one level**; deeper is invalid.

**IDs are file-scoped and immutable.** Never reuse or renumber.

Inline references: `[REQ-3]` (same file), `[feature-slug#REQ-3]` (cross-feature).

Resolution note (closed items only): start a continuation line with `→ `, one per item maximum.

```markdown
- [x] Q-1: Should we paginate?
  → Yes — by 50 with an opaque cursor. Decided 2026-03-12.
```

## Linking

- All structured links live in `links:` frontmatter, keyed by target type slug (always singular).
- Slug rule: `^[a-z0-9]+(-[a-z0-9]+)*$` (kebab-case ASCII).
- **Concepts may link to concepts** (e.g. `persona` → `pain_point`, `goal` → `persona`, `entity` → `entity`) just like features link to concepts. Same `links:` field, same resolution.
- **`feature:` is the only typed-relation key**: accepts either an untyped list **or** a typed object (`requires` / `triggers` / `extends`) — pick one form per file. Typed relations apply only between features.
- **Concept↔feature relations are carried by the concept type** — no need to type them. `constraint: [...]` already means *respects*, `entity: [...]` already means *manipulates*, `external_system: [...]` already means *integrates with*.

## In-prose references

Inside any concept or feature body, reference other entities with a wiki-style syntax:

| Form                          | Use when                                          |
|-------------------------------|---------------------------------------------------|
| `[[type:slug]]`               | Always valid. Explicitly typed.                   |
| `[[slug]]`                    | Shorthand. Only when `slug` is unambiguous.       |

Examples: `[[persona:solo-organizer]]`, `[[remind-on-due-date]]`, `[[max-list-size]]`.

For features, the type prefix is `feature`. For concepts, the type is the concept's type slug.

**In-prose vs frontmatter** — they have different purposes:
- `links:` frontmatter = structural relations (indexed, audited, presented in graphs)
- `[[ ]]` in prose = reading aids (contextual mentions, not exhaustive)

A reference may appear in prose without `links:`, and vice-versa. When a relation is *structurally meaningful*, declare it in `links:` regardless of whether you mention it in prose.

## Spec ↔ code linking

In any source file, in a host-language comment:

```js
// livespec: full-text-search#REQ-3
```

```python
# livespec: full-text-search#AC-1.2
```

```html
<!-- livespec: idempotency#REQ-1 -->
```

One marker MAY list several items of the **same** feature, comma-separated, no whitespace in the payload:

```js
// livespec: analyze-current-page#REQ-1,REQ-2,AC-3.2
```

Marker = literal `livespec:` + space(s) + `{feature-slug}#{spec-item-id}`, optionally followed by `,{spec-item-id}` for more items of that feature. Feature slugs are globally unique within `features/`, so the area is not in the marker: markers survive feature moves. Reference items in different features with one marker each.

## Anti-patterns

### Don't put work in the spec
- **No** features for migrations, upgrades, refactors — those are tasks. Document the *target state* as a REQ in an existing feature or a `tech/` concept.
- **No** `status` field, assignees, due dates, kanban states. Progress lives in checkbox states (`[ ]` → `[x]`) and external trackers.
- **No** "ephemeral implementation context" in `## Tech` ("I'm here, next step is X"). That belongs in PR descriptions or task trackers.

### Don't confuse types
- A document is **either** a feature **or** a concept — never both. `features/auth/two-factor.md` (ships) and `tech/security_pattern/two-factor.md` (standing pattern) may coexist; one file MUST NOT try to be both.
- If a "concept" you're writing has acceptance criteria, it is a feature — move it.
- If a feature states a rule that clearly applies elsewhere, extract it as a concept first, then link from the feature.

### Don't over-fragment
- Prefer **REQ first, extract to feature later** when in doubt about granularity.
- Prefer **start coarser, split later** for areas — easier than consolidating fragmented features.
- AC nesting beyond one level is invalid. Multiple REQs are the answer.

### Don't invent format
- No block-level constructs inside spec item bodies (headings, fenced code blocks, tables). Move them to `## Tech` / `## UX` and reference by ID.
- No new top-level folders. Extension types go inside the existing four.
- In-prose `[[ ]]` references resolve only to whole entities (concept/feature). To reference a spec item, use `[REQ-3]` (same file) or `[feature-slug#REQ-3]` (cross-feature).

### Don't break references
- Slugs SHOULD be stable. Renaming a file breaks inbound links.
- Spec item IDs are immutable. To remove an item without breaking inbound refs, mark `[-]` (cancelled), don't delete.
- Gaps in IDs (`REQ-1, REQ-3, REQ-7`) are valid. Don't renumber to close gaps.

---

When in doubt, the canonical reference is `SPEC.md`. The `examples/todo-app/` directory shows a complete project applying all of the above.
