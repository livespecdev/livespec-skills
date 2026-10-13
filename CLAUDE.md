# CLAUDE.md

## The project

**livespec-skills** is the companion tooling repository (it ships the Claude Code plugin `livespec`) for **LiveSpec**, the open file format for product specifications (format spec lives in the separate `livespec` repository, canonical document `SPEC.md`, home `https://livespec.dev`).

This repo hosts **Claude Code extensions** (skills, subagents, and a packaged plugin) that let humans and agents author and maintain LiveSpec specs **directly on the local files in the user's git repository**. No backend, no API, no MCP server, no proprietary application.

It is the *forward authoring* toolchain for LiveSpec: scope, specify, frame, implement, and keep specs in sync with code, all on plain markdown files versioned in git.

> Reverse-engineering an existing codebase into a LiveSpec project is **out of scope** for this repo. That backward pipeline lives in the separate `reverse-livespec` tooling, which *produces* a `livespec/` project that the skills here then maintain.

## Core model (read this first)

- **Source of truth = the LiveSpec markdown files** in the user's repo. No backend, no server, no sync step, no cache directory: skills read and write the files directly.
- **Files, not an API.** Feature and concept edits are `Read`/`Write`/`Edit` on `features/**/*.md` and `{product|ux|tech}/**/*.md`.
- **Propose, don't impose.** Edits to `product/`, `ux/`, `tech/` are product decisions: skills propose them, and the human reviews via git diff / PR.
- **No status field.** LiveSpec §10 defines none. Progress is the checkbox state of spec items (§8.1).
- **No work-tracking layer.** LiveSpec describes the software, not the work on it (`SPEC.md` §1). Anything that answers *"how is the work going?"* (assignees, due dates, kanban states, delivery batches/ordering/readiness, spec maturity enums) MUST NOT be written into spec files, nor reconstructed elsewhere by these skills. That concern belongs to external work-tracking tools (issue tracker, git branches).

## Locating the project

A LiveSpec project is the directory containing a manifest, `product-spec.yaml` or `livespec.yaml` (`SPEC.md` §3, §4). The names are equivalent. Skills MUST locate the project root by searching for either name, honoring the common patterns from §3.1 (`./`, `docs/spec/`, `.spec/`, `specs/`, and the older `docs/livespec/`, `.livespec/`). A repo MAY contain several projects (monorepo); each `livespec.yaml` is an independent root with its own slug namespace. Never assume a fixed path.

## The format is the contract

The skills write files; `SPEC.md` defines what valid files look like. Non-negotiables when emitting LiveSpec:

- **Four fixed top-level folders**: `product/`, `ux/`, `tech/`, `features/`. No others (§3). New concerns become extension *types* inside these four, never new folders.
- **Concept files**: `{product|ux|tech}/{type}/{slug}.md`, type slug = directory name = link key (§6.1). Core taxonomy in §6.2.
- **Feature files**: `features/{slug}.md` or `features/{area}/{slug}.md` (§7.1). Open with a single summary paragraph (§7.4).
- **Spec items**: GFM checkboxes `- [ ] REQ-1: ...`, ACs nested 2 spaces under their REQ, types `REQ / AC / AS / Q / LIM / UX / TECH` (§8). `UX` and `TECH` are directions (how this feature is built), separated from REQ/AC (what it does) by the substitution test in §6.5. IDs are **file-scoped, immutable, never renumbered**; gaps are valid; cancel with `[-]`, don't delete (§8.3).
- **Links**: frontmatter `links:` keyed by singular type slug (§9.2). In-prose `[[type:slug]]` are reading aids, not a substitute (§9.5).
- **Spec ↔ code**: the `implements: {feature-slug}#{spec-item-id}` comment marker, with `see-spec:` for items the code depends on without realizing (§9.4), is how "live" is mechanical. Readers also accept the legacy `livespec:` verb; skills never write it. `implement-*` and `sync-*` skills place and reconcile these markers.
- **Losslessness**: when editing an existing file, preserve unknown frontmatter keys (`x-*`), unrecognized H2 sections, and existing IDs on write (Level 2, §14). Never emit an empty frontmatter block (§5).
- **Modes**: read `mode` from the manifest. In `loose` (default), canonical section names are RECOMMENDED; in `strict`, section names/order/placement are enforced (§12). Skills SHOULD warn, not silently rewrite, on strict violations.

When unsure whether something is a concept, a feature, or a spec item, apply the decision framework in `SPEC.md` §6.5.

## Repository layout

Packaged as a single Claude Code plugin at the repo root (installable via `claude marketplace add`), following the standard plugin layout:

```
livespec-skills/
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
├── scripts/                   # deterministic helpers behind the check-* skills
│   ├── livespec.py            # shared parser (stdlib only, tolerant, read-only)
│   ├── check_spec.py          # internal spec consistency
│   └── check_drift.py         # spec ↔ code coherence via code markers
├── reference/                 # vendored format spec, bundled with the plugin
│   ├── SPEC.md                # byte-identical copy of upstream SPEC.md (pinned version)
│   └── CHEATSHEET.md          # condensed reference
├── examples/
│   └── sample-project/        # minimal valid LiveSpec project (dogfooding fixture)
└── commands/                  # optional slash commands (TBD)
```

**Bundled format reference.** Skills and agents cite `SPEC.md §N` constantly, and they resolve those citations against the **vendored** copy in `reference/`, not against an external clone. Reference it with relative paths (`../../reference/SPEC.md` from a skill, `../reference/SPEC.md` from an agent): `${CLAUDE_PLUGIN_ROOT}` does NOT expand in skill or agent prose (only in hook, MCP, and LSP config), so it MUST NOT be used there. The copy is pinned to the version in `plugin.json`; when the format bumps, re-vendor from the `livespec` repo (`cp .../livespec/{SPEC,CHEATSHEET}.md reference/`) and update the pin. See `reference/README.md`.

A skill is a folder under `skills/` with a `SKILL.md` whose YAML frontmatter carries `name`, `description` (with trigger phrases), and optional `argument-hint`. Subagents are single markdown files under `agents/` with frontmatter `name`, `description`, `tools`. **Agent tool lists MUST NOT reference any MCP server**: use `Read`, `Glob`, `Grep`, `Edit`, `Write`, `AskUserQuestion` instead.

## The skill suite

| Skill | Purpose |
|---|---|
| `spec-context` | Map the project at session start; bridge spec files ↔ codebase reality. |
| `scope-features` | Decompose natural-language intent into proposed features (and concepts to extract), then write them. |
| `specify-feature` | Author/refine a feature: summary, REQs, nested ACs, AS, Q, LIM. Writes the `.md` directly per §7–§8. |
| `frame-ux` | Frame UX into `UX` items + supporting prose under `## UX`. Reads `ux/` concepts. |
| `frame-tech` | Frame technical approach into `TECH` items + supporting prose under `## Tech`; explore the codebase; reads `tech/` concepts. |
| `implement-feature` | Work through ACs, write code, place `implements:` / `see-spec:` markers (§9.4). Checks `[x]` ACs as they pass; markers anchor code. |
| `finalize-feature` | Tests, CI/quality gate, commit. Delegates spec reconciliation to `sync-spec`. |
| `sync-spec` | Reconcile spec files with what was built: check ACs, add resolution notes (§8.1 `→`), flip or supersede `UX`/`TECH` directions, promote discovered standing rules to concepts. |
| `check-drift` | Report where intent and code disagree: `[x]` items with no marker, dangling markers, code anchored to open or cancelled items. Read-only. |
| `check-spec` | Report internal spec inconsistencies: features with no REQ, duplicate IDs, broken links, orphan concepts. Read-only, spec files only. |

Subagents: `specifier`, `ux-framer`, `tech-framer`, `architect`, `qa`, `strategist`.

> **Conformance validation is still deferred.** A deterministic LiveSpec validator (Level-3 per §14) is intentionally *not* part of this toolchain. When it is built, the reference validator belongs in the `livespec` repo itself (it is constitutive of the standard), and a thin skill here would merely wrap it.
>
> The `check-*` skills are **not** that validator, and the boundary must stay visible in their prose. They answer two questions the format deliberately leaves to tooling: editorial coherence across a project's files, and spec ↔ code coherence (§9.4 explicitly puts coverage rules and drift detection out of scope for the format). `check-drift` cannot live in the `livespec` repo at all: it needs the user's codebase.

### The `scripts/` layer

The `check-*` skills are backed by scripts rather than a reading pass, because their checks are mechanical and a reading pass does not scale past a few dozen features. Rules for anything added there:

- **Python 3 stdlib only.** The plugin cannot install dependencies in the user's environment. `scripts/livespec.py` is the shared parser (tolerant: it never raises on malformed input); the checks import it, they do not re-parse.
- **Read-only, always.** A script in this repo never writes to a LiveSpec project. Writing is the skills' job, through `Edit`, and stays reviewable as a diff.
- **Exit 0 even with findings.** These are diagnostics. A non-zero exit turns them into a CI gate, which reintroduces the work-tracking layer through the back door.
- **`--json` on every script.** The script constates, the model interprets. Findings carry a `spec_ref` (`§N`) so a skill can always show the user the rule behind a finding.
- **Never assume a project path.** Use `find_projects()` / `resolve_project()`; a repo may hold several independent projects (§3.1).

## Working principles for this repo

1. **Interoperability first.** Every skill must produce files a third-party LiveSpec tool (one that knows nothing about Claude Code) can read. If a behavior only works because our skills agree on it out-of-band, it is a bug. Anchor every rule to a `SPEC.md` section.
2. **Files are the source of truth.** No hidden state. A skill's output is a git diff a human can review. Prefer `Edit` over `Write` to keep diffs tight and preserve unknown content.
3. **Spec, not work.** Never write work-tracking into `livespec/`. If a skill needs scratch state (a plan, a backlog), keep it in a gitignorable workspace dir, clearly outside the spec.
4. **Respect modes and conformance.** Read the manifest `mode`; warn rather than rewrite; preserve unknown fields and sections (losslessness).
5. **Propose, don't impose, on concepts.** Edits to `product/`, `ux/`, `tech/` are product decisions: surface them for human review (diff/PR).
6. **Reuse the format's own guidance.** `SPEC.md` §6.5 (concept vs feature vs spec item) and §7.5 (granularity) are the editorial rules; skills should cite them, not reinvent heuristics.
7. **Don't duplicate `reverse-livespec`.** This repo authors forward. If asked to reverse-engineer a codebase, defer to that tool.

## Style preferences

- Skill/agent prose: direct and operational. Avoid AI tells: **no em dashes**, avoid the "it's X, not Y" filler pattern (consistent with the LiveSpec repo's house style).
- **Keep the format's name out of skill and agent prose**, descriptions included: say "the spec", "the spec files", "the format". A team MUST be able to adopt these skills without the brand showing up in what the agent tells them. The name stays only where it is a technical identifier (`livespec.yaml`, the legacy `livespec:` verb, the `livespec` plugin namespace, the `reverse-livespec` tool).
- When a skill writes spec content, follow the LiveSpec style: markdown tables for contracts, concrete complete examples over abstract ones.
- Cite `SPEC.md §N` in skill instructions wherever a rule comes from the format, so skills stay traceable to the spec as it evolves.

### Commits

Commits MUST NOT mention Claude, Claude Code, or any AI agent as committer, author, or contributor. No `Co-Authored-By: Claude ...` trailers or "Generated with" lines. The human author is the sole committer of record. (Same rule as the LiveSpec repo.)

### Releasing (bump the version, or nothing ships)

**Any commit that changes what the plugin does MUST bump `version` in `.claude-plugin/plugin.json` before it is pushed.** Pushing skill or script changes without a bump is a silent no-op for every machine that already installed the previous version.

The reason is mechanical: Claude Code materializes an installed plugin in a cache keyed by version, `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/`, and records the resolved `version` and `gitCommitSha` in `~/.claude/plugins/installed_plugins.json`. When the declared version is unchanged, the target path already exists and `claude plugin update` has nothing to do, however many commits the repository has moved on.

This does not show up on a machine whose marketplace entry is a local `directory` source pointing at this working copy (`known_marketplaces.json`): there, edits appear in the next session with no install step at all. It only bites on machines that installed from the GitHub remote, which is exactly where it is hardest to notice. Do not use "it works on my machine" as evidence that a release shipped.

Release checklist:

1. Bump `version` in `.claude-plugin/plugin.json`. Semver on `0.x`: new skill, new script, or changed skill behavior is a minor; wording and bug fixes are a patch. `marketplace.json` currently declares no version for the entry, so there is nothing to keep in sync there. If one is ever added, the two MUST agree, and `claude plugin tag` fails the release when they do not.
2. `claude plugin validate .`
3. Commit the bump, then push `main`.
4. `claude plugin tag --push` to cut the `livespec--v{version}` git tag.

On the consuming machine, refreshing the marketplace first is what picks up new commits; updating the plugin alone can compare against a stale clone:

```bash
claude plugin marketplace update livespec
claude plugin update livespec
```

Then restart Claude Code: the update is staged, not applied live. Verify with `claude plugin list` (or the recorded `gitCommitSha` in `installed_plugins.json`) rather than assuming.

## Status

The LiveSpec format itself is `v0.1.0-draft` and not frozen, so skills SHOULD pin the `SPEC.md` sections they rely on and expect churn until `1.0.0` is locked.
