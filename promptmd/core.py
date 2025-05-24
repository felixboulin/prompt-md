import re
from pathlib import Path
import sys
import subprocess

CODE_FENCE_RE = re.compile(r"(```.*?```)", re.DOTALL)


def inject(markdown_path: Path) -> str:
    text = markdown_path.read_text(encoding="utf-8")
    parent_of_md = markdown_path.parent.parent

    def replace(match):
        expr = match.group(1).strip()
        if expr.startswith("tree"):
            try:
                result = subprocess.run(
                    expr, shell=True, capture_output=True, text=True, cwd=parent_of_md
                )
                content = result.stdout if result.returncode == 0 else result.stderr
            except Exception as e:
                content = f"*ERROR running command `{expr}`: {e}*"
            return f"```bash\n$ {expr}\n{content.rstrip()}\n```"
        else:
            target = parent_of_md / expr
            if not target.exists():
                print(f"Warning: file not found: {target}", file=sys.stderr)
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
