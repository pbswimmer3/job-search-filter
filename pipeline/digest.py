import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from pipeline.utils import logger, get_db

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


def _get_pipeline_stats():
    conn = get_db()
    total_active = conn.execute(
        "SELECT COUNT(*) as c FROM qualified_roles WHERE status NOT IN ('rejected', 'archived')"
    ).fetchone()["c"]
    conn.close()
    return total_active


def send(scored_roles, errors=None):
    if not WEBHOOK_URL:
        logger.error("[DIGEST] DISCORD_WEBHOOK_URL not set, skipping digest")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    qualified = [r for r in scored_roles if r.get("score", 0) >= 50]
    unqualified = [r for r in scored_roles if r.get("score", 0) < 50]

    if not scored_roles:
        message = f"⚡ Job Search — {today}: No new roles found today."
    else:
        lines = [f"⚡ Job Search Pipeline — {today}\n"]
        lines.append(f"📋 New Qualified Roles ({len(qualified)})")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")

        if qualified:
            for r in sorted(qualified, key=lambda x: x.get("score", 0), reverse=True):
                loc = r.get("location", "N/A")
                lines.append(f"🏢 {r['company']} — {r['title']}")
                lines.append(f"📊 Score: {r.get('score', '?')}/100 | 📍 {loc} | 🔗 {r['source']}")
                if r.get("score_rationale"):
                    lines.append(f"💬 {r['score_rationale']}")
                if r.get("url"):
                    lines.append(r["url"])
                lines.append("")
        else:
            lines.append("No roles scored ≥50 today.\n")

        total_active = _get_pipeline_stats()
        lines.append(f"🗂 Unqualified: {len(unqualified)} roles archived (score < 50)")
        lines.append(f"📊 Pipeline: {total_active} active qualified roles (all-time)")
        lines.append("🖥 Dashboard: http://localhost:8082")

        if errors:
            lines.append("")
            for err in errors:
                lines.append(f"⚠️ {err}")

        message = "\n".join(lines)

    # Discord webhook max is 2000 chars — truncate if needed
    if len(message) > 1950:
        message = message[:1950] + "\n... (truncated)"

    try:
        resp = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
        resp.raise_for_status()
        logger.info("[DIGEST] Discord digest sent")
    except requests.RequestException as e:
        logger.error(f"[DIGEST] Discord send failed: {e}")
