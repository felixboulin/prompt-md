import argparse
from pathlib import Path
import logging


try:
    import pyperclip
except ImportError:
    pyperclip = None

from .core import inject
from .call_openai_api import call_openai_api


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

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
        print("sending ..")
        try:
            answer = call_openai_api(result)
        except Exception as e:
            print(f"❌ Failed to send prompt: {e}")
            return
        out = args.mdfile.with_name(f"{args.mdfile.stem}-ans{args.mdfile.suffix}")
        out.write_text(answer, encoding="utf-8")
        print(f"✅ LLM response saved → {out}")
