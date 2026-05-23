from __future__ import annotations

import logging
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


# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s  %(message)s",
    datefmt= "%H:%M:%S",
)
log = logging.getLogger("read-project-md")


# ── Toast notification ────────────────────────────────────────────────────────

def _show_toast(title: str, message: str, kind: str = "success") -> None:
    COLORS = {
        "success": {"bg": "#22c55e", "fg": "#ffffff", "icon": "✅"},
        "error":   {"bg": "#ef4444", "fg": "#ffffff", "icon": "❌"},
    }
    c = COLORS.get(kind, COLORS["success"])

    toast = tk.Tk()
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(bg=c["bg"])
    toast.attributes("-alpha", 0.95)

    frame = tk.Frame(toast, bg=c["bg"], padx=20, pady=14)
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame,
        text=f"{c['icon']}  {title}",
        bg=c["bg"], fg=c["fg"],
        font=("Segoe UI", 11, "bold"),
        anchor="w",
    ).pack(fill="x")

    tk.Label(
        frame,
        text=message,
        bg=c["bg"], fg=c["fg"],
        font=("Segoe UI", 9),
        anchor="w",
        wraplength=280,
        justify="left",
    ).pack(fill="x", pady=(4, 0))

    toast.update_idletasks()
    w  = toast.winfo_width()
    h  = toast.winfo_height()
    sw = toast.winfo_screenwidth()
    sh = toast.winfo_screenheight()
    toast.geometry(f"{w}x{h}+{sw - w - 24}+{sh - h - 64}")

    def _close():
        toast.destroy()
        toast.quit()

    toast.after(3500, _close)
    toast.mainloop()


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
            log.warning("⚠️  No read.projectignore found — running without ignore rules")
            return cls()

        log.info("📋 Config     : %s", ignore_file)

        project_info : list[str] = []
        tree_rules   : set[str]  = set()
        content_rules: set[str]  = set()
        section = None

        for raw in ignore_file.read_text(encoding="utf-8").splitlines():
            line   = raw.rstrip("\n\r")
            marker = line.strip()

            if marker == _SEC_INFO:    section = "info";    continue
            if marker == _SEC_TREE:    section = "tree";    continue
            if marker == _SEC_CONTENT: section = "content"; continue

            if section == "info":
                project_info.append(line)
                continue

            if not marker or marker.startswith("#"):
                continue

            if section == "tree":
                tree_rules.add(marker.lower())
            elif section == "content":
                content_rules.add(marker.lower())

        log.info("🌲 Tree rules  : %d entries", len(tree_rules))
        log.info("🚫 Skip rules  : %d entries", len(content_rules))

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
        log.warning("⚠️  Could not read: %s", path)
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
            log.warning("⚠️  Permission denied: %s", current)
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
    log.info("━" * 50)
    log.info("📁 Project    : %s", project_path.name)
    log.info("📍 Path       : %s", project_path)
    log.info("━" * 50)

    cfg = IgnoreConfig.load(project_path)

    log.info("🌲 Building project tree...")
    lines: list[str] = [f"# Project: {project_path.name}", ""]

    if cfg.project_info:
        lines += ["## Project Information", "", "```text", *cfg.project_info, "```", ""]

    lines += [
        "## Project Structure", "",
        "```text",
        _build_tree(project_path, cfg.tree_rules),
        "```", "",
    ]

    log.info("🔍 Scanning files...")

    total        = 0
    skip_ext     = 0
    skip_size    = 0
    skip_content = 0

    for file in _collect_files(project_path, cfg.tree_rules):
        if file.is_dir():
            continue

        rel = file.relative_to(project_path)

        if file.suffix.lower() not in ALLOW_EXTENSIONS:
            log.info("   ⊘  %-45s  [extension not allowed]", rel)
            skip_ext += 1
            continue

        if file.stat().st_size > MAX_FILE_SIZE:
            size_mb = file.stat().st_size / 1024 / 1024
            log.warning("   ⊘  %-45s  [too large: %.1f MB]", rel, size_mb)
            skip_size += 1
            continue

        if _is_content_ignored(file, project_path, cfg.content_rules):
            log.info("   ⊘  %-45s  [content ignored]", rel)
            skip_content += 1
            continue

        log.info("   ✔  %s", rel)
        total += 1
        ext = file.suffix.lstrip(".") or "text"
        lines += [f"## {rel}", "", f"```{ext}", _read_text(file), "```", ""]

    output = Path.cwd() / OUTPUT_FILE
    output.write_text("\n".join(lines), encoding="utf-8")

    total_skipped = skip_ext + skip_size + skip_content

    log.info("━" * 50)
    log.info("✅ Output      : %s", output)
    log.info("📦 Included    : %d files", total)
    log.info("⊘  Skipped     : %d files", total_skipped)
    log.info("   ├ ext       : %d", skip_ext)
    log.info("   ├ ignored   : %d", skip_content)
    log.info("   └ too large : %d", skip_size)
    log.info("━" * 50)

    _show_toast(
        title   = "Done!",
        message = f"{project_path.name}\n{total} included · {total_skipped} skipped",
        kind    = "success",
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    root = tk.Tk()
    root.withdraw()

    log.info("🗂️  Waiting for folder selection...")
    folder = filedialog.askdirectory(title="Select Project Folder")

    if not folder:
        log.info("⚠️  No folder selected — exiting.")
        return

    try:
        generate_markdown(Path(folder))
    except Exception as e:
        log.error("❌ Failed: %s", e, exc_info=True)
        _show_toast(title="Error", message=str(e), kind="error")


if __name__ == "__main__":
    main()
    os._exit(0)