import pandas as pd
from pipeline.utils import logger, normalize_role, is_us_location

SEARCH_TERMS = [
    "founder's associate OR biz ops OR GTM strategy OR revenue operations OR strategy and operations OR deal desk",
    "deployment strategist OR strategic project lead OR bizops OR PMO OR program manager operations OR chief of staff",
]

def _df_to_roles(df, source_label="jobspy"):
    roles = []
    if df is None or df.empty:
        return roles
    for _, row in df.iterrows():
        location = str(row.get("location", ""))
        if not is_us_location(location):
            continue
        roles.append(normalize_role(
            title=row.get("title", ""),
            company=row.get("company_name", "") or row.get("company", ""),
            source=row.get("site", source_label),
            url=row.get("job_url", "") or row.get("link", ""),
            job_description=row.get("description", ""),
            location=row.get("location", ""),
            remote=bool(row.get("is_remote", False)),
        ))
    return roles

def _scrape_safe(**kwargs):
    try:
        from jobspy import scrape_jobs
        df = scrape_jobs(**kwargs)
        if isinstance(df, pd.DataFrame):
            return df
    except Exception as e:
        logger.error(f"[JOBSPY] Scrape error ({kwargs.get('site_name', '?')}): {e}")
    return pd.DataFrame()

def run():
    logger.info("[JOBSPY] Starting crawl")
    all_roles = []

    for term in SEARCH_TERMS:
        # Local/hybrid roles
        df = _scrape_safe(
            site_name=["linkedin", "indeed", "google"],
            search_term=term,
            location="San Francisco, CA",
            results_wanted=25,
            hours_old=24,
            is_remote=False,
            country_indeed="USA",
        )
        local_roles = _df_to_roles(df)
        logger.info(f"[JOBSPY] Local search: {len(local_roles)} roles")
        all_roles.extend(local_roles)

        # Remote roles
        df_remote = _scrape_safe(
            site_name=["linkedin", "indeed", "google"],
            search_term=term,
            location="USA",
            results_wanted=25,
            hours_old=24,
            is_remote=True,
            country_indeed="USA",
        )
        remote_roles = _df_to_roles(df_remote)
        logger.info(f"[JOBSPY] Remote search: {len(remote_roles)} roles")
        all_roles.extend(remote_roles)

    logger.info(f"[JOBSPY] Total: {len(all_roles)} roles")
    return all_roles

if __name__ == "__main__":
    from pipeline.utils import setup_logging
    setup_logging()
    results = run()
    for r in results:
        print(f"  [{r['source']}] {r['company']} — {r['title']}")
    print(f"\nTotal: {len(results)}")
