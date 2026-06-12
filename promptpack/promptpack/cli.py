import argparse
import sys
from pathlib import Path

from .scanner import scan
from .transformer import transform
from .serializer import serialize, write


def _resolve_project_path(target: str) -> Path:
    p = Path(target)
    if p.is_absolute() and p.exists():
        return p.resolve()
    cwd = Path.cwd()
    candidate = cwd / target
    if candidate.exists():
        return candidate.resolve()
    script_dir = Path(sys.argv[0]).resolve().parent
    candidate2 = script_dir / target
    if candidate2.exists():
        return candidate2.resolve()
    return cwd / target


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n/1024:.1f}KB"
    return f"{n/1024/1024:.2f}MB"


def main():
    parser = argparse.ArgumentParser(
        prog="promptpack",
        description="Pack a project into a compact AI-readable XML snapshot.",
    )
    parser.add_argument("project", help="Project folder name or path")
    parser.add_argument("-o", "--output", default=None, help="Output file path")
    parser.add_argument("--no-transform", action="store_true", help="Skip minification")
    parser.add_argument("--keep-blanks", action="store_true", help="Keep single blank lines between blocks")
    parser.add_argument("--no-tree", action="store_true", help="Omit directory tree")
    parser.add_argument("--ignore", nargs="*", default=[], help="Extra glob patterns to ignore")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout")

    args = parser.parse_args()

    project_path = _resolve_project_path(args.project)
    if not project_path.exists():
        print(f"error: not found: {project_path}", file=sys.stderr)
        sys.exit(1)
    if not project_path.is_dir():
        print(f"error: not a directory: {project_path}", file=sys.stderr)
        sys.exit(1)

    project_name = project_path.name
    print(f"scanning {project_path} ...")

    raw_total = 0
    collected = []
    for rel_path, lang, content in scan(project_path, extra_ignore=args.ignore):
        raw_total += len(content)
        if not args.no_transform:
            content = transform(content, lang, keep_blanks=args.keep_blanks)
        if content.strip():
            collected.append((rel_path, lang, content))

    xml_output, stats = serialize(
        project_name=project_name,
        files=collected,
        include_tree=not args.no_tree,
    )

    transformed_chars = sum(len(c) for _, _, c in collected)
    ratio = (1 - transformed_chars / raw_total) * 100 if raw_total else 0
    xml_ratio = (1 - stats["output_chars"] / raw_total) * 100 if raw_total else 0

    print(f"files     : {stats['files']}")
    print(f"source    : {_fmt_size(raw_total)} ({raw_total // 4:,} tokens est.)")
    print(f"packed    : {_fmt_size(stats['output_chars'])} (~{stats['output_tokens']:,} tokens)")
    print(f"reduction : {xml_ratio:.1f}%")

    if args.stdout:
        print(xml_output)
        return

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = project_path.parent / f"{project_name}.promptpack.xml"

    write(out_path, xml_output)
    print(f"output    : {out_path}")
