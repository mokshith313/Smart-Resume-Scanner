import json
import logging
import re
import time
import requests
from backend.app.core.config import settings

logger = logging.getLogger("smart_screener.llm")

def call_gemini_api(prompt: str, system_instruction: str = "") -> str:
    """Call Google Gemini API using google-genai package with automatic model fallback."""
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    # Models to try in priority order
    models_to_try = [
        settings.LLM_MODEL,
        "gemini-3.6-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

    last_err = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            logger.warning(f"Gemini API model '{model_name}' failed: {e}. Trying fallback model...")

    if last_err:
        raise last_err
    raise ValueError("Gemini API returned empty response.")


def call_openai_api(prompt: str, system_instruction: str = "") -> str:
    """Call OpenAI API using REST endpoint."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.LLM_MODEL if "gpt" in settings.LLM_MODEL else "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    
    res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
    res.raise_for_status()
    data = res.json()
    return data["choices"][0]["message"]["content"]


def clean_json_response(raw_text: str) -> dict | None:
    """Safely extract and parse JSON object from LLM response text."""
    if not raw_text:
        return None
        
    text = raw_text.strip()
    
    # Remove markdown code fences if present
    if "```" in text:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            text = match.group(1).strip()
            
    # Find JSON object boundaries
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_substring = text[start_idx:end_idx + 1]
        try:
            return json.loads(json_substring)
        except Exception:
            pass

    try:
        return json.loads(text)
    except Exception:
        return None


def execute_llm_json_prompt(prompt: str, system_instruction: str = "", max_retries: int = 2) -> dict | None:
    """
    Executes a structured JSON prompt against configured LLM provider (Gemini or OpenAI).
    Includes automatic retries and JSON cleaning/validation.
    Returns dict on success, None on failure.
    """
    for attempt in range(max_retries + 1):
        try:
            raw_response = None
            
            # Try Gemini first if key exists
            if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 0:
                raw_response = call_gemini_api(prompt, system_instruction)
            # Or try OpenAI if key exists
            elif settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 0:
                raw_response = call_openai_api(prompt, system_instruction)
            else:
                return None

            if raw_response:
                parsed_json = clean_json_response(raw_response)
                if parsed_json:
                    return parsed_json

        except Exception as e:
            logger.warning(f"LLM API Call Attempt {attempt+1} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0)
            else:
                logger.error(f"All {max_retries+1} LLM API attempts failed.")
                
    return None
