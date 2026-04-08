import streamlit as st
import urllib.request
import urllib.error
import json
import os

_DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def _get_gemini_model() -> str:
    try:
        return st.secrets["gemini"]["MODEL"]
    except KeyError:
        return os.environ.get("GEMINI_MODEL", _DEFAULT_GEMINI_MODEL)

def _call_gemini(prompt: str) -> str:
    api_key = st.secrets["gemini"]["GEMINI_API_KEY"]
    model = _get_gemini_model()
    url = f"{_GEMINI_API_BASE}/{model}:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1024}
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")
        except Exception:
            detail = str(e)
        raise RuntimeError(f"Gemini API error {e.code}: {detail}") from e
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _extract_json_object(text: str) -> dict:
    """Best-effort extraction when the model wraps JSON in extra text."""
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def ai_categorize_ticket(title: str, description: str) -> dict:
    """Returns {category, priority} using Gemini."""
    prompt = f"""You are an IT help desk classifier for Gonzaga University.
Given the ticket below, respond with ONLY a JSON object with two fields:
- "category": one of [Network, Hardware, Software, Account/Access, AV Equipment, Email, Printing, General]
- "priority": one of [Low, Medium, High, Critical]

Ticket Title: {title}
Ticket Description: {description}

Rules:
- Critical = system-wide outage or security breach
- High = user completely blocked from work
- Medium = degraded functionality
- Low = minor inconvenience or question

Respond ONLY with valid JSON, no explanation, no markdown.
Example: {{"category": "Network", "priority": "High"}}"""
    try:
        return _extract_json_object(_call_gemini(prompt))
    except Exception:
        return {"category": "General", "priority": "Medium"}


def ai_suggest_fix(title: str, description: str, category: str) -> str:
    """Returns a step-by-step fix suggestion like Nessus does for vulnerabilities."""
    prompt = f"""You are an expert IT support technician at Gonzaga University.
A ticket has been submitted with the following details:

Title: {title}
Category: {category}
Description: {description}

Respond ONLY with valid JSON matching this schema:
{{
  "diagnostics": ["step", "step"],
  "likely_root_causes": ["cause", "cause"],
  "fix_steps": ["step", "step", "step"],
  "verification": ["check", "check"],
  "prevention": ["advice", "advice"]
}}
No markdown. No extra keys.
Keep each item under 14 words."""
    try:
        result = _extract_json_object(_call_gemini(prompt))
        diagnostics = result.get("diagnostics", [])
        causes = result.get("likely_root_causes", [])
        fixes = result.get("fix_steps", [])
        verification = result.get("verification", [])
        prevention = result.get("prevention", [])

        sections = [
            ("Immediate diagnostics", diagnostics),
            ("Likely root causes", causes),
            ("Fix steps", fixes),
            ("Verification", verification),
            ("Prevention", prevention),
        ]
        lines = []
        for header, items in sections:
            if not isinstance(items, list):
                continue
            cleaned_items = [str(i).strip() for i in items if str(i).strip()]
            if not cleaned_items:
                continue
            lines.append(f"### {header}")
            for idx, item in enumerate(cleaned_items, 1):
                lines.append(f"{idx}. {item}")
            lines.append("")
        return "\n".join(lines).strip()
    except Exception:
        return "AI suggestion unavailable. Please diagnose manually."
