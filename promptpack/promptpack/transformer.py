import re
import json


def _remove_blank_lines(lines: list) -> list:
    return [l for l in lines if l.strip()]


def _strip_python(src: str, keep_blanks: bool = False) -> str:
    lines = src.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith('"""') or stripped.startswith("'''"):
            char = stripped[:3]
            rest = stripped[3:]
            if char in rest:
                i += 1
                continue
            i += 1
            while i < len(lines):
                if char in lines[i]:
                    break
                i += 1
            i += 1
            continue

        code_part = re.sub(r'(?<!["\'])#[^\n]*', '', line).rstrip()
        if code_part.strip():
            out.append(code_part)
        elif keep_blanks and out and out[-1] != "":
            out.append("")

        i += 1

    if keep_blanks:
        while out and out[-1] == "":
            out.pop()
        result = []
        prev_blank = False
        for l in out:
            if l == "":
                if not prev_blank:
                    result.append(l)
                prev_blank = True
            else:
                result.append(l)
                prev_blank = False
        return "\n".join(result)

    return "\n".join(out)


def _strip_c_style(src: str, keep_blanks: bool = False) -> str:
    src = re.sub(r'/\*[\s\S]*?\*/', '', src)
    lines = src.splitlines()
    out = []
    for line in lines:
        code = re.sub(r'//[^\n]*', '', line).rstrip()
        if code.strip():
            out.append(code)
        elif keep_blanks and out and out[-1] != "":
            out.append("")

    if keep_blanks:
        while out and out[-1] == "":
            out.pop()
        result = []
        prev_blank = False
        for l in out:
            if l == "":
                if not prev_blank:
                    result.append(l)
                prev_blank = True
            else:
                result.append(l)
                prev_blank = False
        return "\n".join(result)

    return "\n".join(out)


def _strip_hash_style(src: str, keep_blanks: bool = False) -> str:
    lines = src.splitlines()
    out = []
    for line in lines:
        code = re.sub(r'(?<!["\'])#[^\n]*', '', line).rstrip()
        if code.strip():
            out.append(code)
        elif keep_blanks and out and out[-1] != "":
            out.append("")

    if keep_blanks:
        while out and out[-1] == "":
            out.pop()
        result = []
        prev_blank = False
        for l in out:
            if l == "":
                if not prev_blank:
                    result.append(l)
                prev_blank = True
            else:
                result.append(l)
                prev_blank = False
        return "\n".join(result)

    return "\n".join(out)


def _strip_html_style(src: str) -> str:
    src = re.sub(r'<!--[\s\S]*?-->', '', src)
    lines = [l.strip() for l in src.splitlines() if l.strip()]
    return "\n".join(lines)


def _minify_json(src: str) -> str:
    try:
        obj = json.loads(src)
        return json.dumps(obj, separators=(',', ':'))
    except (json.JSONDecodeError, ValueError):
        return "\n".join(l for l in src.splitlines() if l.strip())


def _minify_css(src: str) -> str:
    src = re.sub(r'/\*[\s\S]*?\*/', '', src)
    src = re.sub(r'\s+', ' ', src)
    src = re.sub(r'\s*([{};:,>+~])\s*', r'\1', src)
    return src.strip()


def _strip_markdown(src: str) -> str:
    lines = [l.rstrip() for l in src.splitlines() if l.strip()]
    return "\n".join(lines)


C_STYLE_LANGS = {
    "js", "ts", "jsx", "tsx", "java", "c", "cpp", "h", "hpp",
    "cs", "go", "rs", "swift", "kt", "scala", "dart", "php",
}

HASH_STYLE_LANGS = {
    "rb", "sh", "yaml", "toml", "r", "lua", "tf", "hcl", "nix",
}


def transform(content: str, lang: str, keep_blanks: bool = False) -> str:
    if lang == "py":
        return _strip_python(content, keep_blanks=keep_blanks)
    if lang in C_STYLE_LANGS:
        return _strip_c_style(content, keep_blanks=keep_blanks)
    if lang in HASH_STYLE_LANGS:
        return _strip_hash_style(content, keep_blanks=keep_blanks)
    if lang in ("html", "xml"):
        return _strip_html_style(content)
    if lang == "json":
        return _minify_json(content)
    if lang in ("css", "scss", "sass", "less"):
        return _minify_css(content)
    if lang == "md":
        return _strip_markdown(content)
    lines = [l.rstrip() for l in content.splitlines() if l.strip()]
    return "\n".join(lines)
