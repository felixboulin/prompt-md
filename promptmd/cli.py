import argparse
from pathlib import Path
import logging
from .model_config import MODEL_CONFIG


try:
    import pyperclip
except ImportError:
    pyperclip = None

from .core import inject

from .api_utils import call_openai_api, call_anthropic_api

CALL_API_FN = {
    "openai": call_openai_api,
    "anthropic": call_anthropic_api,
}


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
    p.add_argument("--provider", choices=["openai", "anthropic"], default="openai")
    p.add_argument(
        "--level", choices=["small", "medium", "large", "default"], default="default"
    )
    p.add_argument("--model", help="Override default model for the chosen provider")
    args = p.parse_args()

    prompt = inject(args.mdfile)
    if pyperclip:
        pyperclip.copy(prompt)
        out = args.mdfile.with_name(f"{args.mdfile.stem}-prompt{args.mdfile.suffix}")
        out.write_text(prompt, encoding="utf-8")
        print("prompt saved →", out)
        print("📋  Copied to clipboard.")
        print("📝 Word count:", len(prompt.split()))
        approx_tokens = int(len(prompt) / 2.5)
        print("🧠 Estimated token count:", approx_tokens)
    else:
        print("⚠️  pyperclip not available — clipboard copy skipped.")

    if args.send:
        print("sending ..")
        try:
            model = args.model or MODEL_CONFIG[args.provider][args.level]
            api_fn = CALL_API_FN.get(args.provider)
            if not api_fn:
                raise RuntimeError(f"❌ Unsupported provider: {args.provider}")
            response = api_fn(prompt, model=model)

        except Exception as e:
            print(f"❌ Failed to send prompt: {e}")
            return
        out = args.mdfile.with_name(f"{args.mdfile.stem}-ans{args.mdfile.suffix}")
        out.write_text(response["content"], encoding="utf-8")
        print(f"✅ LLM response saved → {out}")

        input_toks = response.get("input_tokens")
        output_toks = response.get("output_tokens")
        total_toks = (input_toks or 0) + (output_toks or 0)
        print("📊 Token usage:")
        print(f"  ⤷ Input tokens:     {input_toks}")
        print(f"  ⤷ Output tokens:    {output_toks}")
        print(f"  ⤷ Total tokens:     {total_toks}")
