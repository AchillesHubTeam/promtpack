import json
from pathlib import Path
from typing import List, Tuple


def _estimate_tokens(char_count: int) -> int:
    return max(1, char_count // 4)


def _build_tree(files: List[Tuple[str, str, str]]) -> str:
    node = {}
    for path, _, _ in files:
        parts = path.split("/")
        cur = node
        for part in parts[:-1]:
            cur = cur.setdefault(part + "/", {})
        cur[parts[-1]] = None

    lines = []

    def walk(d: dict, prefix: str):
        entries = sorted(d.keys(), key=lambda k: (k.endswith("/"), k.lower()))
        for idx, key in enumerate(entries):
            is_last = idx == len(entries) - 1
            connector = "\u2514\u2500" if is_last else "\u251c\u2500"
            child_prefix = prefix + ("  " if is_last else "\u2502 ")
            lines.append(f"{prefix}{connector}{key}")
            if d[key] is not None:
                walk(d[key], child_prefix)

    walk(node, "")
    return "\n".join(lines)


def _build_dir_groups(files: List[Tuple[str, str, str]]) -> dict:
    groups = {}
    for path, lang, content in files:
        parts = path.split("/")
        dir_key = "/".join(parts[:-1]) if len(parts) > 1 else ""
        groups.setdefault(dir_key, []).append((parts[-1], lang, content, path))
    return groups


def _xml_escape(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def serialize(
    project_name: str,
    files: List[Tuple[str, str, str]],
    include_tree: bool = True,
) -> Tuple[str, dict]:
    raw_chars = sum(len(c) for _, _, c in files)
    tokens = _estimate_tokens(raw_chars)

    parts = []
    parts.append('<?xml version="1.0" encoding="utf-8"?>')
    parts.append(f'<proj n="{_xml_escape(project_name)}" files="{len(files)}" tokens="~{tokens}">')

    if include_tree:
        tree = _build_tree(files)
        parts.append(f"<tree>{_xml_escape(tree)}</tree>")

    groups = _build_dir_groups(files)

    for dir_key in sorted(groups.keys()):
        file_list = groups[dir_key]
        if dir_key:
            parts.append(f'<d p="{_xml_escape(dir_key)}">')
        for fname, lang, content, full_path in sorted(file_list, key=lambda x: x[0]):
            attr_p = f'n="{_xml_escape(fname)}"' if dir_key else f'p="{_xml_escape(full_path)}"'
            escaped = _xml_escape(content)
            parts.append(f'<f {attr_p} l="{lang}">{escaped}</f>')
        if dir_key:
            parts.append("</d>")

    parts.append("</proj>")

    output = "\n".join(parts)

    stats = {
        "files": len(files),
        "output_chars": len(output),
        "output_tokens": _estimate_tokens(len(output)),
        "source_chars": raw_chars,
    }

    return output, stats


def write(output_path: Path, content: str) -> None:
    output_path.write_text(content, encoding="utf-8")
