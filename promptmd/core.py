import re
from pathlib import Path
import sys
import subprocess
import logging
import shlex

CODE_FENCE_RE = re.compile(r"(```.*?```)", re.DOTALL)


def inject(markdown_path: Path) -> str:
    abs_path = str(markdown_path.resolve())
    if not markdown_path.exists():
        logging.error(f"❌ Input markdown file not found: {abs_path}")
        raise FileNotFoundError(f"{markdown_path} does not exist")
    text = markdown_path.read_text(encoding="utf-8")
    parent_of_md = markdown_path.parent.parent

    def replace(match):
        expr = match.group(1).strip()
        if expr.startswith("tree"):
            if ";" in expr or "&&" in expr:
                raise ValueError(
                    "⚠️  Unsafe shell command blocked: chaining is not allowed."
                )
            try:
                logging.info(f"Running shell command: {expr}")
                # Safer split
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
            else:
                content = target.read_text(encoding="utf-8")
        return f"```{expr}\n{content.rstrip()}\n```"

    # Split text into segments inside and outside code fences
    parts = CODE_FENCE_RE.split(text)
    for idx, part in enumerate(parts):
        # Even indexes are outside code fences
        if idx % 2 == 0:
            parts[idx] = re.sub(r"\{\{\s*(.*?)\s*\}\}", replace, part)
    return "".join(parts)
