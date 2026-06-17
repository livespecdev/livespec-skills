# Porting brief: LiveSpec authoring skills

**Audience:** an agent starting fresh, with no memory of prior conversations, tasked with building the Claude Code skills for this repo.

**Goal:** port a Territory-backed product-spec workflow into a set of Claude Code skills that operate **directly on local LiveSpec markdown files** in the user's git repo. No backend, no MCP server, no `.territory/` sync.

Read this whole file once, then `CLAUDE.md`, before writing anything.

---

## 0. Prime directive

Every skill reads and writes plain LiveSpec files and produces a **git diff a human can review**. If a behavior only works because our skills agree on something out-of-band, it is wrong: anchor every rule to a section of the format spec. The format spec is authoritative; these skills are just one conformant tool among potential others.

---

## 1. Load this context before writing

In order:

1. **`./CLAUDE.md`** (this repo): the architecture, the Territory→files shift, the format contract, the layout, the skill suite table. Non-negotiable rules live there.
2. **`/Users/eric/Dev/livespec/SPEC.md`**: the LiveSpec format (`v1.0.0-draft.2`). You will cite its sections (`§3`, `§6`, `§7`, `§8`, `§9`, `§12`, `§14`) constantly. Also skim `IDEAS.md` and `spec_review.md` in that repo for rationale.
3. **The source skills** (what you are porting), at `~/.claude/skills/`:
   `load-context`, `scope-work`, `specify-features`, `ux-framing`, `tech-framing`, `implement-features`, `finalize-work`, `sync-back`, `territory-context`. Each is a `SKILL.md`. Read the source before porting its successor.
4. **`/Users/eric/Dev/reverse-livespec/`**: the existing LiveSpec tool that *already* works on local files (it reverse-engineers a codebase into a `livespec/` project). It is your reference for local-file patterns and the **out-of-scope boundary**: this repo authors forward, reverse-livespec goes backward. Do not duplicate it.
5. **The source subagents** at `~/.claude/agents/*.md` (`specifier`, `ux-framer`, `tech-framer`, `architect`, `qa`, `strategist`).

---

## 2. Decisions already made (do not relitigate)

| Decision | Rationale |
|---|---|
| Source of truth = LiveSpec files located via `livespec.yaml` (`SPEC.md` §3, §3.1). | The whole point of the port. |
| No MCP. Replace every `mcp__topo__*` call with file I/O (`Read`/`Glob`/`Grep`/`Edit`/`Write`). | No Territory dependency. |
| **Feature `status` is dropped.** LiveSpec defines none (`SPEC.md` §10). Progress = checkbox state of spec items (§8.1). | "The software, not the work" (§1). |
| **Batches are dropped entirely.** Pure Territory work-tracking, no LiveSpec equivalent. Do not reconstruct them anywhere. | Confirmed by the maintainer. |
| **A deterministic validator/linter is deferred.** Not part of this toolchain now. When built, the reference validator belongs in the `livespec` repo (it is constitutive of the standard); a skill here would only wrap it. | Keep scope tight; avoid freezing the format prematurely. |
| Package as a **single Claude Code plugin** at the repo root. | Installable via `claude marketplace add`. |
| House style: no em dashes, avoid the "it's X, not Y" pattern. Commits never mention AI authorship. | Consistency with the LiveSpec repo. |

---

## 3. The porting recipe (apply to each skill)

1. **Read the source `SKILL.md` in full.** Note its phases, its gates, its human-interaction points.
2. **List every `mcp__topo__*` call** it makes (directly or implied) and map each to a file operation using the table in §4.
3. **Strip the work layer.** Remove anything touching `status`, batches, readiness, assignees, "mark SPECIFIED/IMPLEMENTED". Progress is expressed only by spec-item checkboxes.
4. **Re-ground reads.** Territory context (`personas`, `constraints`, `ux`, `tech`) now comes from `product/`, `ux/`, `tech/` concept files, not `.territory/*.md`.
5. **Re-ground writes.** Features become `features/**/*.md`; concept suggestions become proposed edits to `product|ux|tech/{type}/{slug}.md`, surfaced for human review via diff, not a suggestion queue.
6. **Preserve the format contract** (`CLAUDE.md` "The format is the contract"): immutable IDs, 2-space AC nesting, losslessness, `livespec:` markers (§9.4), mode awareness (§12). Prefer `Edit` over `Write` to keep diffs tight and preserve unknown sections/fields.
7. **Cite `SPEC.md §N`** in the skill text wherever a rule comes from the format, so skills stay traceable as the spec evolves.
8. **Keep the skill's recognizable shape.** Same overall purpose and phases as the Territory source; only the substrate changes. The maintainer wants "about the same workflow."
9. **Dogfood** against the test fixture (§7). The skill's output must be valid per `SPEC.md`.
10. **No AI-authorship mentions** in any committed content.

---

## 4. Canonical `mcp__topo__*` → local-file mapping

This is the heart of the port. Reuse it across all skills.

| Territory MCP tool | Local-file replacement |
|---|---|
| `sync_product_context` | None. Locate the project root (find nearest `livespec.yaml`, §3.1), then `Glob`/`Read` `product/`, `ux/`, `tech/`, `features/` directly. |
| `search` | `Grep` across the project (feature bodies, spec-item text, concept summaries). |
| `list_features` | `Glob features/**/*.md`; the slug is the filename, the area is the path between `features/` and the file (§7.1). |
| `get_feature` | `Read features/**/{slug}.md`; parse frontmatter `links`/`assets` and the body spec items (§7, §8). |
| `list_context_items` (by type) | `Glob {product|ux|tech}/{type}/*.md`; type slug = directory name (§6.1, §6.2). |
| `get_context_item` | `Read {dir}/{type}/{slug}.md`. |
| `list_feature_areas` | Derive from `features/` subdirectory names. |
| `create_feature` / `create_features` | `Write features/{area}/{slug}.md` with summary paragraph (§7.4) + sections (§7.3). New file = the "create". |
| `update_feature` | `Edit` the feature file (links in frontmatter §9.2; notes into `## UX` / `## Tech` §7.3). No status field exists. |
| `add_spec_items` | `Edit` the body to append `REQ/AC/AS/Q/ISS` items with correct syntax, indentation, and next-in-sequence IDs (§8.1, §8.3). |
| `update_spec_items` | `Edit` the relevant checkbox (`[ ]`→`[x]`/`[-]`), optionally add a resolution note (`→ `, §8.1). Never renumber IDs (§8.3). |
| `suggest_context_item(s)` | Propose a new concept file (or edit) under `product|ux|tech/`; present it as a diff for human review. Mirrors the "human reviews product decisions" intent. |
| `suggest_feature(s)` / `suggest_feature_update` | Propose the feature file (or edit) and surface for review rather than writing silently when it is a genuine product decision. |
| `create_batch` / `update_batch` / `list_batches` / `get_batch` | **Removed.** Batches do not exist in LiveSpec. |

When assigning new spec-item IDs: IDs are file-scoped, human-readable integers, **immutable**, gaps allowed; assign the next free integer in that H2 section, never reuse or renumber (§8.3).

---

## 5. SKILL.md authoring conventions

Each skill is a folder `skills/{name}/SKILL.md`. Frontmatter:

```yaml
---
name: {kebab-case-name}
description: |
  One to three sentences. State what it does, then the trigger phrases ("Use when ...")
  and the boundaries ("Not for ...") so the dispatcher routes correctly.
argument-hint: <optional: expected argument shape>
---
```

- **Naming**: use the names in the suite table below. Verbs match the action.
- **Description**: include explicit trigger phrases and "Not for ..." exclusions, like the Territory sources do. The dispatcher selects skills by description.
- **Body**: operational prose. Phases as headings. Cite `SPEC.md §N`. Concrete examples (full frontmatter + body) over abstract ones.
- **Subagents**: a skill MAY delegate heavy work to a subagent in `agents/`. Subagent frontmatter lists `tools:` but **MUST NOT** include any `mcp__topo__*` tool. Use `Read`, `Glob`, `Grep`, `Edit`, `Write`, `AskUserQuestion`.
- **Human gates**: keep the source's review points. Product decisions (new concepts, new features) are surfaced for human confirmation, not silently committed.

---

## 6. Work list (ordered)

### Phase A: scaffold the plugin
- [ ] `.claude-plugin/plugin.json` (name `livespec-tools`, version `0.1.0`, description, license `Apache-2.0`).
- [ ] `.claude-plugin/marketplace.json` (lists this repo as a marketplace, plugin source `.`).
- [ ] `LICENSE` (Apache-2.0).
- [ ] `README.md` (public intro: what livespec-tools is, install, the skill list).
- [ ] `examples/sample-project/` test fixture (see §7).

### Phase B: skills (in this order)

Build `livespec-context` first; everything depends on locating and reading the project. Then the authoring chain in delivery order.

| # | Skill | Source | Purpose | Writes | Key SPEC refs |
|---|---|---|---|---|---|
| 1 | `livespec-context` | `load-context` + `territory-context` | Locate the project (`livespec.yaml`), map concepts + features, bridge spec ↔ codebase. Read-only orientation. | nothing | §3, §3.1, §6, §7 |
| 2 | `scope-features` | `scope-work` | Decompose intent into proposed `[NEW]/[UPDATE]` features (and concepts worth extracting), iterate with the user, then write the files. **No batches.** | `features/**/*.md`, maybe `product|ux|tech/**` | §6.5, §7, §7.5 |
| 3 | `specify-feature` | `specify-features` | Author/refine one feature: summary, REQs, nested ACs, AS, Q, ISS. | one feature file | §7.3, §7.4, §8 |
| 4 | `ux-framing` | `ux-framing` | Frame UX into `## UX` notes; read `ux/` concepts; optionally produce asset files (§11). | feature `## UX`, `assets/` | §7.3, §9, §11 |
| 5 | `tech-framing` | `tech-framing` | Frame technical approach into `## Tech` notes; explore the codebase; read `tech/` concepts. | feature `## Tech` | §7.3, §9 |
| 6 | `implement-feature` | `implement-features` | Work through ACs, write code, place `livespec:` markers in source (§9.4). Check `[x]` ACs as they pass. Auto-invoke framing skills if `## UX`/`## Tech` missing. **No status flips.** | code + markers; checks ACs | §8.1, §9.4 |
| 7 | `finalize-work` | `finalize-work` | Tests, CI/quality gate, commit. Delegate spec reconciliation to `sync-spec`. | tests, commit | n/a |
| 8 | `sync-spec` | `sync-back` | Reconcile spec with what was built: check ACs, add resolution notes (`→`, §8.1), add `## Tech` notes, promote discovered standing rules to concepts. **Edits local files**, no server push. | feature edits, new concepts | §8.1, §6.5, §9.4 |

### Phase C: subagents
Port `specifier`, `ux-framer`, `tech-framer`, `architect`, `qa` (and `strategist` if useful) from `~/.claude/agents/`. Strip every `mcp__topo__*` tool from their `tools:` list and replace with file tools. Re-ground their instructions on local files.

---

## 7. Test fixture (dogfooding)

Create `examples/sample-project/` as a minimal but valid LiveSpec project (see `SPEC.md` Appendix A for a complete example): a `livespec.yaml`, one or two personas under `product/persona/`, one constraint, and two features with REQs/ACs. Every skill must be exercised against it and leave it valid per `SPEC.md`. This fixture doubles as a human-readable conformance test.

If you want a richer fixture, run `reverse-livespec` against a small codebase to generate one, but a hand-written minimal project is enough to start.

---

## 8. Definition of done (per skill)

A skill is done when:

- [ ] Its `SKILL.md` has correct frontmatter (name, trigger-rich description, argument-hint) and no `mcp__topo__*` references anywhere.
- [ ] Every Territory MCP call in the source has a file-based replacement (§4) or is intentionally removed (work layer).
- [ ] It reads context from `product|ux|tech/` and writes to `features/` / concept files per the format contract.
- [ ] Output is valid against `SPEC.md` (IDs immutable and sequential, AC nesting correct, losslessness preserved, frontmatter never empty, mode respected).
- [ ] It runs end-to-end against `examples/sample-project/` and the result is a clean, reviewable git diff.
- [ ] It cites `SPEC.md §N` for each format rule it enforces.
- [ ] No AI-authorship mentions in committed content; commit rule from `CLAUDE.md` respected.

---

## 9. Things to ask the maintainer if unclear

- Where the LiveSpec project typically sits relative to the codebase (root vs `docs/livespec/` vs `.livespec/`) for the default search order. Default: search nearest `livespec.yaml` upward from cwd, then the §3.1 patterns.
- Whether `specify-feature` / `scope-features` should write files directly or always stage proposals for review first. Default: features written directly (they are the work product); concept changes proposed for review.
- Plugin name / version / license fields if Apache-2.0 is not the final choice.
