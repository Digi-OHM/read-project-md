from __future__ import annotations

import os
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog

import chardet

# ── Constants ─────────────────────────────────────────────────────────────────

OUTPUT_FILE   = "project-Info.md"
IGNORE_CONFIG = "read.projectignore"
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

ALLOW_EXTENSIONS: frozenset[str] = frozenset({
    ".html", ".ts", ".scss", ".css", ".js",
    ".json", ".md", ".txt",
})

_SEC_INFO    = "[PROJECT_INFO]"
_SEC_TREE    = "[TREE_IGNORE]"
_SEC_CONTENT = "[CONTENT_IGNORE]"


# ── Config ────────────────────────────────────────────────────────────────────

@dataclass
class IgnoreConfig:
    project_info : list[str]      = field(default_factory=list)
    tree_rules   : frozenset[str] = field(default_factory=frozenset)
    content_rules: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def load(cls, project_path: Path) -> IgnoreConfig:
        ignore_file = project_path / IGNORE_CONFIG
        if not ignore_file.exists():
            return cls()

        project_info : list[str] = []
        tree_rules   : set[str]  = set()
        content_rules: set[str]  = set()
        section = None

        for raw in ignore_file.read_text(encoding="utf-8").splitlines():
            line   = raw.rstrip("\n\r")
            marker = line.strip()

            if marker == _SEC_INFO:
                section = "info"
                continue
            if marker == _SEC_TREE:
                section = "tree"
                continue
            if marker == _SEC_CONTENT:
                section = "content"
                continue

            if section == "info":
                project_info.append(line)
                continue

            if not marker or marker.startswith("#"):
                continue

            if section == "tree":
                tree_rules.add(marker.lower())
            elif section == "content":
                content_rules.add(marker.lower())

        return cls(project_info, frozenset(tree_rules), frozenset(content_rules))


# ── File helpers ──────────────────────────────────────────────────────────────

def _detect_encoding(path: Path) -> str:
    try:
        raw = path.read_bytes()[:4096]
        return chardet.detect(raw).get("encoding") or "utf-8"
    except Exception:
        return "utf-8"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding=_detect_encoding(path), errors="ignore")
    except Exception:
        return ""


# ── Ignore matching ───────────────────────────────────────────────────────────

def _matches(path: Path, project_path: Path, rule: str) -> bool:
    rel   = path.relative_to(project_path).as_posix().lower()
    parts = rel.split("/")
    name  = path.name.lower()
    ext   = path.suffix.lower()

    return (
        rule in parts
        or name == rule
        or name.endswith(rule)
        or (rule.startswith(".") and ext == rule)
    )


def _is_tree_ignored(path: Path, project_path: Path, rules: frozenset[str]) -> bool:
    return any(_matches(path, project_path, r) for r in rules)


def _is_content_ignored(path: Path, project_path: Path, rules: frozenset[str]) -> bool:
    return any(_matches(path, project_path, r) for r in rules)


# ── Tree builder ──────────────────────────────────────────────────────────────

def _build_tree(project_path: Path, tree_rules: frozenset[str]) -> str:
    lines: list[str] = [project_path.name]

    def _walk(current: Path, prefix: str = "") -> None:
        try:
            items = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        visible = [p for p in items if not _is_tree_ignored(p, project_path, tree_rules)]

        for idx, item in enumerate(visible):
            last      = idx == len(visible) - 1
            connector = "└── " if last else "├── "
            lines.append(f"{prefix}{connector}{item.name}")
            if item.is_dir():
                _walk(item, prefix + ("    " if last else "│   "))

    _walk(project_path)
    return "\n".join(lines)


# ── File collector ────────────────────────────────────────────────────────────

def _collect_files(project_path: Path, tree_rules: frozenset[str]) -> list[Path]:
    files: list[Path] = []

    for root, dirs, filenames in os.walk(project_path):
        root_path = Path(root)
        dirs[:] = [
            d for d in dirs
            if not _is_tree_ignored(root_path / d, project_path, tree_rules)
        ]
        files.extend(root_path / name for name in filenames)

    return files


# ── Markdown generator ────────────────────────────────────────────────────────

def generate_markdown(project_path: Path) -> None:
    cfg   = IgnoreConfig.load(project_path)
    lines : list[str] = [f"# Project: {project_path.name}", ""]

    if cfg.project_info:
        lines += ["## Project Information", "", "```text", *cfg.project_info, "```", ""]

    lines += [
        "## Project Structure", "",
        "```text",
        _build_tree(project_path, cfg.tree_rules),
        "```", "",
    ]

    total = 0
    for file in _collect_files(project_path, cfg.tree_rules):
        if (
            file.is_dir()
            or file.suffix.lower() not in ALLOW_EXTENSIONS
            or file.stat().st_size > MAX_FILE_SIZE
            or _is_content_ignored(file, project_path, cfg.content_rules)
        ):
            continue

        total += 1
        rel = file.relative_to(project_path)
        ext = file.suffix.lstrip(".") or "text"
        lines += [f"## {rel}", "", f"```{ext}", _read_text(file), "```", ""]

    output = Path(__file__).parent / OUTPUT_FILE
    output.write_text("\n".join(lines), encoding="utf-8")

    print("✅ Done")
    print(f"📄 {output}")
    print(f"📦 Files processed: {total}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    root = tk.Tk()
    root.withdraw()

    folder = filedialog.askdirectory(title="Select Project Folder")
    if folder:
        generate_markdown(Path(folder))
    else:
        print("No folder selected.")


if __name__ == "__main__":
    main()
