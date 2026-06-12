# promptpack

> Pack any project folder into a compact, AI-readable XML snapshot.  
> Strip noise. Keep signal. Cut your context window usage by ~50%.

[![PyPI version](https://img.shields.io/pypi/v/promptpack.svg)](https://pypi.org/project/promptpack/)
[![Python Versions](https://img.shields.io/pypi/pyversions/promptpack.svg)](https://pypi.org/project/promptpack/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-AchillesHubTeam-181717?logo=github)](https://github.com/AchillesHubTeam)

---

## What is promptpack?

When you paste an entire codebase into an AI prompt, you waste most of your context window on blank lines, comments, docstrings, and repeated path prefixes. **promptpack** solves this by scanning your project and producing a single `.promptpack.xml` file that contains everything the AI needs — nothing more.

**What it does:**
- Strips all comments, docstrings, and blank lines from source files
- Minifies JSON files to single-line
- Groups files by directory to avoid repeating path prefixes
- Renders the directory tree using compact Unicode box-drawing characters
- Skips irrelevant files: `node_modules`, `dist`, `tests`, `docs`, lock files, binaries, `.env` secrets, changelogs, licenses, and more
- Respects `.gitignore` patterns automatically

**Typical result: ~50% reduction in token count** compared to pasting raw source files.

---

## Install

```bash
pip install promptpack
```

Requires Python 3.8 or higher. No external dependencies.

---

## Quick start

```bash
# Pack a project folder next to it
promptpack my-app

# Pack a project anywhere using its path
promptpack ./path/to/my-app

# Custom output path
promptpack my-app -o context.xml

# Print to stdout (pipe into clipboard, etc.)
promptpack my-app --stdout

# macOS: copy directly to clipboard
promptpack my-app --stdout | pbcopy
```

After running, paste the contents of `my-app.promptpack.xml` into your AI prompt:

```
Here is my full project snapshot:

[paste contents of my-app.promptpack.xml]

Now help me...
```

---

## Output format

The output uses compact abbreviated XML tags to minimize token usage:

```xml
<?xml version="1.0" encoding="utf-8"?>
<proj n="my-app" files="23" tokens="~4800">
<tree>├─package.json
├─tsconfig.json
└─src/
  ├─index.ts
  ├─app.ts
  └─utils/
    ├─helper.ts
    └─types.ts</tree>
<f p="package.json" l="json">{"name":"my-app","version":"1.0.0","scripts":{"dev":"ts-node src/index.ts"}}</f>
<d p="src">
<f n="index.ts" l="ts">import {createApp} from './app'
const app = createApp()
app.listen(3000)</f>
</d>
</proj>
```

### Tag reference

| Tag | Attribute | Meaning |
|-----|-----------|---------|
| `<proj>` | `n` | project name |
| `<proj>` | `files` | total file count included |
| `<proj>` | `tokens` | estimated token count of packed content |
| `<tree>` | — | directory structure with box-drawing chars |
| `<d>` | `p` | directory path (groups files to avoid path repetition) |
| `<f>` | `p` | file path (top-level files) |
| `<f>` | `n` | file name (files inside a `<d>` block) |
| `<f>` | `l` | language identifier |

### Language identifiers

`py` `js` `ts` `jsx` `tsx` `java` `c` `cpp` `go` `rs` `rb` `php`  
`swift` `kt` `cs` `dart` `lua` `sh` `sql` `html` `css` `scss`  
`json` `yaml` `toml` `md` `gql` `proto` `tf` `docker` `nix` …

---

## CLI options

```
usage: promptpack [-h] [-o OUTPUT] [--no-transform] [--keep-blanks]
                  [--no-tree] [--ignore [IGNORE ...]] [--stdout]
                  project
```

| Flag | Description |
|------|-------------|
| `project` | Folder name or path to pack |
| `-o`, `--output` | Custom output file path |
| `--no-transform` | Skip all minification (raw source content) |
| `--keep-blanks` | Keep one blank line between code blocks (less aggressive) |
| `--no-tree` | Omit the directory tree from output |
| `--ignore PATTERN` | Additional glob patterns to exclude |
| `--stdout` | Print XML to stdout instead of writing a file |

---

## What gets included vs excluded

**Included by default:**
- All source code files (`.py`, `.ts`, `.js`, `.go`, `.rs`, `.java`, …)
- Config files (`.json`, `.yaml`, `.toml`, `.env.example`, …)
- Build scripts (`Dockerfile`, `Makefile`, `.sh`, …)
- Root-level documentation (`README.md`)

**Excluded by default:**
- `node_modules/`, `__pycache__/`, `.git/`, `venv/`, `dist/`, `build/`
- `tests/`, `test/`, `__tests__/`, `spec/`, `e2e/`
- `docs/`, `doc/`, `examples/`, `fixtures/`, `stubs/`, `vendor/`
- Lock files: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `*.lock`
- Minified files: `*.min.js`, `*.min.css`, `*.map`
- Binary files: images, fonts, executables, archives
- Secret files: `.env`, `.env.local`, `.env.production`
- Documentation text: `*.txt`, `*.rst`, `CHANGELOG*`, `LICENSE*`, `AUTHORS*`
- Any file over 512 KB
- All patterns listed in `.gitignore`

You can add extra patterns at runtime:

```bash
promptpack my-app --ignore "*.test.ts" "migrations/"
```

---

## Minification details

| Language | What gets stripped |
|----------|--------------------|
| Python | Inline `#` comments, docstrings (`"""..."""`, `'''...'''`), blank lines |
| JS / TS / Go / Java / C++ / Rust / … | `//` line comments, `/* */` block comments, blank lines |
| Ruby / Shell / YAML / TOML / … | `#` line comments, blank lines |
| HTML / XML | `<!-- -->` comments, blank lines |
| JSON | Reformatted to single-line with no spaces |
| CSS / SCSS | `/* */` comments, excess whitespace between selectors |
| Markdown | Trailing whitespace, consecutive blank lines |

---

## Benchmark

Tested on [Flask](https://github.com/pallets/flask) source (31 source files, excluding tests and docs):

| | Size | Est. tokens |
|--|------|-------------|
| Raw source | 349 KB | ~89,400 |
| promptpack output | 173 KB | ~44,200 |
| **Reduction** | **50.6%** | **50.6%** |

---

## Programmatic usage

You can use promptpack as a library inside your own scripts:

```python
from pathlib import Path
from promptpack.scanner import scan
from promptpack.transformer import transform
from promptpack.serializer import serialize, write

project = Path("./my-app")

files = []
for rel_path, lang, content in scan(project):
    minified = transform(content, lang)
    if minified.strip():
        files.append((rel_path, lang, minified))

xml_output, stats = serialize(project_name="my-app", files=files)

print(f"Files: {stats['files']}")
print(f"Tokens: ~{stats['output_tokens']:,}")

write(Path("my-app.promptpack.xml"), xml_output)
```

---

## Publishing / contributing

This project is open source under the MIT license.

- **GitHub:** [https://github.com/AchillesHubTeam/promptpack](https://github.com/AchillesHubTeam/promptpack)
- **PyPI:** [https://pypi.org/project/promptpack](https://pypi.org/project/promptpack)
- **Issues:** [https://github.com/AchillesHubTeam/promptpack/issues](https://github.com/AchillesHubTeam/promptpack/issues)

Pull requests are welcome.

---

## License

[MIT](./LICENSE) © [AchillesHubTeam](https://github.com/AchillesHubTeam)
