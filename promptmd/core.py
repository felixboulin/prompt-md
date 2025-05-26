import re
from pathlib import Path
import sys
import subprocess
import logging
import shlex

CODE_FENCE_RE = re.compile(r"(```.*?```)", re.DOTALL)


def inject(markdown_path: Path, seen: set = None) -> str:
    abs_path = str(markdown_path.resolve())
    if not markdown_path.exists():
        logging.error(f"❌ Input markdown file not found: {abs_path}")
        raise FileNotFoundError(f"{markdown_path} does not exist")

    if seen is None:
        seen = set()
    if markdown_path in seen:
        raise ValueError(f"❌ Circular include detected: {markdown_path}")
    seen.add(markdown_path)

    text = markdown_path.read_text(encoding="utf-8")
    parent_of_md = markdown_path.parent.parent
    current_folder = markdown_path.parent

    def replace(match, seen=seen):
        expr = match.group(1).strip()
        COMMENT_PREFIX = {
            "py": "#",
            "js": "//",
            "ts": "//",
            "json": "//",
            "sh": "#",
            "bash": "#",
            "html": "<!--",
            "css": "/*",
            "yml": "#",
            "yaml": "#",
            "sql": "--",
            "toml": "#",
        }

        if expr.startswith("include"):
            included_file = expr.split("include", 1)[1].strip()
            include_path = current_folder / included_file
            if not include_path.exists():
                logging.error(f"❌ Included file not found: {include_path}")
                return f"```txt\n# ERROR: Included file not found: {included_file}\n```"
            try:
                # Recursively inject the included file
                return inject(include_path, seen=seen)
            except Exception as e:
                logging.exception(f"Error including file: {include_path}")
                return f"```txt\n# ERROR: Failed to include {included_file}: {e}\n```"

        elif expr.startswith("tree"):
            if ";" in expr or "&&" in expr:
                raise ValueError(
                    "⚠️  Unsafe shell command blocked: chaining is not allowed."
                )
            try:
                logging.info(f"Running shell command: {expr}")
                cmd = shlex.split(expr)
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=parent_of_md,
                    check=True,
                )
                content = result.stdout
            except subprocess.CalledProcessError as e:
                logging.error(f"Command failed: {expr}\n{e.stderr}")
                content = f"*ERROR running command `{expr}`: {e.stderr.strip()}*"
            except Exception as e:
                logging.exception("Unexpected error running shell command")
                content = f"*ERROR running command `{expr}`: {e}*"
            return f"```bash\n$ {expr}\n{content.rstrip()}\n```"

        else:
            target = parent_of_md / expr
            if not target.exists():
                logging.warning(f"File not found: {target}")
                content = f"*ERROR: {expr} not found*"
                return f"```txt\n# Missing file: {expr}\n{content.rstrip()}\n```"

            content = target.read_text(encoding="utf-8")
            ext = Path(expr).suffix.lstrip(".") or "txt"
            prefix = COMMENT_PREFIX.get(ext, "#")

            # Get the relative path again for LLM context
            rel_path = str(Path(expr))  # keep path as written in {{ ... }}

            if prefix == "<!--":
                comment = f"{prefix} File: {rel_path} -->"
            elif prefix == "/*":
                comment = f"{prefix} File: {rel_path} */"
            else:
                comment = f"{prefix} File: {rel_path}"

            return f"```{ext}\n{comment}\n{content.rstrip()}\n```"

    # Split text into segments inside and outside code fences
    parts = CODE_FENCE_RE.split(text)
    for idx, part in enumerate(parts):
        # Even indexes are outside code fences
        if idx % 2 == 0:
            # lambda function: closure
            parts[idx] = re.sub(
                r"\{\{\s*(.*?)\s*\}\}", lambda m: replace(m, seen), part
            )
    return "".join(parts)
