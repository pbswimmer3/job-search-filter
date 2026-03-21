import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from pipeline.utils import logger

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

KIMI_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
KIMI_BASE_URL = "https://api.moonshot.ai/v1"
KIMI_MODEL = "kimi-k2.5"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(PROJECT_ROOT, "PRAD_PROFILE.md")

PROMPT_TEMPLATE = """You are a job qualification agent. Score the following job posting against the candidate profile below on a scale of 0-100. Return ONLY valid JSON, no explanation outside the JSON.

CANDIDATE PROFILE:
{profile}

SCORING RUBRIC:
- Role scope & ownership (30%): Does the role offer end-to-end ownership? Penalize pure support/execution roles with no strategic component.
- Stage fit (20%): Seed-Series C preferred. Heavy penalty for large enterprises.
- Functional match (25%): Overlap with target role types, deal desk, GenAI tooling, customer-facing ops, cross-functional execution.
- Technical/AI signal (15%): Opportunity to apply AI/automation skills? Bonus for tooling, process building, or data work.
- Seniority fit (10%): IC role with some ownership. Penalize entry-level coordinators and VP+ roles. Ideal: 1-4 years experience required.

JOB POSTING:
Title: {title}
Company: {company}
Location: {location}
Description: {description}

Return this exact JSON:
{{"score": <integer 0-100>, "rationale": "<2-3 sentences explaining the score, citing specific JD language and profile match/gaps>"}}"""


def _load_profile():
    try:
        with open(PROFILE_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"[QUALIFY] Profile not found at {PROFILE_PATH}")
        return ""


# Load once at import time; reloaded per pipeline run via score_all
_profile_cache = None


def _get_profile():
    global _profile_cache
    if _profile_cache is None:
        _profile_cache = _load_profile()
    return _profile_cache


def _call_kimi(prompt):
    if not KIMI_API_KEY:
        logger.error("[QUALIFY] MOONSHOT_API_KEY not set")
        return None
    client = OpenAI(api_key=KIMI_API_KEY, base_url=KIMI_BASE_URL)
    try:
        response = client.chat.completions.create(
            model=KIMI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=1,  # K2.5 thinking model only allows temperature=1
            max_tokens=4000,  # K2.5 needs headroom for reasoning tokens
        )
        content = response.choices[0].message.content or ""
        content = content.strip()
        # Handle markdown-wrapped JSON
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"[QUALIFY] JSON parse error: {e} — raw: {content[:200]}")
        return None
    except Exception as e:
        logger.error(f"[QUALIFY] Kimi API error: {e}")
        return None


def score_role(role):
    description = role.get("job_description", "")
    # Truncate very long descriptions to fit context window
    if len(description) > 6000:
        description = description[:6000] + "..."

    prompt = PROMPT_TEMPLATE.format(
        profile=_get_profile(),
        title=role["title"],
        company=role["company"],
        location=role["location"],
        description=description,
    )
    result = _call_kimi(prompt)
    if result and isinstance(result.get("score"), (int, float)):
        role["score"] = int(result["score"])
        role["score_rationale"] = result.get("rationale", "")
    else:
        # Default to low score on API failure so it doesn't block pipeline
        role["score"] = 0
        role["score_rationale"] = "Scoring failed — API error or invalid response"
        logger.warning(f"[QUALIFY] Failed to score: {role['company']} — {role['title']}")
    return role


def score_all(roles):
    # Reload profile fresh each pipeline run
    global _profile_cache
    _profile_cache = _load_profile()
    if not _profile_cache:
        logger.error("[QUALIFY] Empty profile — scores will be unreliable")

    logger.info(f"[QUALIFY] Scoring {len(roles)} roles via Kimi K2.5")
    scored = []
    for i, role in enumerate(roles):
        scored.append(score_role(role))
        if (i + 1) % 10 == 0:
            logger.info(f"[QUALIFY] Scored {i + 1}/{len(roles)}")
    qualified = sum(1 for r in scored if r.get("score", 0) >= 50)
    logger.info(f"[QUALIFY] Done: {qualified} qualified, {len(scored) - qualified} unqualified")
    return scored
