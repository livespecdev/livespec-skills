#!/usr/bin/env python3
"""check-spec: internal consistency of a spec project.

Reads the spec files only, never the codebase. Answers: do the specs hold
together? (spec <-> code coherence is check_drift.py.)

This is NOT the deferred LiveSpec validator (Level-3 conformance, §14): that one
is constitutive of the format and belongs in the `livespec` repo. This script is
an editorial diagnostic. It reports, it never writes.

Usage:
  python3 check_spec.py [PROJECT_ROOT] [--json] [--only CHECK,...] [--skip CHECK,...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from livespec import (  # noqa: E402
    CONCEPT_ROOTS,
    PROSE_REF_RE,
    SLUG_RE,
    XFEAT_REF_RE,
    Concept,
    Feature,
    Project,
    Report,
    emit,
    resolve_project,
)

# §6.2 core taxonomy: type slug -> containing top-level directory.
CORE_TAXONOMY = {
    "persona": "product",
    "pain_point": "product",
    "goal": "product",
    "principle": "product",
    "constraint": "product",
    "entity": "product",
    "glossary_term": "product",
    "ui_component": "ux",
    "design_principle": "ux",
    "ux_pattern": "ux",
    "screen": "ux",
    "coding_standard": "tech",
    "architecture_decision": "tech",
    "external_system": "tech",
}

SAME_FILE_REF_RE = re.compile(r"\[(?P<id>(?:REQ|AC|AS|Q|LIM|UX|TECH)-[0-9.]+)\](?!\()")

CHECKS = [
    "duplicate-manifest",
    "feature-no-requirements",
    "feature-no-summary",
    "duplicate-id",
    "ac-orphan",
    "ac-nesting",
    "ac-id-mismatch",
    "item-nesting",
    "malformed-item",
    "unknown-item-type",
    "item-annotation",
    "req-done-open-ac",
    "req-open-all-ac-done",
    "resolution-note",
    "broken-link",
    "unknown-link-type",
    "broken-item-ref",
    "broken-prose-ref",
    "ambiguous-prose-ref",
    "orphan-concept",
    "invalid-slug",
    "concept-placement",
    "concept-item-type",
    "empty-frontmatter",
    "missing-title",
    "open-question",
    "open-limitation",
]


def known_types(project: Project) -> dict:
    """Core taxonomy plus every extension type actually present on disk (§6.2)."""
    types = dict(CORE_TAXONOMY)
    for root_dir in CONCEPT_ROOTS:
        base = project.root / root_dir
        if base.is_dir():
            for d in base.iterdir():
                if d.is_dir() and d.name not in ("assets",):
                    types.setdefault(d.name, root_dir)
    return types


def link_targets(links: dict):
    """Yield (type_slug, target_slug) pairs from a `links:` mapping (§9.2)."""
    for key, value in links.items():
        if key == "feature":
            if isinstance(value, list):
                for slug in value:
                    yield "feature", str(slug)
            elif isinstance(value, dict):
                for relation, slugs in value.items():
                    if isinstance(slugs, list):
                        for slug in slugs:
                            yield "feature", str(slug)
                    elif isinstance(slugs, str):
                        yield "feature", slugs
            continue
        if isinstance(value, list):
            for slug in value:
                yield key, str(slug)
        elif isinstance(value, str):
            yield key, value


def check_items(report: Report, doc, enabled) -> None:
    seen: dict = {}
    reqs = [i for i in doc.items if i.type == "REQ"]

    for item in doc.items:
        key = (item.section, item.id)
        if key in seen and "duplicate-id" in enabled:
            report.add(
                check="duplicate-id", severity="error", spec_ref="§8.3",
                file=doc.rel, line=item.line, item=item.id,
                message=f"{item.id} is already used at line {seen[key]}. IDs are file-scoped and immutable; extend the sequence instead.",
            )
        seen.setdefault(key, item.line)

        if item.type == "AC":
            if item.parent_id is None and "ac-orphan" in enabled:
                report.add(
                    check="ac-orphan", severity="error", spec_ref="§8.2",
                    file=doc.rel, line=item.line, item=item.id,
                    message=f"{item.id} is not nested under a REQ.",
                )
            if item.indent >= 4 and "ac-nesting" in enabled:
                report.add(
                    check="ac-nesting", severity="error", spec_ref="§8.1",
                    file=doc.rel, line=item.line, item=item.id,
                    message=f"{item.id} is nested {item.indent} spaces deep; ACs sit exactly 2 spaces under their REQ. Split into several REQs.",
                )
            if item.parent_id and "ac-id-mismatch" in enabled:
                expected = item.parent_id.split("-", 1)[1]
                got = item.id.split("-", 1)[1].split(".")[0]
                if got != expected:
                    report.add(
                        check="ac-id-mismatch", severity="warning", spec_ref="§8.3",
                        file=doc.rel, line=item.line, item=item.id,
                        message=f"{item.id} is nested under {item.parent_id}; its ID should read AC-{expected}.N.",
                    )

        if item.type != "AC" and item.indent > 0 and "item-nesting" in enabled:
            report.add(
                check="item-nesting", severity="error", spec_ref="§8.1",
                file=doc.rel, line=item.line, item=item.id,
                message=f"{item.id} is nested {item.indent} spaces deep; only ACs nest, under their REQ. "
                        f"Write it as a top-level item.",
            )

        if "resolution-note" in enabled:
            if len(item.resolution_notes) > 1:
                report.add(
                    check="resolution-note", severity="error", spec_ref="§8.1",
                    file=doc.rel, line=item.line, item=item.id,
                    message=f"{item.id} carries {len(item.resolution_notes)} resolution notes; at most one is allowed.",
                )
            if item.resolution_notes and item.open:
                report.add(
                    check="resolution-note", severity="warning", spec_ref="§8.1",
                    file=doc.rel, line=item.line, item=item.id,
                    message=f"{item.id} is still open but carries a resolution note.",
                )

        if item.type == "Q" and item.open and "open-question" in enabled:
            report.add(
                check="open-question", severity="info", spec_ref="§8.2",
                file=doc.rel, line=item.line, item=item.id,
                feature=getattr(doc, "slug", None),
                message=f"{item.id}: {item.body}",
            )
        if item.type == "LIM" and item.open and "open-limitation" in enabled:
            report.add(
                check="open-limitation", severity="info", spec_ref="§8.2",
                file=doc.rel, line=item.line, item=item.id,
                feature=getattr(doc, "slug", None),
                message=f"{item.id}: {item.body}",
            )

    for req in reqs:
        acs = [i for i in doc.items if i.type == "AC" and i.parent_id == req.id]
        live = [a for a in acs if not a.cancelled]
        if not live:
            continue
        if req.done and any(a.open for a in live) and "req-done-open-ac" in enabled:
            open_ids = ", ".join(a.id for a in live if a.open)
            report.add(
                check="req-done-open-ac", severity="warning", spec_ref="§8.2",
                file=doc.rel, line=req.line, item=req.id,
                message=f"{req.id} is [x] but {open_ids} still open.",
            )
        if req.open and all(a.done for a in live) and "req-open-all-ac-done" in enabled:
            report.add(
                check="req-open-all-ac-done", severity="info", spec_ref="§8.2",
                file=doc.rel, line=req.line, item=req.id,
                message=f"{req.id} is [ ] but all {len(live)} of its ACs are [x].",
            )

    annotated = [i for i in doc.items if i.annotations]
    if "item-annotation" in enabled and annotated:
        tags = sorted({t for i in annotated for t in re.findall(r"\[([^\]]*)\]", i.annotations)})
        report.add(
            check="item-annotation", severity="warning", spec_ref="§8.1",
            file=doc.rel, line=annotated[0].line,
            message=f"{len(annotated)} item(s) carry bracketed tags between the ID and the colon "
                    f"({', '.join('[' + t + ']' for t in tags[:6])}). §8.1 puts the body straight after the ':'; "
                    f"a strict parser reads these as part of the ID and fails to resolve the item.",
        )

    if "unknown-item-type" in enabled and doc.unknown_typed:
        # One finding per (file, type): a project that adopted a custom type uses
        # it dozens of times, and listing every line buries the real findings.
        by_type: dict = {}
        for lineno, type_slug, item_id in doc.unknown_typed:
            by_type.setdefault(type_slug, []).append((lineno, item_id))
        for type_slug, occurrences in sorted(by_type.items()):
            first_line, first_id = occurrences[0]
            hint = {
                "TE": " If 'TE' stands for tech directions, the §8.2 type is TECH.",
                "ISS": " ISS was renamed LIM (known limitation); a defect scheduled for a fix belongs in the issue tracker, not the spec.",
            }.get(type_slug, "")
            report.add(
                check="unknown-item-type", severity="warning", spec_ref="§8.2",
                file=doc.rel, line=first_line,
                message=f"{len(occurrences)} item(s) of type '{type_slug}' ({first_id} and following). "
                        f"§8.2 defines REQ, AC, AS, Q, LIM, UX, TECH only; a reader that does not know '{type_slug}' will skip them.{hint}",
            )

    if "malformed-item" in enabled:
        for lineno, text in doc.malformed:
            report.add(
                check="malformed-item", severity="warning", spec_ref="§8.1",
                file=doc.rel, line=lineno,
                message=f"checkbox line does not parse as a spec item: {text[:100]}",
            )


def check_refs(report: Report, project: Project, doc, types: dict, enabled) -> None:
    own_ids = {i.id for i in doc.items}

    for lineno, text in doc.body_lines:
        if text.lstrip().startswith(("```", "~~~")):
            continue

        if "broken-item-ref" in enabled:
            for m in SAME_FILE_REF_RE.finditer(text):
                if m.group("id") not in own_ids:
                    report.add(
                        check="broken-item-ref", severity="warning", spec_ref="§8.1",
                        file=doc.rel, line=lineno,
                        message=f"[{m.group('id')}] does not exist in this file.",
                    )
            for m in XFEAT_REF_RE.finditer(text):
                target = project.feature(m.group("slug"))
                if target is None:
                    report.add(
                        check="broken-item-ref", severity="warning", spec_ref="§8.1",
                        file=doc.rel, line=lineno,
                        message=f"[{m.group('slug')}#{m.group('id')}] points at an unknown feature.",
                    )
                elif target.item(m.group("id")) is None:
                    report.add(
                        check="broken-item-ref", severity="warning", spec_ref="§8.1",
                        file=doc.rel, line=lineno,
                        message=f"[{m.group('slug')}#{m.group('id')}]: {m.group('slug')} has no {m.group('id')}.",
                    )

        for m in PROSE_REF_RE.finditer(text):
            payload = m.group("payload").strip()
            if ":" in payload:
                if "broken-prose-ref" not in enabled:
                    continue
                type_slug, _, slug = payload.partition(":")
                type_slug, slug = type_slug.strip(), slug.strip()
                if type_slug == "feature":
                    if project.feature(slug) is None:
                        report.add(
                            check="broken-prose-ref", severity="warning", spec_ref="§9.5",
                            file=doc.rel, line=lineno,
                            message=f"[[feature:{slug}]] resolves to no file.",
                        )
                elif type_slug not in types:
                    report.add(
                        check="broken-prose-ref", severity="warning", spec_ref="§9.5",
                        file=doc.rel, line=lineno,
                        message=f"[[{payload}]] uses type '{type_slug}', absent from the taxonomy and from the project tree.",
                    )
                elif project.concept(type_slug, slug) is None:
                    report.add(
                        check="broken-prose-ref", severity="warning", spec_ref="§9.5",
                        file=doc.rel, line=lineno,
                        message=f"[[{payload}]] resolves to no file under {types[type_slug]}/{type_slug}/.",
                    )
            else:
                matches = [c.rel for c in project.concepts_by_slug(payload)]
                if project.feature(payload):
                    matches.append(project.feature(payload).rel)
                if not matches and "broken-prose-ref" in enabled:
                    report.add(
                        check="broken-prose-ref", severity="warning", spec_ref="§9.5",
                        file=doc.rel, line=lineno,
                        message=f"[[{payload}]] matches no feature and no concept.",
                    )
                elif len(matches) > 1 and "ambiguous-prose-ref" in enabled:
                    report.add(
                        check="ambiguous-prose-ref", severity="warning", spec_ref="§9.5",
                        file=doc.rel, line=lineno,
                        message=f"[[{payload}]] is ambiguous ({', '.join(matches)}). Use the typed form [[type:slug]].",
                    )


def check_links(report: Report, project: Project, doc, types: dict, enabled) -> None:
    for type_slug, target in link_targets(doc.links):
        if type_slug == "feature":
            if project.feature(target) is None and "broken-link" in enabled:
                report.add(
                    check="broken-link", severity="warning", spec_ref="§9.2",
                    file=doc.rel, line=1,
                    message=f"links.feature -> '{target}': no features/**/{target}.md.",
                )
            continue
        if type_slug not in types:
            if "unknown-link-type" in enabled:
                report.add(
                    check="unknown-link-type", severity="warning", spec_ref="§9.2",
                    file=doc.rel, line=1,
                    message=f"links.{type_slug}: type absent from the core taxonomy and from the project tree.",
                )
            continue
        if project.concept(type_slug, target) is None and "broken-link" in enabled:
            report.add(
                check="broken-link", severity="warning", spec_ref="§9.2",
                file=doc.rel, line=1,
                message=f"links.{type_slug} -> '{target}': no {types[type_slug]}/{type_slug}/{target}.md.",
            )


def check_doc_shape(report: Report, doc, enabled) -> None:
    if doc.frontmatter_present and doc.frontmatter_empty and "empty-frontmatter" in enabled:
        report.add(
            check="empty-frontmatter", severity="warning", spec_ref="§5",
            file=doc.rel, line=1,
            message="empty frontmatter block; omit it entirely.",
        )
    if not doc.title and "missing-title" in enabled:
        report.add(
            check="missing-title", severity="warning", spec_ref="§6.4",
            file=doc.rel, line=1, message="no H1 title.",
        )
    if not SLUG_RE.match(doc.slug) and "invalid-slug" in enabled:
        report.add(
            check="invalid-slug", severity="warning", spec_ref="§9.1",
            file=doc.rel, line=1,
            message=f"slug '{doc.slug}' is not kebab-case ASCII.",
        )


def check_feature_shape(report: Report, feature: Feature, enabled) -> None:
    reqs = [i for i in feature.items if i.type == "REQ"]
    if not reqs and "feature-no-requirements" in enabled:
        report.add(
            check="feature-no-requirements", severity="warning", spec_ref="§7.3",
            file=feature.rel, line=1, feature=feature.slug,
            message="no REQ in this feature: it states intent but nothing testable.",
        )

    if "feature-no-summary" in enabled:
        summary = None
        seen_h1 = False
        for _, text in feature.body_lines:
            if not seen_h1:
                if text.startswith("# "):
                    seen_h1 = True
                continue
            stripped = text.strip()
            if not stripped:
                continue
            if stripped.startswith(("#", "-", "*", ">", "|", "```")):
                break
            summary = stripped
            break
        if summary is None:
            report.add(
                check="feature-no-summary", severity="warning", spec_ref="§7.4",
                file=feature.rel, line=1, feature=feature.slug,
                message="no summary paragraph between the H1 and the first section.",
            )


def check_concept_placement(report: Report, concept: Concept, enabled) -> None:
    if "concept-placement" in enabled and not concept.type:
        report.add(
            check="concept-placement", severity="error", spec_ref="§6.1",
            file=concept.rel, line=1,
            message=f"sits directly under {concept.root}/; concepts live in {concept.root}/{{type}}/{{slug}}.md.",
        )


def check_concept_items(report: Report, concept: Concept, enabled) -> None:
    if "concept-item-type" not in enabled:
        return
    for item in concept.items:
        if item.type != "Q":
            report.add(
                check="concept-item-type", severity="error", spec_ref="§6.4",
                file=concept.rel, line=item.line, item=item.id,
                message=f"{item.id}: a concept holds only Q items, in ## Questions. "
                        f"A requirement or direction belongs in a feature.",
            )


def check_orphan_concepts(report: Report, project: Project, enabled) -> None:
    if "orphan-concept" not in enabled:
        return
    referenced = set()
    for doc in project.docs:
        for type_slug, target in link_targets(doc.links):
            referenced.add((type_slug, target))
        for _, text in doc.body_lines:
            for m in PROSE_REF_RE.finditer(text):
                payload = m.group("payload").strip()
                if ":" in payload:
                    t, _, s = payload.partition(":")
                    referenced.add((t.strip(), s.strip()))
                else:
                    for c in project.concepts_by_slug(payload):
                        referenced.add((c.type, c.slug))
    for concept in project.concepts:
        if not concept.type:
            continue  # already reported by concept-placement; it cannot be linked at all
        if (concept.type, concept.slug) not in referenced:
            report.add(
                check="orphan-concept", severity="info", spec_ref="§9.2",
                file=concept.rel, line=1,
                message=f"{concept.type}:{concept.slug} is referenced by no feature and no concept.",
            )


def check_manifest(report: Report, project: Project, enabled) -> None:
    if "duplicate-manifest" not in enabled or len(project.manifest_files) < 2:
        return
    report.add(
        check="duplicate-manifest", severity="error", spec_ref="§4",
        file=project.manifest_files[0], line=1,
        message=f"The project root holds several manifests ({', '.join(project.manifest_files)}). Keep one; this script read {project.manifest_files[0]}.",
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check a spec project's internal consistency.")
    parser.add_argument("project", nargs="?", help="project root (defaults to discovery from CWD)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--only", help="comma-separated checks to run")
    parser.add_argument("--skip", help="comma-separated checks to skip")
    parser.add_argument("--feature", help="restrict to one feature slug")
    parser.add_argument("--list-checks", action="store_true", help="print available checks and exit")
    args = parser.parse_args(argv)

    if args.list_checks:
        for name in CHECKS:
            print(name)
        return 0

    enabled = set(CHECKS)
    if args.only:
        requested = {c.strip() for c in args.only.split(",") if c.strip()}
        unknown = requested - set(CHECKS)
        if unknown:
            print(f"error: unknown check(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        enabled = requested
    if args.skip:
        enabled -= {c.strip() for c in args.skip.split(",") if c.strip()}

    project = resolve_project(args.project, Path.cwd())
    types = known_types(project)

    features = project.features
    if args.feature:
        features = [f for f in features if f.slug == args.feature]
        if not features:
            print(f"error: no feature '{args.feature}' in {project.root}", file=sys.stderr)
            return 2

    report = Report("check-spec", project, scope=args.feature)
    check_manifest(report, project, enabled)

    for feature in features:
        check_doc_shape(report, feature, enabled)
        check_feature_shape(report, feature, enabled)
        check_items(report, feature, enabled)
        check_links(report, project, feature, types, enabled)
        check_refs(report, project, feature, types, enabled)

    if not args.feature:
        for concept in project.concepts:
            check_doc_shape(report, concept, enabled)
            check_concept_placement(report, concept, enabled)
            check_concept_items(report, concept, enabled)
            check_items(report, concept, enabled)
            check_links(report, project, concept, types, enabled)
            check_refs(report, project, concept, types, enabled)
        check_orphan_concepts(report, project, enabled)

    all_items = [i for f in features for i in f.items]
    report.stats = {
        "features": len(features),
        "spec items": len(all_items),
        "REQ": sum(1 for i in all_items if i.type == "REQ"),
        "AC": sum(1 for i in all_items if i.type == "AC"),
        "open Q": sum(1 for i in all_items if i.type == "Q" and i.open),
        "open Q (concepts)": sum(
            1 for c in project.concepts for i in c.items if i.type == "Q" and i.open
        ) if not args.feature else 0,
        "open LIM": sum(1 for i in all_items if i.type == "LIM" and i.open),
        "UX": sum(1 for i in all_items if i.type == "UX"),
        "TECH": sum(1 for i in all_items if i.type == "TECH"),
    }
    if project.mode == "strict":
        report.notes.append("project is in strict mode (§12.2): section names, order, and placement are enforced; this script does not check them.")

    return emit(report, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
