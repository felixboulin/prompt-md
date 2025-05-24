import os
import requests
import logging

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

_SYSTEM_PROMPT = (
    "You are an expert programmer answering code questions from collaborators. "
    "In all your replies, wrap code in markdown code fences that include the "
    "file extension for syntax highlighting."
)


def get_api_key(env_var_name: str) -> str:
    api_key = os.getenv(env_var_name)
    if not api_key:
        raise RuntimeError(f"Missing {env_var_name} environment variable")
    return api_key


def send_request(url: str, headers: dict, payload: dict, timeout: int) -> dict:
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Network or HTTP error when sending request", exc_info=True)
        raise RuntimeError(f"❌ Network or HTTP error: {e}")
    return response.json()


def handle_response(response: dict, api_name: str) -> str:
    if "choices" in response:
        return response["choices"][0]["message"]["content"]
    elif "content" in response:
        return response["content"][0]["text"]
    else:
        logging.error(f"{api_name} API error: unexpected response format")
        raise RuntimeError(f"❌ {api_name} API returned unexpected response format.")


def call_anthropic_api(
    prompt: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    api_key = get_api_key("ANTHROPIC_API_KEY")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    payload = {
        "model": model,
        "system": _SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    response = send_request(ANTHROPIC_URL, headers, payload, timeout=90)
    return handle_response(response, "Anthropic")


def call_openai_api(prompt: str, model: str = "gpt-4.1") -> str:
    api_key = get_api_key("OPENAI_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    response = send_request(OPENAI_URL, headers, payload, timeout=60)
    return handle_response(response, "OpenAI")
