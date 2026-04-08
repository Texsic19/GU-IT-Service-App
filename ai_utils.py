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
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 512}
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
        result = _call_gemini(prompt)
        result = result.replace("```json", "").replace("```", "").strip()
        return json.loads(result)
    except Exception:
        return {"category": "General", "priority": "Medium"}


def ai_suggest_fix(title: str, description: str, category: str) -> str:
    """Returns a step-by-step fix suggestion like Nessus does for vulnerabilities."""
    prompt = f"""You are an expert IT support technician at Gonzaga University.
A ticket has been submitted with the following details:

Title: {title}
Category: {category}
Description: {description}

Provide a clear, step-by-step resolution guide for the IT technician who will handle this ticket.
Format your response as numbered steps. Be specific and practical.
Include:
1. Immediate diagnostic steps
2. Most likely root causes
3. Step-by-step fix instructions
4. How to verify the issue is resolved
5. Any preventive advice

Keep it concise but thorough. Use plain language."""
    try:
        return _call_gemini(prompt)
    except Exception:
        return "AI suggestion unavailable. Please diagnose manually."
