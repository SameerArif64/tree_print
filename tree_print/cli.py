#!/usr/bin/env python3
from pathlib import Path
from typing import List, Set
import argparse
import fnmatch
import subprocess
import re
import pyperclip
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)
COLOR_DIR = Fore.BLUE + Style.BRIGHT
COLOR_FILE = Fore.RESET

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub("", text)

def human_readable_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"

def matches_patterns(name: str, patterns: List[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) for pat in patterns)

def get_git_tracked_files(root: Path) -> Set[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        return set(Path(root / line.strip()) for line in result.stdout.splitlines())
    except subprocess.CalledProcessError:
        return set()

def collapse_single_dirs(path: Path, git_tracked: Set[Path] | None = None, exclude: List[str] | None = None) -> Path:
    if exclude is None:
        exclude = []

    while True:
        items = [item for item in path.iterdir() if not matches_patterns(item.name, exclude)]
        if git_tracked is not None:
            items = [item for item in items if item in git_tracked or any(p.is_relative_to(item) for p in git_tracked if p.is_file())]
        dirs = [d for d in items if d.is_dir()]
        files = [f for f in items if f.is_file()]

        if len(dirs) == 1 and not files:
            path = dirs[0]
        else:
            break
    return path

def build_tree_lines(
    startpath: Path,
    indent: str = "",
    exclude: List[str] | None = None,
    git_tracked: Set[Path] | None = None,
    color: bool = True,
    show_sizes: bool = True,
    compact: bool = False,
    depth: int | None = None,
    current_level: int = 0
) -> List[str]:
    if exclude is None:
        exclude = []

    if compact:
        startpath = collapse_single_dirs(startpath, git_tracked, exclude)

    items = sorted(
        (item for item in startpath.iterdir() if not matches_patterns(item.name, exclude)),
        key=lambda x: (x.is_file(), x.name.lower())
    )

    if git_tracked is not None:
        items = [item for item in items if item in git_tracked or any(p.is_relative_to(item) for p in git_tracked if p.is_file())]

    lines = []
    for i, item in enumerate(items):
        if depth is not None and current_level >= depth:
            continue

        connector = "└── " if i == len(items) - 1 else "├── "
        name = f"{COLOR_DIR}{item.name}{Style.RESET_ALL}" if color and item.is_dir() else f"{COLOR_FILE}{item.name}{Style.RESET_ALL}"
        size = f" ({human_readable_size(item.stat().st_size)})" if show_sizes and item.is_file() else ""
        lines.append(indent + connector + name + size)

        if item.is_dir():
            extension = "    " if i == len(items) - 1 else "│   "
            lines.extend(build_tree_lines(item, indent + extension, exclude, git_tracked, color, show_sizes, compact, depth, current_level + 1))
    return lines

def main():
    parser = argparse.ArgumentParser(description="Git-aware enhanced cross-platform directory tree printer.")
    parser.add_argument("path", type=str, help="Root directory path to print the tree from")
    parser.add_argument("-e", "--exclude", type=str, nargs="*", default=[], help="Files/folders to exclude")
    parser.add_argument("-G", "--git", action="store_true", help="Only show git-tracked files/folders")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--no-size", action="store_true", help="Hide file sizes")
    parser.add_argument("-c", "--compact", action="store_true", help="Collapse single-child directories")
    parser.add_argument("-L", "--depth", type=int, help="Limit the depth of the tree")
    parser.add_argument("--clipboard", action="store_true", help="Copy tree output to clipboard instead of printing")
    args = parser.parse_args()

    root_path = Path(args.path)
    if not root_path.exists():
        print(f"Error: Path '{root_path}' does not exist.")
        return

    git_tracked = get_git_tracked_files(root_path) if args.git else None

    lines = build_tree_lines(
        root_path,
        exclude=args.exclude,
        git_tracked=git_tracked,
        color=not args.no_color,
        show_sizes=not args.no_size,
        compact=args.compact,
        depth=args.depth
    )

    output = "\n".join(lines)
    if args.clipboard:
        pyperclip.copy(strip_ansi(output))
        print("Tree copied to clipboard!")
    else:
        print(output)

if __name__ == "__main__":
    main()
