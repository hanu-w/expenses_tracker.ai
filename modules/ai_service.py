"""
ExpenseAI — AI Service Module
Handles all Gemini API interactions: smart insights, natural language parsing,
and budget advice — with caching, threading, and rule-based fallbacks.
"""

import os
import re
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional

from config import (
    GEMINI_MODEL, AI_CACHE_TTL_INSIGHTS, AI_CACHE_TTL_BUDGET,
    CATEGORIES, CURRENCY_SYMBOL, DATE_FORMAT,
)

# ─── Lazy SDK import ──────────────────────────────────────────────────────────
_genai_client = None


def _get_client():
    """Lazily initialise the Gemini client; returns None if no key."""
    global _genai_client
    if _genai_client is not None:
        return _genai_client

    api_key = _load_api_key()
    if not api_key:
        return None

    try:
        from google import genai
        _genai_client = genai.Client(api_key=api_key)
        return _genai_client
    except Exception as e:
        print(f"[AI] Failed to initialise Gemini client: {e}")
        return None


def _load_api_key() -> str:
    """Load the Gemini API key from environment / .env file."""
    # 1. Check environment variable first
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key

    # 2. Fallback: read .env file beside config.py
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            os.environ["GEMINI_API_KEY"] = val
                            return val
        except Exception:
            pass
    return ""


def reload_client():
    """Force re-initialise the client (e.g. after key change)."""
    global _genai_client
    _genai_client = None
    # Clear env so _load_api_key re-reads .env
    os.environ.pop("GEMINI_API_KEY", None)
    return _get_client()


def has_api_key() -> bool:
    """Return True if a non-empty API key is available."""
    return bool(_load_api_key())


# ═══════════════════════════════════════════════════════════════════════════════
#  Response Cache
# ═══════════════════════════════════════════════════════════════════════════════

class _Cache:
    """Simple TTL key-value cache."""

    def __init__(self):
        self._store: dict[str, tuple[float, object]] = {}

    def get(self, key: str, ttl: int) -> Optional[object]:
        if key in self._store:
            ts, val = self._store[key]
            if time.time() - ts < ttl:
                return val
            del self._store[key]
        return None

    def set(self, key: str, value: object):
        self._store[key] = (time.time(), value)

    def clear(self):
        self._store.clear()


_cache = _Cache()


# ═══════════════════════════════════════════════════════════════════════════════
#  Low-level API call (runs in worker thread)
# ═══════════════════════════════════════════════════════════════════════════════

def _call_gemini(prompt: str) -> Optional[str]:
    """Send a prompt to Gemini and return the text response, or None."""
    client = _get_client()
    if not client:
        return None
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"[AI] Gemini API error: {e}")
        return None


def _hash_data(data) -> str:
    """Create a short hash from data to use as a cache key."""
    raw = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════════════════
#  1. Smart Insights
# ═══════════════════════════════════════════════════════════════════════════════

def _build_insights_prompt(summary: dict) -> str:
    """Build a prompt for Gemini to analyse spending data."""
    return f"""You are a personal finance advisor analysing spending data.

Spending Summary:
- Total all-time: {summary.get('total', 0):.2f}
- This month: {summary.get('monthly', 0):.2f}
- This week: {summary.get('weekly', 0):.2f}
- Last week: {summary.get('last_week', 0):.2f}
- Budget: {summary.get('budget', 0):.2f}
- Category Breakdown: {json.dumps(summary.get('categories', []))}

Respond with ONLY a valid JSON object (no markdown fencing) in this format:
{{
  "insights": [
    "insight 1",
    "insight 2",
    "insight 3"
  ],
  "suggestion": "one actionable suggestion"
}}

Rules:
- Give exactly 3 short insights (1-2 sentences each) and 1 suggestion
- Be specific using the actual numbers provided
- Use {CURRENCY_SYMBOL} for currency
- Keep the tone friendly and encouraging
- Focus on patterns, not just restating numbers"""


def _parse_insights_response(text: str) -> Optional[dict]:
    """Parse the JSON response from Gemini."""
    try:
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
        data = json.loads(cleaned)
        if "insights" in data and "suggestion" in data:
            return data
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: try to extract any JSON object from the text
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            data = json.loads(match.group())
            if "insights" in data and "suggestion" in data:
                return data
        except json.JSONDecodeError:
            pass

    return None


def _rule_based_insights(summary: dict) -> dict:
    """Fallback rule-based insights when API is unavailable."""
    insights = []
    total = summary.get("total", 0)
    weekly = summary.get("weekly", 0)
    last_week = summary.get("last_week", 0)
    monthly = summary.get("monthly", 0)
    budget = summary.get("budget", 0)
    categories = summary.get("categories", [])

    # Insight 1: Week comparison
    if last_week > 0:
        change = ((weekly - last_week) / last_week) * 100
        if change > 10:
            insights.append(
                f"Your spending is up {change:.0f}% this week compared to last week "
                f"({CURRENCY_SYMBOL}{weekly:,.0f} vs {CURRENCY_SYMBOL}{last_week:,.0f})."
            )
        elif change < -10:
            insights.append(
                f"Great job! Spending is down {abs(change):.0f}% compared to last week."
            )
        else:
            insights.append("Your spending is consistent with last week — steady habits!")
    else:
        insights.append(f"You've spent {CURRENCY_SYMBOL}{weekly:,.0f} this week so far.")

    # Insight 2: Top category
    if categories:
        top = categories[0]
        pct = (top["total"] / total * 100) if total > 0 else 0
        insights.append(
            f"{top['category']} is your largest category at {pct:.0f}% "
            f"({CURRENCY_SYMBOL}{top['total']:,.0f}) of total spending."
        )

    # Insight 3: Budget status
    if budget > 0:
        pct_used = (monthly / budget) * 100
        if pct_used >= 90:
            insights.append(
                f"You've used {pct_used:.0f}% of your monthly budget — consider slowing down."
            )
        elif pct_used >= 50:
            insights.append(
                f"You're at {pct_used:.0f}% of your budget with time left in the month."
            )
        else:
            insights.append(
                f"Budget is on track — only {pct_used:.0f}% used so far this month."
            )
    else:
        insights.append(
            f"Your all-time total is {CURRENCY_SYMBOL}{total:,.0f}. "
            "Setting a budget could help you manage spending better."
        )

    # Fill up to 3
    while len(insights) < 3:
        insights.append("Keep tracking your expenses daily for better financial health.")

    # Suggestion
    suggestion = (
        "Review your top spending category and see if any purchases there are discretionary."
    )
    if budget > 0 and monthly > budget * 0.9:
        suggestion = "Avoid non-essential purchases for the rest of the month to stay within budget."

    return {"insights": insights[:3], "suggestion": suggestion}


def get_smart_insights(
    db,
    on_result: Callable[[dict], None],
    on_error: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
):
    """
    Fetch AI-powered spending insights asynchronously.
    Calls `on_result(data)` on the calling thread (via after()) with:
        {"insights": [str, str, str], "suggestion": str, "source": "ai"|"cache"|"rule"}
    """
    # Build summary from DB
    total = db.get_total()
    weekly = db.get_weekly_total()
    last_week = db.get_last_week_total()
    monthly = db.get_monthly_total()
    budget_str = db.get_setting("monthly_budget", "0")
    budget = float(budget_str) if budget_str else 0
    categories = db.get_category_breakdown()

    summary = {
        "total": total,
        "weekly": weekly,
        "last_week": last_week,
        "monthly": monthly,
        "budget": budget,
        "categories": categories,
    }

    # Check cache
    cache_key = f"insights_{_hash_data(summary)}"
    if not force_refresh:
        cached = _cache.get(cache_key, AI_CACHE_TTL_INSIGHTS)
        if cached:
            cached["source"] = "cache"
            on_result(cached)
            return

    # No API key? Use fallback directly
    if not has_api_key():
        result = _rule_based_insights(summary)
        result["source"] = "rule"
        _cache.set(cache_key, result)
        on_result(result)
        return

    # API call in background thread
    def _worker():
        prompt = _build_insights_prompt(summary)
        raw = _call_gemini(prompt)
        if raw:
            parsed = _parse_insights_response(raw)
            if parsed:
                parsed["source"] = "ai"
                _cache.set(cache_key, parsed)
                on_result(parsed)
                return

        # Fallback
        result = _rule_based_insights(summary)
        result["source"] = "rule"
        _cache.set(cache_key, result)
        if on_error:
            on_error("Could not reach AI — showing rule-based insights")
        on_result(result)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


# ═══════════════════════════════════════════════════════════════════════════════
#  2. Natural Language Input Parser
# ═══════════════════════════════════════════════════════════════════════════════

def _build_parse_prompt(text: str) -> str:
    categories_str = ", ".join(CATEGORIES)
    today = datetime.now().strftime(DATE_FORMAT)
    return f"""Parse this expense description into structured data.

Input: "{text}"
Today's date: {today}

Respond with ONLY a valid JSON object (no markdown fencing):
{{
  "amount": <number>,
  "category": "<one of: {categories_str}>",
  "date": "<YYYY-MM-DD format>",
  "note": "<brief description>"
}}

Rules:
- Extract the monetary amount (just the number)
- Map the description to the closest category from the list
- Interpret relative dates: "today" = {today}, "yesterday" = {(datetime.now() - timedelta(days=1)).strftime(DATE_FORMAT)}, etc.
- If no date is mentioned, use today's date
- The note should be a clean, short description of what was purchased
- If category is unclear, use "Other"
"""


def _regex_parse_expense(text: str) -> dict:
    """Fallback regex-based parser for natural language expense input."""
    result = {
        "amount": 0,
        "category": "Other",
        "date": datetime.now().strftime(DATE_FORMAT),
        "note": text.strip(),
    }

    # Extract amount (first number found, possibly with decimals)
    amt_match = re.search(r"[\$₹€£¥]?\s*(\d+(?:[.,]\d{1,2})?)", text)
    if amt_match:
        result["amount"] = float(amt_match.group(1).replace(",", "."))

    # Extract date keywords
    lower = text.lower()
    if "yesterday" in lower:
        result["date"] = (datetime.now() - timedelta(days=1)).strftime(DATE_FORMAT)
    elif "day before" in lower:
        result["date"] = (datetime.now() - timedelta(days=2)).strftime(DATE_FORMAT)
    elif "last week" in lower:
        result["date"] = (datetime.now() - timedelta(days=7)).strftime(DATE_FORMAT)

    # Try to match a YYYY-MM-DD date in input
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if date_match:
        result["date"] = date_match.group(1)

    # Category keyword mapping
    category_keywords = {
        "Food": ["food", "pizza", "burger", "lunch", "dinner", "breakfast", "coffee",
                 "restaurant", "meal", "snack", "groceries", "eat", "ate", "biryani",
                 "chai", "tea", "milk", "bread", "rice", "chicken", "veg", "fruit",
                 "sweets", "cake", "ice cream", "juice", "water", "soda", "drink"],
        "Transport": ["uber", "ola", "cab", "taxi", "auto", "bus", "metro", "train",
                      "flight", "fuel", "petrol", "diesel", "gas", "parking", "toll",
                      "ride", "travel", "commute", "drive"],
        "Shopping": ["shopping", "amazon", "flipkart", "clothes", "shoes", "bag",
                     "watch", "phone", "laptop", "gadget", "electronics", "bought",
                     "purchase", "order", "online", "store", "mall"],
        "Bills": ["bill", "rent", "electricity", "water bill", "internet", "wifi",
                  "phone bill", "recharge", "subscription", "emi", "loan", "insurance",
                  "gas bill", "maintenance"],
        "Entertainment": ["movie", "netflix", "spotify", "game", "concert", "party",
                          "pub", "bar", "club", "outing", "fun", "ticket", "show",
                          "play", "stream", "youtube", "premium"],
        "Health": ["doctor", "medicine", "hospital", "pharmacy", "medical", "health",
                   "gym", "fitness", "yoga", "dental", "checkup", "test", "lab",
                   "clinic", "therapy", "vitamin"],
        "Education": ["book", "course", "class", "tuition", "tutorial", "udemy",
                      "coursera", "school", "college", "university", "exam", "study",
                      "stationery", "notebook", "pen"],
    }

    for cat, keywords in category_keywords.items():
        for kw in keywords:
            if kw in lower:
                result["category"] = cat
                break
        if result["category"] != "Other":
            break

    # Clean up note — remove the amount and date parts
    note = text
    if amt_match:
        note = note.replace(amt_match.group(0), "").strip()
    for word in ["yesterday", "today", "day before yesterday", "last week"]:
        note = re.sub(rf"\b{word}\b", "", note, flags=re.IGNORECASE).strip()
    # Remove currency symbols
    note = re.sub(r"[\$₹€£¥]", "", note).strip()
    # Clean extra spaces
    note = re.sub(r"\s+", " ", note).strip()
    if note:
        result["note"] = note

    return result


def parse_natural_input(
    text: str,
    on_result: Callable[[dict], None],
    on_error: Optional[Callable[[str], None]] = None,
):
    """
    Parse a free-text expense description asynchronously.
    Calls on_result(data) with: {"amount", "category", "date", "note", "source": "ai"|"rule"}
    """
    text = text.strip()
    if not text:
        on_result({
            "amount": 0, "category": "Other",
            "date": datetime.now().strftime(DATE_FORMAT),
            "note": "", "source": "rule",
        })
        return

    # No API key? Use regex directly
    if not has_api_key():
        result = _regex_parse_expense(text)
        result["source"] = "rule"
        on_result(result)
        return

    def _worker():
        prompt = _build_parse_prompt(text)
        raw = _call_gemini(prompt)
        if raw:
            try:
                cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
                data = json.loads(cleaned)
                # Validate required fields
                parsed = {
                    "amount": float(data.get("amount", 0)),
                    "category": data.get("category", "Other"),
                    "date": data.get("date", datetime.now().strftime(DATE_FORMAT)),
                    "note": data.get("note", text),
                    "source": "ai",
                }
                # Validate category
                if parsed["category"] not in CATEGORIES:
                    parsed["category"] = "Other"
                # Validate date format
                try:
                    datetime.strptime(parsed["date"], DATE_FORMAT)
                except ValueError:
                    parsed["date"] = datetime.now().strftime(DATE_FORMAT)
                on_result(parsed)
                return
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"[AI] Parse error: {e}")

        # Fallback
        result = _regex_parse_expense(text)
        result["source"] = "rule"
        if on_error:
            on_error("AI parsing unavailable — using keyword matching")
        on_result(result)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


# ═══════════════════════════════════════════════════════════════════════════════
#  3. Budget Advice
# ═══════════════════════════════════════════════════════════════════════════════

def _build_budget_prompt(spending: float, budget: float, categories: list) -> str:
    return f"""You are a concise personal finance advisor.

Monthly budget: {CURRENCY_SYMBOL}{budget:,.0f}
Spent so far: {CURRENCY_SYMBOL}{spending:,.0f} ({(spending/budget*100):.0f}% used)
Category breakdown: {json.dumps(categories)}

Give exactly ONE short paragraph (2-3 sentences max) of practical budget advice.
Be specific about which categories to watch. Use {CURRENCY_SYMBOL} for currency.
Keep the tone friendly and encouraging. Do NOT use markdown formatting.
Respond with plain text only — no JSON, no bullet points."""


def _rule_based_budget_advice(spending: float, budget: float, categories: list) -> str:
    """Fallback template-based budget advice."""
    pct = (spending / budget * 100) if budget > 0 else 0
    remaining = max(budget - spending, 0)

    if pct >= 100:
        top_cat = categories[0]["category"] if categories else "your expenses"
        return (
            f"You've exceeded your budget by {CURRENCY_SYMBOL}{spending - budget:,.0f}. "
            f"Your highest spending is in {top_cat}. "
            "Consider cutting discretionary spending for the rest of the month."
        )
    elif pct >= 80:
        return (
            f"You have {CURRENCY_SYMBOL}{remaining:,.0f} left in your budget. "
            "Focus on essentials-only spending to stay within your limit. "
            "Small savings now will add up by month end."
        )
    elif pct >= 50:
        top_cat = categories[0]["category"] if categories else "your top category"
        return (
            f"You're pacing well at {pct:.0f}% of budget. "
            f"Keep an eye on {top_cat} as it's your biggest area. "
            f"You still have {CURRENCY_SYMBOL}{remaining:,.0f} available."
        )
    else:
        return (
            f"Excellent! You've only used {pct:.0f}% of your budget. "
            f"You have {CURRENCY_SYMBOL}{remaining:,.0f} remaining. "
            "Keep maintaining these healthy spending habits."
        )


def get_budget_advice(
    db,
    on_result: Callable[[dict], None],
    on_error: Optional[Callable[[str], None]] = None,
    force_refresh: bool = False,
):
    """
    Fetch AI-powered budget advice asynchronously.
    Calls on_result(data) with: {"advice": str, "source": "ai"|"cache"|"rule"}
    """
    budget_str = db.get_setting("monthly_budget", "0")
    budget = float(budget_str) if budget_str else 0
    if budget <= 0:
        on_result({"advice": "", "source": "rule"})
        return

    spending = db.get_monthly_total()
    categories = db.get_category_breakdown()

    summary = {"spending": spending, "budget": budget, "categories": categories}
    cache_key = f"budget_{_hash_data(summary)}"

    if not force_refresh:
        cached = _cache.get(cache_key, AI_CACHE_TTL_BUDGET)
        if cached:
            cached["source"] = "cache"
            on_result(cached)
            return

    if not has_api_key():
        result = {
            "advice": _rule_based_budget_advice(spending, budget, categories),
            "source": "rule",
        }
        _cache.set(cache_key, result)
        on_result(result)
        return

    def _worker():
        prompt = _build_budget_prompt(spending, budget, categories)
        raw = _call_gemini(prompt)
        if raw and raw.strip():
            result = {"advice": raw.strip(), "source": "ai"}
            _cache.set(cache_key, result)
            on_result(result)
            return

        result = {
            "advice": _rule_based_budget_advice(spending, budget, categories),
            "source": "rule",
        }
        _cache.set(cache_key, result)
        if on_error:
            on_error("AI unavailable — showing rule-based advice")
        on_result(result)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Connection Test
# ═══════════════════════════════════════════════════════════════════════════════

def test_connection(
    on_result: Callable[[bool, str], None],
):
    """
    Test the API connection asynchronously.
    Calls on_result(success: bool, message: str).
    """
    if not has_api_key():
        on_result(False, "No API key configured")
        return

    def _worker():
        try:
            client = _get_client()
            if not client:
                on_result(False, "Failed to initialise client")
                return

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents="Reply with exactly: OK",
            )
            if response and response.text:
                on_result(True, "Connected to Gemini successfully!")
            else:
                on_result(False, "Empty response from API")
        except Exception as e:
            on_result(False, f"Connection failed: {str(e)}")

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


# ═══════════════════════════════════════════════════════════════════════════════
#  5. API Key Management
# ═══════════════════════════════════════════════════════════════════════════════

def save_api_key(key: str) -> bool:
    """Save the API key to the .env file. Returns True on success."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    try:
        lines = []
        key_found = False

        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        lines.append(f"GEMINI_API_KEY={key}\n")
                        key_found = True
                    else:
                        lines.append(line)

        if not key_found:
            lines.append(f"GEMINI_API_KEY={key}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # Update in-memory
        os.environ["GEMINI_API_KEY"] = key
        reload_client()
        return True
    except Exception as e:
        print(f"[AI] Failed to save API key: {e}")
        return False


def clear_api_key() -> bool:
    """Remove the API key from .env and memory."""
    return save_api_key("")


def clear_cache():
    """Clear all cached AI responses."""
    _cache.clear()
