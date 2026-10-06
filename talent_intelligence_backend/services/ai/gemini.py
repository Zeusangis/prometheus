import json
import os
import time

# Operators can override this with GEMINI_MODEL when a different available model
# is required for their account or region.
DEFAULT_MODEL = "gemini-flash-lite-latest"
# Transient provider failures (5xx, transport, short rate limits) are retried with
# exponential backoff so one demand spike does not fail a whole analysis.
RETRY_ATTEMPTS = 3
RETRY_BASE_SECONDS = 1.0
RETRY_MAX_SECONDS = 8.0
# A provider that asks us to wait longer than this is telling us the budget is gone
# for a long window (for example a daily free-tier quota). Retrying would only spend
# more of a very small budget, so we stop and let the recruiter see the real reason.
RETRY_MAX_SERVER_DELAY = 60.0


class ProviderUnavailable(RuntimeError):
    pass


class InvalidProviderOutput(ValueError):
    pass


def _int_env(name, default):
    try:
        return max(1, int(os.environ.get(name, "").strip() or default))
    except ValueError:
        return default


def _float_env(name, default):
    try:
        return max(0.0, float(os.environ.get(name, "").strip() or default))
    except ValueError:
        return default


def configured_model():
    return os.environ.get("GEMINI_MODEL", "").strip() or DEFAULT_MODEL


def provider_status():
    """Readiness for operators and the health endpoint. Never exposes the key itself."""
    return {
        "resume_provider_configured": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
        "resume_model": configured_model(),
    }


def _status_code(error):
    raw = getattr(error, "code", None) or getattr(error, "status_code", None)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _retry_details(error):
    """Yield the ``details`` entries the SDK attached to a provider error."""
    details = getattr(error, "details", None)
    if not isinstance(details, dict):
        return
    entries = details.get("error", {}).get("details")
    if isinstance(entries, list):
        yield from entries


def server_retry_delay(error):
    """Seconds the provider asked us to wait, or ``None`` when it did not say."""
    for entry in _retry_details(error):
        if not isinstance(entry, dict):
            continue
        raw = entry.get("retryDelay") if entry.get("@type", "").endswith("RetryInfo") else None
        if isinstance(raw, str) and raw.endswith("s"):
            try:
                return float(raw[:-1])
            except ValueError:
                return None
    return None


def is_transient(error):
    """True only for failures a later identical call may resolve."""
    module = type(error).__module__ or ""
    if module.startswith(("httpx", "httpcore")):
        return True
    if not module.startswith(("google.genai", "google.api_core")):
        return False
    if _status_code(error) in (408, 409, 429):
        return True
    text = str(error).upper()
    if "RESOURCE_EXHAUSTED" in text or "UNAVAILABLE" in text or "DEADLINE_EXCEEDED" in text:
        return True
    status = _status_code(error)
    return status is not None and status >= 500


def classify_provider_error(error):
    """Map SDK/transport failures to a safe, actionable message.

    Returns ``None`` for errors that are not provider failures, so a real bug in our
    own call still surfaces instead of being reported as an outage.
    """
    module = type(error).__module__ or ""
    text = str(error).upper()
    status = _status_code(error)
    if module.startswith(("httpx", "httpcore")):
        return ProviderUnavailable(
            "AI provider could not be reached from the server. Check outbound network access and retry."
        )
    if not module.startswith(("google.genai", "google.api_core")):
        return None
    if status in (401, 403) or "API_KEY_INVALID" in text:
        return ProviderUnavailable(
            "AI provider rejected the credentials. Set a valid GEMINI_API_KEY in the backend .env and retry."
        )
    if status == 404 or "NOT_FOUND" in text:
        return ProviderUnavailable(
            "AI provider does not recognise the configured model. Set GEMINI_MODEL to an available model and retry."
        )
    if status == 429 or "RESOURCE_EXHAUSTED" in text:
        return ProviderUnavailable(
            "AI provider quota or rate limit reached. Free-tier keys allow only a small "
            "number of requests per day and per model; retry once the window resets, or "
            "raise the quota for this key."
        )
    if status is not None and status >= 500:
        return ProviderUnavailable("AI provider is temporarily unavailable. Retry later.")
    if status == 400:
        return ProviderUnavailable(
            "AI provider rejected the request. Check GEMINI_MODEL and the analysis schema, then retry."
        )
    return ProviderUnavailable("AI provider request failed. Retry later.")


def generate_json(prompt, schema, model=None):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ProviderUnavailable(
            "Resume AI analysis is unavailable: no GEMINI_API_KEY is configured on the server."
        )
    # Import and initialize only inside the worker call, never during Flask boot.
    from google import genai
    from google.genai import types

    model = model or configured_model()
    attempts = _int_env("GEMINI_RETRY_ATTEMPTS", RETRY_ATTEMPTS)
    base = _float_env("GEMINI_RETRY_BASE_SECONDS", RETRY_BASE_SECONDS)
    response = None
    for attempt in range(1, attempts + 1):
        try:
            with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60_000)) as client:
                response = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json", response_json_schema=schema,
                        temperature=0.2,
                    ),
                )
            break
        except Exception as error:
            unavailable = classify_provider_error(error)
            if unavailable is None:
                # Not a provider failure: a bug in our own call must still surface.
                raise
            if attempt >= attempts or not is_transient(error):
                raise unavailable from error
            requested = server_retry_delay(error)
            if requested is not None and requested > RETRY_MAX_SERVER_DELAY:
                # A long-window quota: retrying would only spend more of a tiny budget.
                raise unavailable from error
            time.sleep(requested if requested is not None else min(base * (2 ** (attempt - 1)), RETRY_MAX_SECONDS))
    text = getattr(response, "text", None)
    if not text:
        raise InvalidProviderOutput("AI returned no structured data to analyse.")
    try:
        value = json.loads(text)
    except ValueError as error:
        raise InvalidProviderOutput("AI returned invalid structured data.") from error
    if not isinstance(value, dict):
        raise InvalidProviderOutput("AI returned invalid structured data.")
    return value, model
