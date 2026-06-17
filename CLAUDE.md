# CLAUDE.md

## The project

**livespec-tools** is the companion tooling repository for **LiveSpec**, the open file format for product specifications (format spec lives at `/Users/eric/Dev/livespec`, canonical document `SPEC.md`, home `https://livespec.dev`).

This repo hosts **Claude Code extensions** (skills, subagents, and a packaged plugin) that let humans and agents author and maintain LiveSpec specs **directly on the local files in the user's git repository**. No backend, no API, no MCP server, no proprietary application.

It is the *forward authoring* toolchain for LiveSpec: scope, specify, frame, implement, and keep specs in sync with code, all on plain markdown files versioned in git.

> Reverse-engineering an existing codebase into a LiveSpec project is **out of scope** for this repo. That backward pipeline lives in the separate `reverse-livespec` tooling (`/Users/eric/Dev/reverse-livespec`), which *produces* a `livespec/` project that the skills here then maintain.

## The architectural shift (read this first)

These skills are a port of a Territory-backed workflow (`/Users/eric/Dev/topo`). The single most important change:

| Territory (old) | livespec-tools (new) |
|---|---|
| Source of truth = Territory server, reached via `mcp__topo__*` MCP tools | Source of truth = **LiveSpec markdown files** in the user's repo |
| `sync_product_context` pulls context into `.territory/` | Skills **read the files directly**; no sync step, no `.territory/` |
| `create_feature`, `update_feature`, `add_spec_items`, `update_spec_items` | **Read/Write/Edit on `features/**/*.md`** |
| `suggest_context_item`, `suggest_feature` (human review queue in the UI) | **Propose edits to `product/`, `ux/`, `tech/` files**; the human reviews via git diff / PR |
| Feature `status: IDEA|SPECIFIED|IMPLEMENTED` | **No status.** LiveSpec §10 defines none. Progress = checkbox state of spec items (§8.1) |
| Delivery `batch` (ordering, readiness) | **Dropped entirely.** Batches are pure Territory work-tracking with no LiveSpec equivalent. Sequencing a body of work lives in external tools (git branches, issue tracker), not in this toolchain |

**Corollary: drop the "work" layer.** LiveSpec describes the software, not the work on it (`SPEC.md` §1). Anything that answers *"how is the work going?"* (assignees, due dates, kanban states, batch ordering and readiness, spec maturity enums) MUST NOT be written into spec files, nor reconstructed elsewhere by these skills. Where the old Territory skill did this, the port removes it: that concern belongs to external work-tracking tools.

## Locating the project

A LiveSpec project is the directory containing a `livespec.yaml` (`SPEC.md` §3). Skills MUST locate the project root by searching for `livespec.yaml`, honoring the common patterns from §3.1 (`./`, `docs/livespec/`, `.livespec/`, `specs/`). A repo MAY contain several projects (monorepo); each `livespec.yaml` is an independent root with its own slug namespace. Never assume a fixed path.

## The format is the contract

The skills write files; `SPEC.md` defines what valid files look like. Non-negotiables when emitting LiveSpec:

- **Four fixed top-level folders**: `product/`, `ux/`, `tech/`, `features/`. No others (§3). New concerns become extension *types* inside these four, never new folders.
- **Concept files**: `{product|ux|tech}/{type}/{slug}.md`, type slug = directory name = link key (§6.1). Core taxonomy in §6.2.
- **Feature files**: `features/{slug}.md` or `features/{area}/{slug}.md` (§7.1). Open with a single summary paragraph (§7.4).
- **Spec items**: GFM checkboxes `- [ ] REQ-1: ...`, ACs nested 2 spaces under their REQ, types `REQ / AC / AS / Q / ISS` (§8). IDs are **file-scoped, immutable, never renumbered**; gaps are valid; cancel with `[-]`, don't delete (§8.3).
- **Links**: frontmatter `links:` keyed by singular type slug (§9.2). In-prose `[[type:slug]]` are reading aids, not a substitute (§9.5).
- **Spec ↔ code**: the `livespec: {feature-slug}#{spec-item-id}` comment marker (§9.4) is how "live" is mechanical. `implement-*` and `sync-*` skills place and reconcile these markers.
- **Losslessness**: when editing an existing file, preserve unknown frontmatter keys (`x-*`), unrecognized H2 sections, and existing IDs on write (Level 2, §14). Never emit an empty frontmatter block (§5).
- **Modes**: read `mode` from `livespec.yaml`. In `loose` (default), canonical section names are RECOMMENDED; in `strict`, section names/order/placement are enforced (§12). Skills SHOULD warn, not silently rewrite, on strict violations.

When unsure whether something is a concept, a feature, or a spec item, apply the decision framework in `SPEC.md` §6.5.

## Repository layout

Packaged as a single Claude Code plugin at the repo root (installable via `claude marketplace add`), following the standard plugin layout:

```
livespec-tools/
├── CLAUDE.md                  # this file (working instructions for the repo)
├── README.md                  # public-facing intro (TBD)
├── LICENSE                    # permissive (Apache-2.0 planned)
├── .claude-plugin/
│   ├── marketplace.json       # lists this repo as a marketplace
│   └── plugin.json            # plugin metadata (name, version, description)
├── skills/
│   └── {skill-name}/SKILL.md  # one folder per skill
├── agents/
│   └── {agent-name}.md        # subagent definitions (local-file tools only)
├── reference/                 # vendored format spec, bundled with the plugin
│   ├── SPEC.md                # byte-identical copy of upstream SPEC.md (pinned version)
│   └── CHEATSHEET.md          # condensed reference
├── examples/
│   └── sample-project/        # minimal valid LiveSpec project (dogfooding fixture)
└── commands/                  # optional slash commands (TBD)
```

**Bundled format reference.** Skills and agents cite `SPEC.md §N` constantly, and they resolve those citations against the **vendored** copy in `reference/`, not against an external clone. Reference it with relative paths (`../../reference/SPEC.md` from a skill, `../reference/SPEC.md` from an agent): `${CLAUDE_PLUGIN_ROOT}` does NOT expand in skill or agent prose (only in hook, MCP, and LSP config), so it MUST NOT be used there. The copy is pinned to the version in `plugin.json`; when the format bumps, re-vendor from the `livespec` repo (`cp .../livespec/{SPEC,CHEATSHEET}.md reference/`) and update the pin. See `reference/README.md`.

A skill is a folder under `skills/` with a `SKILL.md` whose YAML frontmatter carries `name`, `description` (with trigger phrases), and optional `argument-hint`. Subagents are single markdown files under `agents/` with frontmatter `name`, `description`, `tools`. **Agent tool lists MUST NOT reference `mcp__topo__*`**: use `Read`, `Glob`, `Grep`, `Edit`, `Write`, `AskUserQuestion` instead.

## The skill suite (port plan)

Recognizable names from the Territory workflow, re-grounded on local files. Build incrementally; each lands as its own `skills/{name}/SKILL.md`.

| Skill | Purpose | Key change vs Territory |
|---|---|---|
| `livespec-context` | Map the project at session start; bridge spec files ↔ codebase reality. | Merges old `load-context` + `territory-context`. Reads files; no sync. |
| `scope-features` | Decompose natural-language intent into proposed features (and concepts to extract). | Was `scope-work`. **Batches dropped** (pure Territory); outputs a plan of `[NEW]/[UPDATE]` feature files to write, then writes them. |
| `specify-feature` | Author/refine a feature: summary, REQs, nested ACs, AS, Q, ISS. | Was `specify-features`. Writes the `.md` directly per §7–§8. |
| `ux-framing` | Frame UX into `## UX` notes (and future `UX_DIRECTION`, §15 #005). | Reads `ux/` concepts instead of `.territory/ux.md`. |
| `tech-framing` | Frame technical approach into `## Tech` notes; explore the codebase. | Reads `tech/` concepts; writes `## Tech`. |
| `implement-feature` | Work through ACs, write code, place `livespec:` markers (§9.4). | No status flips. Checks `[x]` ACs as they pass; markers anchor code. |
| `finalize-work` | Tests, CI/quality gate, commit. | Delegates spec reconciliation to `sync-spec`. |
| `sync-spec` | Reconcile spec files with what was built: check ACs, add resolution notes (§8.1 `→`), add `## Tech` notes, promote discovered standing rules to concepts. | Was `sync-back`. **Edits local files** instead of pushing to a server. |

Subagents to port (strip MCP, point at files): `specifier`, `ux-framer`, `tech-framer`, `architect`, `qa`, plus a `strategist` if useful. Source versions in `~/.claude/agents/*.md`.

> **Validation is deferred.** A deterministic LiveSpec validator (Level-3 conformance per §14) is intentionally *not* part of this toolchain for now. When it is built, the reference validator belongs in the `livespec` repo itself (it is constitutive of the standard), and a thin skill here would merely wrap it.

## Working principles for this repo

1. **Interoperability first.** Every skill must produce files a third-party LiveSpec tool (one that knows nothing about Claude Code) can read. If a behavior only works because our skills agree on it out-of-band, it is a bug. Anchor every rule to a `SPEC.md` section.
2. **Files are the source of truth.** No hidden state. A skill's output is a git diff a human can review. Prefer `Edit` over `Write` to keep diffs tight and preserve unknown content.
3. **Spec, not work.** Never write work-tracking into `livespec/`. If a skill needs scratch state (a plan, a backlog), keep it in a gitignorable workspace dir, clearly outside the spec.
4. **Respect modes and conformance.** Read the manifest `mode`; warn rather than rewrite; preserve unknown fields and sections (losslessness).
5. **Propose, don't impose, on concepts.** Edits to `product/`, `ux/`, `tech/` are product decisions: surface them for human review (diff/PR), mirroring the old `suggest_*` intent.
6. **Reuse the format's own guidance.** `SPEC.md` §6.5 (concept vs feature vs spec item) and §7.5 (granularity) are the editorial rules; skills should cite them, not reinvent heuristics.
7. **Don't duplicate `reverse-livespec`.** This repo authors forward. If asked to reverse-engineer a codebase, defer to that tool.

## Style preferences

- Skill/agent prose: direct and operational. Avoid AI tells: **no em dashes**, avoid the "it's X, not Y" filler pattern (consistent with the LiveSpec repo's house style).
- When a skill writes spec content, follow the LiveSpec style: markdown tables for contracts, concrete complete examples over abstract ones.
- Cite `SPEC.md §N` in skill instructions wherever a rule comes from the format, so skills stay traceable to the spec as it evolves.

### Commits

Commits MUST NOT mention Claude, Claude Code, or any AI agent as committer, author, or contributor. No `Co-Authored-By: Claude ...` trailers or "Generated with" lines. The human author is the sole committer of record. (Same rule as the LiveSpec repo.)

## Status

Bootstrapping. CLAUDE.md first; plugin manifest, skills, and agents to follow. The LiveSpec format itself is `v1.0.0-draft.2` and not frozen, so skills SHOULD pin the `SPEC.md` sections they rely on and expect churn until `1.0.0` is locked.

### Suggested next steps

1. Scaffold `.claude-plugin/{plugin.json,marketplace.json}` + `LICENSE` + `README.md`.
2. Port `livespec-context` first (every other skill depends on locating and reading the project).
3. Port the authoring chain: `scope-features` → `specify-feature` → framing (`ux-framing`, `tech-framing`) → `implement-feature` → `finalize-work` → `sync-spec`.
4. Port the subagents, stripping all `mcp__topo__*` tools.
