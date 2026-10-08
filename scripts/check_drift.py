#!/usr/bin/env python3
"""check-drift: coherence between LiveSpec intent and codebase reality.

Cross-references the checkbox state of spec items (§8.1) with the `livespec:`
markers found in source code (§9.4). Answers: does the code say the same thing
as the spec?

The format defines the marker syntax and explicitly leaves coverage rules and
drift detection to tooling (§9.4, "Scope of this section"). This script is one
such tool. It reports, it never writes: the fixes belong to /sync-spec (spec
side) or /implement-feature (code side).

Usage:
  python3 check_drift.py [PROJECT_ROOT] [--code-root DIR] [--feature SLUG] [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from livespec import (  # noqa: E402
    CONCEPT_ROOTS,
    Project,
    Report,
    emit,
    repo_root,
    resolve_project,
    scan_markers,
)

CHECKS = [
    "marker-unknown-feature",
    "marker-unknown-id",
    "marker-on-cancelled",
    "marker-on-open",
    "done-unmarked",
    "open-unmarked",
    "feature-unmarked",
]


def anchor_targets(project: Project, features):
    """Spec items whose marker coverage is reported: REQ and AC only.

    UX and TECH directions MAY carry markers too (§9.4) and those markers are
    resolved, but a direction with no marker is not a gap: many directions
    (a layout, a wording choice) have no single code site to point at.
    """
    for feature in features:
        for item in feature.items:
            if item.type in ("REQ", "AC"):
                yield feature, item


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Check LiveSpec intent against codebase reality.")
    parser.add_argument("project", nargs="?", help="project root (defaults to discovery from CWD)")
    parser.add_argument("--code-root", help="directory to scan for livespec: markers (defaults to the git repo root)")
    parser.add_argument("--feature", help="restrict the report to one feature slug")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--only", help="comma-separated checks to run")
    parser.add_argument("--skip", help="comma-separated checks to skip")
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

    if args.code_root:
        code_root = Path(args.code_root).expanduser().resolve()
        if not code_root.is_dir():
            print(f"error: --code-root {code_root} is not a directory", file=sys.stderr)
            return 2
    else:
        code_root = repo_root(project.root)
        if code_root == project.root and not any(
            (project.root / d).is_dir() for d in ("src", "lib", "app")
        ):
            # Spec-only repo: the code most likely lives beside it, not under it.
            code_root = project.root

    # Markers inside the spec tree itself are prose, not anchors.
    exclude = [project.root / d for d in (*CONCEPT_ROOTS, "features")]
    markers = scan_markers(code_root, exclude=exclude)

    report = Report("check-drift", project, scope=args.feature)

    features = project.features
    if args.feature:
        features = [f for f in features if f.slug == args.feature]
        if not features:
            print(f"error: no feature '{args.feature}' in {project.root}", file=sys.stderr)
            return 2
    in_scope = {f.slug for f in features}

    # ---- marker side: every marker must resolve (§9.4)
    direct: dict = {}   # (feature_slug, item_id) -> [Marker]
    for marker in markers:
        feature = project.feature(marker.slug)
        if feature is None:
            if "marker-unknown-feature" in enabled and not args.feature:
                report.add(
                    check="marker-unknown-feature", severity="error", spec_ref="§9.4",
                    file=marker.file, line=marker.line, feature=marker.slug,
                    message=f"marker points at feature '{marker.slug}': no features/**/{marker.slug}.md. Renamed or deleted?",
                )
            continue
        if args.feature and marker.slug != args.feature:
            continue
        for item_id in marker.ids:
            item = feature.item(item_id)
            if item is None:
                if "marker-unknown-id" in enabled:
                    report.add(
                        check="marker-unknown-id", severity="error", spec_ref="§9.4",
                        file=marker.file, line=marker.line,
                        feature=marker.slug, item=item_id,
                        message=f"marker points at {marker.slug}#{item_id}, absent from the feature file. IDs are immutable (§8.3): the item was deleted instead of cancelled, or the ID is a typo.",
                    )
                continue
            direct.setdefault((marker.slug, item_id), []).append(marker)
            if item.cancelled and "marker-on-cancelled" in enabled:
                report.add(
                    check="marker-on-cancelled", severity="warning", spec_ref="§8.1",
                    file=marker.file, line=marker.line,
                    feature=marker.slug, item=item_id,
                    message=f"code is anchored to {item_id}, marked [-] cancelled: {item.body[:80]}",
                )
            elif item.open and item.type in ("REQ", "AC", "UX", "TECH") and "marker-on-open" in enabled:
                # A marker on an open LIM points at the code where the limitation lives,
                # and on an open Q at the code the question is about: neither is a
                # divergence. An open direction means "decided, not yet applied",
                # so code anchored to it disagrees with the spec, as for REQ/AC.
                report.add(
                    check="marker-on-open", severity="warning", spec_ref="§8.1",
                    file=marker.file, line=marker.line,
                    feature=marker.slug, item=item_id,
                    message=f"code is anchored to {item_id}, still [ ] open: {item.body[:80]}",
                )

    # ---- spec side: coverage of each anchorable item
    def covered(feature, item) -> bool:
        if (feature.slug, item.id) in direct:
            return True
        if item.type == "AC" and item.parent_id:
            # A marker on a REQ implicitly covers its nested ACs (§9.4).
            return (feature.slug, item.parent_id) in direct
        if item.type == "REQ":
            acs = [
                i for i in feature.items
                if i.type == "AC" and i.parent_id == item.id and not i.cancelled
            ]
            return bool(acs) and all((feature.slug, a.id) in direct for a in acs)
        return False

    done_total = done_covered = 0
    for feature, item in anchor_targets(project, features):
        if item.cancelled:
            continue
        is_covered = covered(feature, item)
        if item.done:
            done_total += 1
            if is_covered:
                done_covered += 1
            elif "done-unmarked" in enabled:
                report.add(
                    check="done-unmarked", severity="warning", spec_ref="§9.4",
                    file=feature.rel, line=item.line,
                    feature=feature.slug, item=item.id,
                    message=f"{item.id} is [x] but no livespec: marker anchors it: {item.body[:80]}",
                )
        elif item.open and not is_covered and "open-unmarked" in enabled:
            report.add(
                check="open-unmarked", severity="info", spec_ref="§8.1",
                file=feature.rel, line=item.line,
                feature=feature.slug, item=item.id,
                message=f"{item.id} is [ ] with no code anchored to it: {item.body[:80]}",
            )

    if "feature-unmarked" in enabled:
        for feature in features:
            anchorable = [i for i in feature.items if i.type in ("REQ", "AC") and not i.cancelled]
            if not anchorable:
                continue
            if not any((feature.slug, i.id) in direct for i in anchorable):
                state = "some items are [x]" if any(i.done for i in anchorable) else "all items are [ ]"
                report.add(
                    check="feature-unmarked", severity="info", spec_ref="§9.4",
                    file=feature.rel, line=1, feature=feature.slug,
                    message=f"no livespec: marker anywhere in the code for this feature ({state}).",
                )

    resolved = sum(len(v) for v in direct.values())
    report.stats = {
        "code root": str(code_root),
        "markers found": len(markers),
        "marker->item links resolved": resolved,
        "features in scope": len(features),
        "anchored [x] items": f"{done_covered}/{done_total}" if done_total else "0/0",
    }
    if not markers:
        report.notes.append(
            "no livespec: marker found in the scanned tree. Either the code is elsewhere "
            "(pass --code-root) or nothing has been anchored yet (§9.4)."
        )
    if code_root == project.root:
        report.notes.append(
            "code root equals the project root; if this repo holds specs only, "
            "point --code-root at the application repo."
        )

    return emit(report, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
