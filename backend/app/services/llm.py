import json
import logging
import re
import time
import requests
from backend.app.core.config import settings

logger = logging.getLogger("smart_screener.llm")

def call_gemini_api(prompt: str, system_instruction: str = "") -> str:
    """Call Google Gemini API using google-genai package."""
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )
    if system_instruction:
        config.system_instruction = system_instruction
        
    response = client.models.generate_content(
        model=settings.LLM_MODEL if "gemini" in settings.LLM_MODEL else "gemini-2.5-flash",
        contents=prompt,
        config=config
    )
    return response.text


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
            if settings.GEMINI_API_KEY:
                raw_response = call_gemini_api(prompt, system_instruction)
            # Or try OpenAI if key exists
            elif settings.OPENAI_API_KEY:
                raw_response = call_openai_api(prompt, system_instruction)
            else:
                # No API key provided -> Return None so caller uses fallback engine
                return None

            if raw_response:
                # Clean up JSON formatting if LLM added markdown backticks
                clean_json_str = raw_response.strip()
                if clean_json_str.startswith("```json"):
                    clean_json_str = clean_json_str[7:]
                if clean_json_str.startswith("```"):
                    clean_json_str = clean_json_str[3:]
                if clean_json_str.endswith("```"):
                    clean_json_str = clean_json_str[:-3]
                clean_json_str = clean_json_str.strip()
                
                return json.loads(clean_json_str)

        except Exception as e:
            logger.warning(f"LLM API Call Attempt {attempt+1} failed: {e}")
            if attempt < max_retries:
                time.sleep(1.0)
            else:
                logger.error(f"All {max_retries+1} LLM API attempts failed.")
                
    return None
