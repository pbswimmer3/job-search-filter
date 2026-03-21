import time
import requests
from pipeline.utils import logger, normalize_role, is_us_location
from pipeline.company_list import GREENHOUSE_COMPANIES, ROLE_KEYWORDS, NEGATIVE_KEYWORDS

API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"

def _matches_keywords(title):
    title_lower = title.lower()
    if any(neg in title_lower for neg in NEGATIVE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in ROLE_KEYWORDS)

def run():
    logger.info(f"[GREENHOUSE] Starting crawl for {len(GREENHOUSE_COMPANIES)} companies")
    roles = []
    for company_name, token in GREENHOUSE_COMPANIES:
        try:
            resp = requests.get(API_URL.format(token=token), timeout=15)
            if resp.status_code == 404:
                logger.warning(f"[GREENHOUSE] {company_name} ({token}): 404, skipping")
                continue
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("jobs", [])
            for job in jobs:
                title = job.get("title", "")
                if not _matches_keywords(title):
                    continue
                location_name = ""
                if job.get("location", {}).get("name"):
                    location_name = job["location"]["name"]
                if not is_us_location(location_name):
                    continue
                description = ""
                if job.get("content"):
                    description = job["content"]
                url = job.get("absolute_url", "")
                roles.append(normalize_role(
                    title=title,
                    company=company_name,
                    source="greenhouse",
                    url=url,
                    job_description=description,
                    location=location_name,
                    remote="remote" in location_name.lower(),
                ))
            time.sleep(0.5)
        except requests.RequestException as e:
            logger.error(f"[GREENHOUSE] {company_name} error: {e}")
            continue
    logger.info(f"[GREENHOUSE] Found {len(roles)} matching roles")
    return roles

if __name__ == "__main__":
    from pipeline.utils import setup_logging
    setup_logging()
    results = run()
    for r in results:
        print(f"  {r['company']} — {r['title']} ({r['location']})")
    print(f"\nTotal: {len(results)}")
