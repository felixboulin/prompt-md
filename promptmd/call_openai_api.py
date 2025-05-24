import os
import requests
import logging


def call_openai_api(prompt: str, model: str = "gpt-4o") -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    system_prompt = (
        "You are an expert programmer answering code questions from collaborators. "
        "In all your replies, you surround the code blocks into a markdown code block "
        "that always includes the file extension for syntax highlighting."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60,
        )
    except requests.exceptions.RequestException as e:
        logging.error("Network error when calling OpenAI API", exc_info=True)
        raise RuntimeError(f"❌ Network error: {e}")

    if not response.ok:
        logging.error(f"OpenAI API error: {response.status_code}\n{response.text}")
        raise RuntimeError(
            f"❌ Request to OpenAI failed with status {response.status_code}.\n"
            f"Details: {response.text.strip()[:300]}..."  # truncate long errors
        )

    return response.json()["choices"][0]["message"]["content"]
