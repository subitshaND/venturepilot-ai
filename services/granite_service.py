"""
granite_service.py
──────────────────
IBM watsonx.ai integration for VenturePilot AI.

Authentication flow
───────────────────
IBM watsonx.ai uses IAM (Identity and Access Management) bearer tokens.
Every request to the generation endpoint must carry a short-lived access
token obtained by exchanging the API key against the IBM IAM token URL.

Environment variables (loaded from .env via python-dotenv)
──────────────────────────────────────────────────────────
  GRANITE_API_KEY      – IBM Cloud API key
  GRANITE_API_URL      – watsonx.ai endpoint base URL
                         e.g. https://eu-de.ml.cloud.ibm.com
  GRANITE_PROJECT_ID   – watsonx.ai project ID (from the project settings)
  GRANITE_MODEL_ID     – Model deployment ID
                         e.g. ibm/granite-4-h-small
"""

import os
import logging

import requests
from dotenv import load_dotenv

# ── Load environment variables from .env (no-op if already loaded) ──────────
load_dotenv()

# ── Module-level logger ──────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ── IBM IAM token endpoint (public, never changes) ───────────────────────────
_IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

# ── watsonx.ai chat endpoint (required for instruct/chat-tuned models) ────────
# granite-4-h-small is a structured-chat model; /ml/v1/text/chat is the correct
# endpoint. /ml/v1/text/generation only works for base completion models.
_CHAT_PATH = "/ml/v1/text/chat?version=2024-05-31"

# ── Default model ID (used when GRANITE_MODEL_ID is not set in .env) ─────────
# Valid watsonx.ai model IDs use the "ibm/" prefix, not "ibm-granite/".
# Full list: https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/fm-models.html
# "ibm/granite-4-h-small" is the current instruct-capable Granite model in eu-de.
_DEFAULT_MODEL_ID = "ibm/granite-4-h-small"


# ────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    """
    Read and validate all required credentials from environment variables.

    Returns:
        dict: Containing api_key, api_url, project_id, model_id.

    Raises:
        EnvironmentError: If any required variable is missing or empty.
    """
    required = {
        "api_key":    "GRANITE_API_KEY",
        "api_url":    "GRANITE_API_URL",
        "project_id": "GRANITE_PROJECT_ID",
    }

    config = {}
    missing = []

    for key, env_var in required.items():
        value = os.getenv(env_var, "").strip()
        if not value:
            missing.append(env_var)
        config[key] = value

    # GRANITE_MODEL_ID is optional; fall back to the known-good default.
    config["model_id"] = os.getenv("GRANITE_MODEL_ID", "").strip() or _DEFAULT_MODEL_ID

    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Please set them in your .env file."
        )

    # Normalise: strip trailing slash from the base URL
    config["api_url"] = config["api_url"].rstrip("/")

    return config


def _get_iam_token(api_key: str) -> str:
    """
    Exchange an IBM Cloud API key for a short-lived IAM bearer token.

    IBM IAM tokens expire after 60 minutes. For production use you would
    cache the token and only refresh when it nears expiry. This
    implementation fetches a fresh token on every call to keep the service
    stateless and simple.

    Args:
        api_key (str): IBM Cloud API key.

    Returns:
        str: The IAM access token string.

    Raises:
        RuntimeError: If the token exchange fails.
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": api_key,
    }

    logger.debug("Requesting IAM token from %s", _IAM_TOKEN_URL)

    try:
        response = requests.post(
            _IAM_TOKEN_URL,
            headers=headers,
            data=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("IAM token request timed out. Check your network connection.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"IAM token request failed: {exc}") from exc

    token_data = response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise RuntimeError(
            "IAM response did not contain an access_token. "
            f"Response body: {token_data}"
        )

    logger.debug("IAM token obtained successfully.")
    return access_token


# Per-call completion token cap enforced server-side by the watsonx.ai project
# tier. Probing confirmed the server hard-limits each response to 1024 tokens
# regardless of the max_new_tokens value sent in the request.
_MAX_NEW_TOKENS = 1024

# Maximum continuation rounds before giving up (safety valve).
_MAX_CONTINUATIONS = 20


def _call_chat(
    chat_url: str,
    headers: dict,
    model_id: str,
    project_id: str,
    messages: list,
) -> tuple:
    """
    Make one call to the watsonx.ai chat endpoint.

    Args:
        chat_url   : Full watsonx.ai chat endpoint URL.
        headers    : Auth + content-type headers.
        model_id   : watsonx.ai model ID.
        project_id : watsonx.ai project ID.
        messages   : Conversation history as a list of role/content dicts.

    Returns:
        (content, finish_reason) — finish_reason is "stop" or "length".

    Raises:
        RuntimeError : HTTP or network error.
        ValueError   : Unexpected response structure.
    """
    payload = {
        "model_id": model_id,
        "project_id": project_id,
        "messages": messages,
        "parameters": {
            "max_new_tokens": _MAX_NEW_TOKENS,
            "temperature": 0.5,
            "top_p": 0.95,
        },
    }

    try:
        response = requests.post(chat_url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "The watsonx.ai chat request timed out. "
            "The model may be under heavy load — please try again."
        )
    except requests.exceptions.HTTPError as exc:
        try:
            error_body = response.json()
        except Exception:
            error_body = response.text
        raise RuntimeError(
            f"watsonx.ai API returned HTTP {response.status_code}: {error_body}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"watsonx.ai API request failed: {exc}") from exc

    try:
        choice = response.json()["choices"][0]
        return choice["message"]["content"], choice.get("finish_reason", "stop")
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(
            f"Unexpected API response structure: {response.json()}"
        ) from exc


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────

def generate_startup_blueprint(startup_data: dict) -> str:
    print("===== GRANITE FUNCTION CALLED =====")
    """
    Generate a complete AI-powered startup blueprint using IBM Granite.

    End-to-end flow:
      1. Load and validate credentials from environment variables.
      2. Build the structured prompt from the startup form data.
      3. Exchange the API key for a short-lived IAM bearer token.
      4. POST the generation request to the watsonx.ai REST endpoint.
      5. Extract and return the generated text from the response.

    Args:
        startup_data (dict): Form fields submitted by the user, expected keys:
            - startup_name    (str) : Name of the startup
            - founder_name    (str) : Founder's name (optional)
            - industry        (str) : Industry sector
            - startup_idea    (str) : Description of the idea / problem
            - target_audience (str) : Target customer segment
            - business_stage  (str) : Current development stage

    Returns:
        str: The AI-generated business blueprint as plain text.

    Raises:
        EnvironmentError : One or more required env vars are missing.
        RuntimeError     : IAM authentication or API call failed.
        ValueError       : The API returned an unexpected response structure.
    """

    # ── Step 1: Load credentials ─────────────────────────────────────────────
    config = _load_config()
    logger.info(
        "Generating blueprint for startup='%s' using model='%s'",
        startup_data.get("startup_name", "unknown"),
        config["model_id"],
    )

    # ── Step 2: Build the structured prompt ──────────────────────────────────
    # Import here to avoid circular imports; the prompt module is a pure helper.
    from prompts.startup_prompt import build_startup_prompt  # noqa: PLC0415
    prompt = build_startup_prompt(startup_data)
    logger.debug("Prompt length: %d characters", len(prompt))

    # ── Step 3: Obtain a fresh IAM bearer token ───────────────────────────────
    access_token = _get_iam_token(config["api_key"])

    # ── Step 4: Call the watsonx.ai chat endpoint, continuing if truncated ────
    # The project tier hard-caps each response at 1024 completion tokens.
    # We detect finish_reason="length" and loop: each round appends the partial
    # assistant turn to the conversation history and asks the model to continue,
    # building up the full report across multiple calls.
    chat_url = config["api_url"] + _CHAT_PATH

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    messages = [{"role": "user", "content": prompt}]
    parts: list[str] = []
    model_id = config["model_id"]
    project_id = config["project_id"]

    for round_num in range(1, _MAX_CONTINUATIONS + 1):
        logger.debug("Chat round %d — sending %d message(s)", round_num, len(messages))
        content, finish_reason = _call_chat(
            chat_url, headers, model_id, project_id, messages
        )
        parts.append(content)
        logger.debug(
            "Round %d complete: finish_reason=%s, chars=%d",
            round_num, finish_reason, len(content),
        )

        if finish_reason != "length":
            # Model reached a natural stopping point — we are done.
            break

        # Truncated: append assistant turn + a continuation nudge, then loop.
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": "Continue."})
    else:
        logger.warning(
            "Reached maximum continuation rounds (%d). "
            "Report may still be incomplete.",
            _MAX_CONTINUATIONS,
        )

    # ── Step 5: Assemble the full report ─────────────────────────────────────
    generated_text = "".join(parts).strip()

    if not generated_text:
        raise ValueError("The model returned an empty response. Try again.")

    logger.info(
        "Blueprint generated in %d round(s), %d characters total.",
        len(parts), len(generated_text),
    )
    print(generated_text)
    return generated_text
