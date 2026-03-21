import sqlite3
import logging
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jobs.db")
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline.log")
LAST_RUN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".last_run")

logger = logging.getLogger("job_pipeline")

def setup_logging():
    handler = logging.FileHandler(LOG_PATH)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    # Also log to stdout for interactive runs
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(console)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def dedup_roles(roles, existing_urls):
    """Filter out roles whose URL is already in the DB."""
    seen = set()
    result = []
    for role in roles:
        url = role.get("url", "")
        if url and url not in existing_urls and url not in seen:
            seen.add(url)
            result.append(role)
    return result

def _clean(val):
    """Coerce to str and strip. Handles NaN/None/float from pandas."""
    if val is None or (isinstance(val, float) and val != val):  # NaN check
        return ""
    return str(val).strip()


def normalize_role(title, company, source, url, date_found=None, job_description="",
                   location="", remote=False):
    return {
        "title": _clean(title),
        "company": _clean(company),
        "source": _clean(source),
        "url": _clean(url),
        "date_found": _clean(date_found) or datetime.now().strftime("%Y-%m-%d"),
        "job_description": _clean(job_description),
        "location": _clean(location),
        "remote": 1 if remote else 0,
    }

# Non-US locations to reject. If location contains any of these, skip it.
# "Remote" with no country qualifier is allowed (assumed US-eligible).
NON_US_INDICATORS = [
    "canada", "uk", "united kingdom", "london", "england", "ireland", "dublin",
    "germany", "berlin", "munich", "france", "paris", "netherlands", "amsterdam",
    "spain", "madrid", "barcelona", "italy", "sweden", "stockholm",
    "singapore", "tokyo", "japan", "india", "bengaluru", "bangalore", "mumbai",
    "hyderabad", "delhi", "pune", "chennai", "gurgaon",
    "brazil", "são paulo", "sao paulo", "mexico city",
    "australia", "sydney", "melbourne", "tel aviv", "israel",
    "south korea", "seoul", "china", "beijing", "shanghai",
    "vancouver", "toronto", "montreal", "ottawa",
    "emea", "apac", "latam",
]


def is_us_location(location):
    """Return True if location appears to be US-based or unspecified (remote)."""
    if not location:
        return True  # No location = don't filter out
    loc_lower = location.lower()
    # Explicit US signals — always keep
    if any(us in loc_lower for us in ["united states", "usa", ", us", "(us)"]):
        return True
    # Check for non-US indicators
    if any(non_us in loc_lower for non_us in NON_US_INDICATORS):
        return False
    # Default: keep (covers US cities, "Remote", ambiguous strings)
    return True


def write_last_run():
    with open(LAST_RUN_PATH, "w") as f:
        f.write(datetime.now().isoformat())
