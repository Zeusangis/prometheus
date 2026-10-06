import json
import os


class ProviderUnavailable(RuntimeError):
    pass


class InvalidProviderOutput(ValueError):
    pass


def generate_json(prompt, schema, model=None):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ProviderUnavailable("Resume AI analysis is unavailable: GEMINI_API_KEY is not configured.")
    # Import and initialize only inside the worker call, never during Flask boot.
    from google import genai
    from google.genai import types

    model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    with genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60_000)) as client:
        response = client.models.generate_content(
            model=model, contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_json_schema=schema,
                temperature=0.2,
            ),
        )
    try:
        value = json.loads(response.text or "")
    except (TypeError, ValueError) as error:
        raise InvalidProviderOutput("AI returned invalid structured data.") from error
    if not isinstance(value, dict):
        raise InvalidProviderOutput("AI returned invalid structured data.")
    return value, model
