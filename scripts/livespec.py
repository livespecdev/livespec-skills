"""Shared LiveSpec parsing helpers for the check-* scripts.

Pure stdlib, no dependencies: the plugin cannot install anything in the user's
environment. Parses the subset of LiveSpec that the checks need, tolerantly:
anything it does not understand is preserved as-is and never raises.

Section references (§N) point to reference/SPEC.md, pinned v1.0.0-draft.2.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- constants

CONCEPT_ROOTS = ("product", "ux", "tech")

# Directories never worth walking, for either spec or code scans.
IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".claude",
    "node_modules", "bower_components", "vendor", "third_party",
    "dist", "build", "out", "target", "coverage", "tmp",
    ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".tox", ".gradle", ".next", ".nuxt", ".svelte-kit", ".cache",
    "Pods", "DerivedData", ".terraform",
}

# Binary-ish extensions skipped when grepping for livespec: markers.
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tiff", ".avif",
    ".pdf", ".zip", ".gz", ".tar", ".bz2", ".xz", ".7z", ".rar", ".jar", ".war",
    ".mp3", ".mp4", ".mov", ".avi", ".mkv", ".wav", ".ogg", ".webm", ".flac",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".so", ".dylib", ".dll", ".exe", ".bin", ".o", ".a", ".class", ".pyc",
    ".db", ".sqlite", ".sqlite3", ".lock", ".pack", ".idx",
}

MAX_SCAN_BYTES = 2_000_000

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")  # §9.1

# §8.1 inline syntax. Indent is captured to validate nesting depth.
# `annot` tolerates the bracketed-tag extension some projects write between the
# ID and the colon (`- [x] REQ-3 [security]: ...`). It is not part of the §8.1
# grammar, but refusing to parse the item would lose the whole file; check_spec
# reports it instead.
ITEM_RE = re.compile(
    r"^(?P<indent>[ \t]*)- \[(?P<state>[ xX\-])\]\s+"
    r"(?P<type>REQ|AC|AS|Q|LIM|UX|TECH)-(?P<num>[0-9]+(?:\.[0-9]+)*)"
    r"(?P<annot>(?:[ \t]+\[[^\]\n]*\])*)[ \t]*:\s?(?P<body>.*)$"
)
# A checkbox line inside a spec section that does not match ITEM_RE.
LOOSE_CHECKBOX_RE = re.compile(r"^(?P<indent>[ \t]*)- \[(?P<state>[ xX\-])\]\s*(?P<rest>.*)$")
# Same shape as a spec item but with a type outside the §8.2 set (e.g. TE-1, UXD-3).
UNKNOWN_TYPED_RE = re.compile(
    r"^(?P<indent>[ \t]*)- \[(?P<state>[ xX\-])\]\s+"
    r"(?P<type>[A-Z][A-Z_]{0,14})-(?P<num>[0-9]+(?:\.[0-9]+)*)"
    r"(?:[ \t]+\[[^\]\n]*\])*[ \t]*:\s?(?P<body>.*)$"
)

H2_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
RESOLUTION_RE = re.compile(r"^\s*→ (?P<note>.*)$")  # §8.1 resolution note

# §9.4 marker payload: no whitespace inside the id list.
MARKER_RE = re.compile(
    r"livespec:[ \t]+(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)#(?P<ids>[A-Za-z]+-[0-9.]+(?:,[A-Za-z]+-[0-9.]+)*)"
)
# §9.5 in-prose reference.
PROSE_REF_RE = re.compile(r"\[\[(?P<payload>[^\[\]\s][^\[\]]*?)\]\]")
# §8.1 cross-feature spec item reference inside a body.
XFEAT_REF_RE = re.compile(r"\[(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)#(?P<id>[A-Za-z]+-[0-9.]+)\]")

SPEC_SECTIONS = {
    "requirements": "REQ",
    "assumptions": "AS",
    "questions": "Q",
    "limitations": "LIM",
    "ux": "UX",
    "tech": "TECH",
}


# ------------------------------------------------------------------ models

@dataclass
class SpecItem:
    type: str            # REQ | AC | AS | Q | LIM | UX | TECH
    id: str              # e.g. REQ-1, AC-1.2
    state: str           # " " | "x" | "-"
    body: str
    line: int
    section: str         # H2 title the item was found under
    indent: int
    parent_id: str | None = None
    annotations: str = ""   # bracketed tags between the ID and the colon, if any
    resolution_notes: list[str] = field(default_factory=list)
    continuation: list[str] = field(default_factory=list)

    @property
    def done(self) -> bool:
        return self.state == "x"

    @property
    def cancelled(self) -> bool:
        return self.state == "-"

    @property
    def open(self) -> bool:
        return self.state == " "


@dataclass
class Doc:
    """A parsed LiveSpec markdown file (feature or concept)."""
    path: Path
    rel: str
    slug: str
    frontmatter: dict
    frontmatter_present: bool
    frontmatter_empty: bool
    title: str | None
    sections: list[str]
    body_lines: list[tuple[int, str]]  # (1-based line no, text) after frontmatter
    items: list[SpecItem] = field(default_factory=list)
    malformed: list[tuple[int, str]] = field(default_factory=list)
    # (line, type, id) for checkbox items using a type outside §8.2
    unknown_typed: list[tuple[int, str, str]] = field(default_factory=list)
    parse_notes: list[tuple[int, str]] = field(default_factory=list)

    @property
    def links(self) -> dict:
        raw = self.frontmatter.get("links")
        return raw if isinstance(raw, dict) else {}


@dataclass
class Feature(Doc):
    area: str | None = None

    def item(self, item_id: str) -> SpecItem | None:
        for it in self.items:
            if it.id == item_id:
                return it
        return None


@dataclass
class Concept(Doc):
    root: str = ""   # product | ux | tech
    type: str = ""   # type slug == directory name (§6.1)


@dataclass
class Project:
    root: Path
    manifest: dict
    features: list[Feature]
    concepts: list[Concept]

    @property
    def mode(self) -> str:
        m = self.manifest.get("mode")
        return m if isinstance(m, str) and m else "loose"

    @property
    def name(self) -> str:
        n = self.manifest.get("name")
        return n if isinstance(n, str) and n else self.root.name

    def feature(self, slug: str) -> Feature | None:
        for f in self.features:
            if f.slug == slug:
                return f
        return None

    def concept(self, type_slug: str, slug: str) -> Concept | None:
        for c in self.concepts:
            if c.type == type_slug and c.slug == slug:
                return c
        return None

    def concepts_by_slug(self, slug: str) -> list[Concept]:
        return [c for c in self.concepts if c.slug == slug]

    @property
    def docs(self) -> list[Doc]:
        return [*self.features, *self.concepts]


# ------------------------------------------------------------------ YAML-ish

def _scalar(raw: str):
    """Coerce a YAML scalar. Deliberately minimal: strings, bools, ints, null."""
    v = raw.strip()
    if not v:
        return ""
    if (v[0] == '"' and v[-1] == '"' and len(v) > 1) or (v[0] == "'" and v[-1] == "'" and len(v) > 1):
        return v[1:-1]
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _inline_list(raw: str) -> list:
    inner = raw.strip()[1:-1].strip()
    if not inner:
        return []
    return [_scalar(part) for part in inner.split(",") if part.strip() != ""]


def parse_yaml_block(text: str) -> dict:
    """Parse the YAML subset LiveSpec frontmatter and manifests actually use.

    Handles nested mappings by indentation, inline `[a, b]` lists, block lists,
    and block scalars (`|`, `>`), which are consumed but flattened to a string.
    Anything else degrades to a raw string rather than raising.
    """
    root: dict = {}
    # stack of (indent, container)
    stack: list[tuple[int, dict]] = [(-1, root)]
    lines = text.splitlines()
    i = 0
    pending_list: list | None = None
    pending_indent = -1

    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()

        if stripped.startswith("- "):
            if pending_list is not None and indent > pending_indent:
                pending_list.append(_scalar(stripped[2:]))
            continue

        m = re.match(r"^(?P<key>[^:]+):(?P<rest>.*)$", stripped)
        if not m:
            continue
        key = m.group("key").strip().strip('"').strip("'")
        rest = m.group("rest").strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, root)]
        container = stack[-1][1]
        pending_list = None
        pending_indent = indent

        if rest.startswith("[") and rest.endswith("]"):
            container[key] = _inline_list(rest)
        elif rest in ("|", ">", "|-", ">-", "|+", ">+"):
            chunk: list[str] = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip(" "))) <= indent:
                    break
                chunk.append(nxt.strip())
                i += 1
            container[key] = " ".join(c for c in chunk if c).strip()
        elif rest == "":
            # Either a nested mapping or a block list; decide by lookahead.
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip().startswith("- ") and (
                len(lines[j]) - len(lines[j].lstrip(" "))
            ) > indent:
                lst: list = []
                container[key] = lst
                pending_list = lst
            else:
                child: dict = {}
                container[key] = child
                stack.append((indent, child))
        else:
            container[key] = _scalar(rest)

    return root


def split_frontmatter(text: str) -> tuple[dict, bool, bool, int, str]:
    """Return (frontmatter, present, empty, body_start_line, body_text).

    `body_start_line` is 1-based and points at the first body line.
    """
    if not text.startswith("---"):
        return {}, False, False, 1, text
    lines = text.splitlines(keepends=True)
    if lines[0].strip() != "---":
        return {}, False, False, 1, text
    for idx in range(1, len(lines)):
        if lines[idx].strip() in ("---", "..."):
            block = "".join(lines[1:idx])
            fm = parse_yaml_block(block)
            body = "".join(lines[idx + 1:])
            return fm, True, block.strip() == "", idx + 2, body
    # Unterminated frontmatter: treat the whole file as body.
    return {}, False, False, 1, text


# ------------------------------------------------------------------ parsing

def _parse_items(body_lines: list[tuple[int, str]], doc: Doc) -> None:
    section = ""
    last_top: SpecItem | None = None
    last_any: SpecItem | None = None

    for lineno, text in body_lines:
        h2 = H2_RE.match(text)
        if h2:
            section = h2.group("title")
            doc.sections.append(section)
            last_top = None
            last_any = None
            continue

        m = ITEM_RE.match(text)
        if m:
            indent = len(m.group("indent").replace("\t", "  "))
            itype = m.group("type")
            item = SpecItem(
                type=itype,
                id=f"{itype}-{m.group('num')}",
                state=m.group("state").lower(),
                body=m.group("body").strip(),
                line=lineno,
                section=section,
                indent=indent,
                annotations=m.group("annot").strip(),
            )
            if itype == "AC":
                item.parent_id = last_top.id if last_top and last_top.type == "REQ" else None
            else:
                last_top = item
            doc.items.append(item)
            last_any = item
            continue

        unknown = UNKNOWN_TYPED_RE.match(text)
        if unknown and section:
            doc.unknown_typed.append(
                (lineno, unknown.group("type"), f"{unknown.group('type')}-{unknown.group('num')}")
            )
            last_any = None
            continue

        loose = LOOSE_CHECKBOX_RE.match(text)
        if loose and section:
            doc.malformed.append((lineno, text.strip()))
            last_any = None
            continue

        if last_any is not None and text.strip():
            indent = len(text) - len(text.lstrip(" "))
            if indent > last_any.indent:
                res = RESOLUTION_RE.match(text)
                if res:
                    last_any.resolution_notes.append(res.group("note").strip())
                else:
                    last_any.continuation.append(text.strip())
            else:
                last_any = None
        elif not text.strip():
            # A blank line does not close an item body in markdown lists, but
            # two of them effectively do; keep it simple and stay permissive.
            pass


def parse_doc(path: Path, root: Path) -> Doc:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, present, empty, start, body = split_frontmatter(text)
    body_lines = [(start + i, line) for i, line in enumerate(body.splitlines())]
    title = None
    for _, line in body_lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return Doc(
        path=path,
        rel=str(path.relative_to(root)),
        slug=path.stem,
        frontmatter=fm,
        frontmatter_present=present,
        frontmatter_empty=empty,
        title=title,
        sections=[],
        body_lines=body_lines,
    )


def _as_feature(d: Doc, area: str | None) -> Feature:
    f = Feature(
        path=d.path, rel=d.rel, slug=d.slug, frontmatter=d.frontmatter,
        frontmatter_present=d.frontmatter_present, frontmatter_empty=d.frontmatter_empty,
        title=d.title, sections=[], body_lines=d.body_lines, area=area,
    )
    _parse_items(f.body_lines, f)
    return f


def _as_concept(d: Doc, root_dir: str, type_slug: str) -> Concept:
    c = Concept(
        path=d.path, rel=d.rel, slug=d.slug, frontmatter=d.frontmatter,
        frontmatter_present=d.frontmatter_present, frontmatter_empty=d.frontmatter_empty,
        title=d.title, sections=[], body_lines=d.body_lines,
        root=root_dir, type=type_slug,
    )
    for _, text in c.body_lines:
        h2 = H2_RE.match(text)
        if h2:
            c.sections.append(h2.group("title"))
    return c


def load_project(root: Path) -> Project:
    root = root.resolve()
    manifest_path = root / "livespec.yaml"
    manifest = {}
    if manifest_path.is_file():
        manifest = parse_yaml_block(manifest_path.read_text(encoding="utf-8", errors="replace"))

    features: list[Feature] = []
    fdir = root / "features"
    if fdir.is_dir():
        for path in sorted(fdir.rglob("*.md")):
            rel_parts = path.relative_to(fdir).parts
            # Match against the path *inside* the project: an absolute path may
            # legitimately contain a segment named tmp/, build/, env/, ...
            if any(part in IGNORED_DIRS for part in rel_parts[:-1]):
                continue
            area = "/".join(rel_parts[:-1]) if len(rel_parts) > 1 else None
            features.append(_as_feature(parse_doc(path, root), area))

    concepts: list[Concept] = []
    for root_dir in CONCEPT_ROOTS:
        base = root / root_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            rel_parts = path.relative_to(base).parts
            if any(part in IGNORED_DIRS for part in rel_parts[:-1]):
                continue
            type_slug = rel_parts[0] if len(rel_parts) > 1 else ""
            concepts.append(_as_concept(parse_doc(path, root), root_dir, type_slug))

    return Project(root=root, manifest=manifest, features=features, concepts=concepts)


# --------------------------------------------------------------- discovery

def find_projects(start: Path, max_depth: int = 4) -> list[Path]:
    """Locate LiveSpec project roots (§3, §3.1). Never assume a fixed path."""
    start = start.resolve()
    found: list[Path] = []

    if (start / "livespec.yaml").is_file():
        found.append(start)

    def walk(base: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(p for p in base.iterdir() if p.is_dir())
        except (PermissionError, OSError):
            return
        for d in entries:
            if d.name in IGNORED_DIRS or (d.name.startswith(".") and d.name != ".livespec"):
                continue
            if (d / "livespec.yaml").is_file():
                found.append(d)
                continue  # nested projects are independent roots; do not recurse in
            walk(d, depth + 1)

    walk(start, 1)

    # Walk up too: the user may sit inside the codebase, spec above or beside.
    for parent in start.parents:
        if (parent / "livespec.yaml").is_file() and parent not in found:
            found.append(parent)
        if (parent / ".git").exists():
            break

    seen, unique = set(), []
    for p in found:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def repo_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def iter_source_files(root: Path, exclude: list[Path] | None = None):
    """Yield candidate source files for a marker scan."""
    exclude = [e.resolve() for e in (exclude or [])]

    def excluded(p: Path) -> bool:
        return any(p == e or e in p.parents for e in exclude)

    stack = [root]
    while stack:
        base = stack.pop()
        try:
            entries = list(base.iterdir())
        except (PermissionError, OSError):
            continue
        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    if entry.name in IGNORED_DIRS or excluded(entry):
                        continue
                    stack.append(entry)
                elif entry.is_file():
                    if entry.suffix.lower() in BINARY_EXT or excluded(entry):
                        continue
                    if entry.stat().st_size > MAX_SCAN_BYTES:
                        continue
                    yield entry
            except OSError:
                continue


@dataclass
class Marker:
    slug: str
    ids: list[str]
    file: str
    line: int
    raw: str


MARKDOWN_EXT = {".md", ".markdown", ".mdx"}
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")


def _blank(chunk: str) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in chunk)


def _mask_markdown(text: str) -> str:
    """Keep only markers that are real anchors in a markdown file.

    §9.4 requires a marker to sit inside a comment in the host language's native
    syntax. In markdown that is `<!-- -->`. A marker shown in prose, in backticks,
    or inside a fenced code block is documentation *about* the format, not an
    anchor: without this, every repo that documents LiveSpec reports its own
    examples as broken links.

    Returns the text with everything outside an HTML comment blanked out (line
    numbers preserved), fenced code blocks removed first.
    """
    lines = text.splitlines(keepends=True)
    fence = None
    kept = []
    for line in lines:
        stripped = line.lstrip()
        if fence is None:
            marker = stripped[:3]
            if marker in ("```", "~~~"):
                fence = marker
                kept.append(_blank(line))
                continue
            kept.append(line)
        else:
            kept.append(_blank(line))
            if stripped.startswith(fence):
                fence = None
    defenced = INLINE_CODE_RE.sub(lambda m: _blank(m.group(0)), "".join(kept))

    masked = list(_blank(defenced))
    for m in HTML_COMMENT_RE.finditer(defenced):
        for i in range(m.start(), m.end()):
            masked[i] = defenced[i]
    return "".join(masked)


def scan_markers(root: Path, exclude: list[Path] | None = None) -> list[Marker]:
    """Find every `livespec:` marker in the tree (§9.4). Case-sensitive."""
    markers: list[Marker] = []
    for path in iter_source_files(root, exclude):
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        if "livespec:" not in text:
            continue
        if path.suffix.lower() in MARKDOWN_EXT:
            text = _mask_markdown(text)
            if "livespec:" not in text:
                continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for m in MARKER_RE.finditer(line):
                markers.append(
                    Marker(
                        slug=m.group("slug"),
                        ids=m.group("ids").split(","),
                        file=str(path.relative_to(root)),
                        line=lineno,
                        raw=m.group(0),
                    )
                )
    return markers


# ---------------------------------------------------------------- findings

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


@dataclass
class Finding:
    check: str
    severity: str      # error | warning | info
    message: str
    file: str | None = None
    line: int | None = None
    item: str | None = None
    feature: str | None = None
    spec_ref: str | None = None   # e.g. "§8.2"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class Report:
    def __init__(self, tool: str, project: Project, scope: str | None = None):
        self.tool = tool
        self.project = project
        self.scope = scope
        self.findings: list[Finding] = []
        self.stats: dict = {}
        self.notes: list[str] = []

    def add(self, **kwargs) -> None:
        self.findings.append(Finding(**kwargs))

    def sorted_findings(self) -> list[Finding]:
        return sorted(
            self.findings,
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.check, f.file or "", f.line or 0),
        )

    def to_dict(self) -> dict:
        counts: dict = {}
        for f in self.findings:
            counts[f.check] = counts.get(f.check, 0) + 1
        return {
            "tool": self.tool,
            "project": {
                "root": str(self.project.root),
                "name": self.project.name,
                "mode": self.project.mode,
                "features": len(self.project.features),
                "concepts": len(self.project.concepts),
            },
            "scope": self.scope,
            "stats": self.stats,
            "notes": self.notes,
            "counts_by_check": counts,
            "counts_by_severity": {
                sev: sum(1 for f in self.findings if f.severity == sev)
                for sev in ("error", "warning", "info")
            },
            "findings": [f.to_dict() for f in self.sorted_findings()],
        }

    def render(self, out=sys.stdout) -> None:
        d = self.to_dict()
        print(f"{self.tool} — {d['project']['name']}  ({d['project']['root']})", file=out)
        meta = f"mode: {d['project']['mode']}  features: {d['project']['features']}  concepts: {d['project']['concepts']}"
        if self.scope:
            meta += f"  scope: {self.scope}"
        print(meta, file=out)
        for key, value in self.stats.items():
            print(f"  {key}: {value}", file=out)
        for note in self.notes:
            print(f"  note: {note}", file=out)
        print(file=out)

        if not self.findings:
            print("No findings.", file=out)
            return

        current = None
        for f in self.sorted_findings():
            head = f"{f.severity}/{f.check}"
            if head != current:
                current = head
                count = sum(
                    1 for x in self.findings if x.check == f.check and x.severity == f.severity
                )
                ref = f"  ({f.spec_ref})" if f.spec_ref else ""
                print(f"[{f.severity.upper()}] {f.check} — {count}{ref}", file=out)
            loc = f.file or ""
            if f.line:
                loc = f"{loc}:{f.line}"
            print(f"  {loc}  {f.message}", file=out)
        print(file=out)
        sev = d["counts_by_severity"]
        print(
            f"Total: {len(self.findings)} "
            f"({sev['error']} error, {sev['warning']} warning, {sev['info']} info)",
            file=out,
        )


def emit(report: Report, as_json: bool) -> int:
    """Print the report. Exit code is 0 even with findings: this is a diagnostic,
    not a quality gate (LiveSpec describes the software, not the work on it)."""
    if as_json:
        json.dump(report.to_dict(), sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        report.render()
    return 0


def resolve_project(arg: str | None, cwd: Path) -> Project:
    """Resolve the project to check, or exit(2) with an actionable message."""
    if arg:
        root = Path(arg).expanduser().resolve()
        if root.is_file() and root.name == "livespec.yaml":
            root = root.parent
        if not (root / "livespec.yaml").is_file():
            print(f"error: no livespec.yaml in {root}", file=sys.stderr)
            raise SystemExit(2)
        return load_project(root)

    candidates = find_projects(cwd)
    if not candidates:
        print(
            "error: no livespec.yaml found. Pass the project root explicitly "
            "(see SPEC.md §3.1 for common locations).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if len(candidates) > 1:
        listing = "\n".join(f"  {c}" for c in candidates)
        print(
            "error: several LiveSpec projects found; pass one explicitly:\n" + listing,
            file=sys.stderr,
        )
        raise SystemExit(2)
    return load_project(candidates[0])
