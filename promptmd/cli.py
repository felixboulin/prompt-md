import argparse
from pathlib import Path
import pyperclip
from .core import inject

try:
    import pyperclip
except ImportError:
    pyperclip = None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mdfile", type=Path)
    p.add_argument("--send", action="store_true")
    args = p.parse_args()

    result = inject(args.mdfile)
    if pyperclip:
        pyperclip.copy(result)
        print("📋  Copied to clipboard.")
    else:
        print("⚠️  pyperclip not available — clipboard copy skipped.")

    if args.send:
        print("sending")
