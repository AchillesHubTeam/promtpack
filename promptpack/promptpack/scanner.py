import os
import fnmatch
from pathlib import Path
from typing import Iterator, Tuple
from .config import DEFAULT_IGNORE_DIRS, DEFAULT_IGNORE_FILES, LANGUAGE_MAP, MAX_FILE_BYTES


def _load_gitignore_patterns(root: Path) -> list:
    gi = root / ".gitignore"
    if not gi.exists():
        return []
    patterns = []
    with open(gi, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def _matches_any(name: str, patterns: list) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def _is_ignored_file(filename: str) -> bool:
    for pat in DEFAULT_IGNORE_FILES:
        if fnmatch.fnmatch(filename, pat):
            return True
    return False


def _detect_language(path: Path) -> str:
    name = path.name.lower()
    if name == "dockerfile":
        return "docker"
    if name == "makefile":
        return "make"
    if name == "gemfile":
        return "ruby"
    if name == ".env.example":
        return "env"
    suffix = path.suffix.lower()
    return LANGUAGE_MAP.get(suffix, "txt")


def _is_binary(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
        return b"\x00" in chunk
    except OSError:
        return True


def scan(root: Path, extra_ignore: list = None) -> Iterator[Tuple[str, str, str]]:
    gitignore = _load_gitignore_patterns(root)
    extra = extra_ignore or []

    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        rel_dir = current.relative_to(root)

        dirnames[:] = [
            d for d in sorted(dirnames)
            if d not in DEFAULT_IGNORE_DIRS
            and not _matches_any(d, gitignore)
            and not _matches_any(d, extra)
            and not d.startswith(".")
        ]

        for filename in sorted(filenames):
            if _is_ignored_file(filename):
                continue
            if _matches_any(filename, gitignore):
                continue
            if _matches_any(filename, extra):
                continue

            filepath = current / filename
            if filepath.stat().st_size > MAX_FILE_BYTES:
                continue
            if _is_binary(filepath):
                continue

            rel_path = str(filepath.relative_to(root)).replace("\\", "/")
            lang = _detect_language(filepath)

            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            yield rel_path, lang, content
