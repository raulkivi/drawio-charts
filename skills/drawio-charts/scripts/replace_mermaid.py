#!/usr/bin/env python3
"""Find Mermaid blocks in Markdown and swap them for draw.io images.

Usage:
  python3 replace_mermaid.py list PATH... [--json]   plan: every ```mermaid block,
                                                     its type and a suggested image
  python3 replace_mermaid.py apply PLAN.json         replace each block whose image
                                                     exists; keep the Mermaid in a comment
  python3 replace_mermaid.py restore FILE...         undo: put the Mermaid blocks back

A replaced block becomes:

  ![Title](diagrams/title.drawio.svg)

  <!-- mermaid-source: diagrams/title.drawio.svg
  ```mermaid
  ...original lines, with "-->" escaped so the comment can't end early...
  ```
  -->

Blocks inside other fences or inside HTML comments are left alone, so running
apply again changes nothing. Images go in a diagrams/ folder next to each file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SUPPORTED = ("flowchart", "sequence", "er", "class", "state")
TYPE_KEYWORDS = {
    "flowchart": "flowchart", "graph": "flowchart", "sequencediagram": "sequence", "erdiagram": "er",
    "classdiagram": "class", "classdiagram-v2": "class", "statediagram": "state", "statediagram-v2": "state",
}
MARKDOWN_SUFFIXES = (".md", ".markdown")
IMAGE_DIR = "diagrams"
FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
SOURCE_MARKER = re.compile(r"^(\s*)<!-- mermaid-source: (.+)$")


@dataclass
class Block:
    index: int
    start: int          # 0-based line of the opening fence
    end: int            # 0-based line of the closing fence
    indent: str
    code: str
    kind: str
    title: str | None

    @property
    def supported(self) -> bool:
        return self.kind in SUPPORTED

    @property
    def sha(self) -> str:
        return hashlib.sha256(self.code.encode()).hexdigest()[:16]


def diagram_type(code: str) -> str:
    lines = [line.strip() for line in code.splitlines()]
    i = 0
    while i < len(lines) and not lines[i]:
        i += 1
    if i < len(lines) and lines[i] == "---":   # YAML front matter
        i += 1
        while i < len(lines) and lines[i] != "---":
            i += 1
        i += 1
    for line in lines[i:]:
        if not line or line.startswith("%%"):
            continue
        word = line.split()[0].lower()
        return TYPE_KEYWORDS.get(word, word)
    return "unknown"


def find_blocks(text: str) -> list[Block]:
    lines = [line.rstrip("\r") for line in text.split("\n")]
    blocks: list[Block] = []
    heading: str | None = None
    in_comment = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if in_comment:
            in_comment = "-->" not in line
            i += 1
            continue
        opening = FENCE_OPEN.match(line)
        if opening:
            indent, fence, info = opening.groups()
            if fence[0] == "`" and "`" in info:
                i += 1
                continue
            close = _find_close(lines, i + 1, fence)
            if close is None:
                break  # unclosed fence runs to the end of the file
            if info.strip().lower().split(" ")[0:1] == ["mermaid"]:
                code_lines = [_dedent(l, indent) for l in lines[i + 1:close]]
                code = "\n".join(code_lines) + ("\n" if code_lines else "")
                blocks.append(Block(len(blocks), i, close, indent, code, diagram_type(code),
                                    _front_matter_title(code) or heading))
            i = close + 1
            continue
        if "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            in_comment = True
        elif match := HEADING.match(line):
            heading = match.group(1) or heading
        i += 1
    return blocks


def plan_files(paths: list[Path]) -> list[dict]:
    plan = []
    used: dict[Path, set[str]] = {}
    for path in _markdown_files(paths):
        folder = path.parent / IMAGE_DIR
        taken = used.setdefault(folder, {p.name for p in folder.glob("*")} if folder.is_dir() else set())
        for block in find_blocks(_read(path)):
            base = _slug(block.title) or f"{path.stem}-diagram-{block.index + 1}"
            name, n = f"{base}.drawio.svg", 2
            while name in taken:
                name, n = f"{base}-{n}.drawio.svg", n + 1
            taken.add(name)
            plan.append({
                "file": str(path), "index": block.index, "line": block.start + 1, "type": block.kind,
                "supported": block.supported, "title": block.title or base.replace("-", " ").capitalize(),
                "image": f"{IMAGE_DIR}/{name}", "sha": block.sha,
            })
    return plan


def apply_plan(plan: list[dict]) -> dict:
    replaced, skipped = 0, []
    by_file: dict[str, list[dict]] = {}
    for entry in plan:
        by_file.setdefault(entry["file"], []).append(entry)
    for file, entries in by_file.items():
        path = Path(file)
        text = _read(path)
        lines = text.split("\n")
        eol = "\r" if "\r\n" in text else ""
        blocks = find_blocks(text)
        for entry in sorted(entries, key=lambda e: e["index"], reverse=True):
            reason = _skip_reason(entry, blocks, path, text)
            if reason:
                skipped.append({"file": file, "index": entry["index"], "reason": reason})
                continue
            block = blocks[entry["index"]]
            lines[block.start:block.end + 1] = _replacement(block, lines[block.start:block.end + 1],
                                                            entry["title"], entry["image"], eol)
            replaced += 1
        new_text = "\n".join(lines)
        if new_text != text:
            _write(path, new_text)
    skipped.sort(key=lambda s: (s["file"], s["index"]))
    return {"replaced": replaced, "skipped": skipped}


def restore_text(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        marker = SOURCE_MARKER.match(lines[i].rstrip("\r"))
        if not marker:
            out.append(lines[i])
            i += 1
            continue
        indent, image = marker.group(1), marker.group(2).strip()
        end = next((j for j in range(i + 1, len(lines)) if lines[j].rstrip("\r") == f"{indent}-->"), None)
        if end is None:
            out.append(lines[i])
            i += 1
            continue
        if len(out) >= 2 and not out[-1].strip() and out[-2].strip().endswith(f"]({image})"):
            del out[-2:]
        out.extend(_unescape(line) for line in lines[i + 1:end])
        i = end + 1
    return "\n".join(out)


# --- helpers ---------------------------------------------------------------

def _read(path: Path) -> str:
    # newline="" keeps CRLF files byte-for-byte; plain text mode would rewrite them as LF
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def _write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _find_close(lines: list[str], start: int, fence: str) -> int | None:
    closing = re.compile(rf"^\s*{re.escape(fence[0])}{{{len(fence)},}}\s*$")
    return next((j for j in range(start, len(lines)) if closing.match(lines[j])), None)


def _dedent(line: str, indent: str) -> str:
    return line[len(indent):] if line.startswith(indent) else line.lstrip()


def _front_matter_title(code: str) -> str | None:
    lines = code.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        if key.strip() == "title" and value.strip():
            return value.strip().strip("\"'")
    return None


def _slug(title: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")[:60].strip("-")


def _markdown_files(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(p for p in path.rglob("*") if p.suffix.lower() in MARKDOWN_SUFFIXES and p.is_file()))
        elif path.suffix.lower() in MARKDOWN_SUFFIXES:
            found.append(path)
    return found


def _skip_reason(entry: dict, blocks: list[Block], path: Path, text: str) -> str | None:
    if not entry.get("supported", entry.get("type") in SUPPORTED):
        return f"unsupported type {entry.get('type')}"
    index = entry["index"]
    if index >= len(blocks) or blocks[index].sha != entry["sha"]:
        if f"<!-- mermaid-source: {entry['image']}" in text:
            return "already converted"
        return "block changed since the plan was made; run list again"
    if not (path.parent / entry["image"]).is_file():
        return f"image {entry['image']} does not exist"
    return None


def _replacement(block: Block, raw: list[str], title: str, image: str, eol: str) -> list[str]:
    alt = title.replace("[", "(").replace("]", ")")
    return ([f"{block.indent}![{alt}]({image}){eol}", eol, f"{block.indent}<!-- mermaid-source: {image}{eol}"]
            + [_escape(line) for line in raw]
            + [f"{block.indent}-->{eol}"])


def _escape(line: str) -> str:
    """Make a line safe inside an HTML comment, reversibly."""
    return line.replace("--&", "--&amp;").replace("-->", "--&gt;").replace("--!>", "--!&gt;")


def _unescape(line: str) -> str:
    return line.replace("--!&gt;", "--!>").replace("--&gt;", "-->").replace("--&amp;", "--&")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    list_cmd = commands.add_parser("list", help="plan the conversion")
    list_cmd.add_argument("paths", nargs="+", type=Path)
    list_cmd.add_argument("--json", action="store_true", help="print the plan as JSON (input for apply)")
    apply_cmd = commands.add_parser("apply", help="replace blocks listed in a plan")
    apply_cmd.add_argument("plan", type=Path)
    restore_cmd = commands.add_parser("restore", help="put converted Mermaid blocks back")
    restore_cmd.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)

    if args.command == "list":
        plan = plan_files(args.paths)
        if args.json:
            print(json.dumps(plan, indent=2))
        else:
            for e in plan:
                status = "ok" if e["supported"] else "unsupported"
                print(f"{e['file']}:{e['line']}  #{e['index']}  {e['type']:<10} {status:<12} -> {e['image']}")
            print(f"{len(plan)} block(s), {sum(e['supported'] for e in plan)} supported")
        return 0
    if args.command == "apply":
        report = apply_plan(json.loads(args.plan.read_text(encoding="utf-8")))
        print(f"replaced {report['replaced']}, skipped {len(report['skipped'])}")
        for s in report["skipped"]:
            print(f"  {s['file']} #{s['index']}: {s['reason']}")
        return 0
    for path in args.files:
        text = _read(path)
        restored = restore_text(text)
        if restored != text:
            _write(path, restored)
            print(f"restored {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
