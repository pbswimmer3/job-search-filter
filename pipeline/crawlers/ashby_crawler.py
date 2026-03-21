import time
import requests
from pipeline.utils import logger, normalize_role, is_us_location
from pipeline.company_list import ASHBY_COMPANIES, ROLE_KEYWORDS, NEGATIVE_KEYWORDS

API_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


def _matches_keywords(title):
    title_lower = title.lower()
    if any(neg in title_lower for neg in NEGATIVE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in ROLE_KEYWORDS)


def run():
    logger.info(f"[ASHBY] Starting crawl for {len(ASHBY_COMPANIES)} companies")
    roles = []
    for company_name, slug in ASHBY_COMPANIES:
        try:
            resp = requests.get(API_URL.format(slug=slug), timeout=15)
            if resp.status_code == 404:
                logger.warning(f"[ASHBY] {company_name} ({slug}): 404, skipping")
                continue
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("jobs", [])
            for job in jobs:
                title = job.get("title", "")
                if not _matches_keywords(title):
                    continue
                location_name = job.get("location", "")
                if not is_us_location(location_name):
                    continue
                is_remote = job.get("isRemote") is True or job.get("workplaceType") == "Remote"
                description = job.get("descriptionPlain", "") or job.get("descriptionHtml", "")
                url = job.get("jobUrl", "")
                roles.append(normalize_role(
                    title=title,
                    company=company_name,
                    source="ashby",
                    url=url,
                    job_description=description,
                    location=location_name,
                    remote=is_remote,
                ))
            time.sleep(0.5)
        except requests.RequestException as e:
            logger.error(f"[ASHBY] {company_name} error: {e}")
            continue
    logger.info(f"[ASHBY] Found {len(roles)} matching roles")
    return roles


if __name__ == "__main__":
    from pipeline.utils import setup_logging
    setup_logging()
    results = run()
    for r in results:
        print(f"  {r['company']} — {r['title']} ({r['location']})")
    print(f"\nTotal: {len(results)}")
