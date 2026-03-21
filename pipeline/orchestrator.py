#!/usr/bin/env python3
"""Job search pipeline orchestrator. Run daily via cron."""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.utils import setup_logging, logger, write_last_run
from pipeline import tracker
from pipeline.crawlers import jobspy_crawler, greenhouse_crawler, ashby_crawler
from pipeline.qualify import score_all
from pipeline.digest import send


def run():
    setup_logging()
    logger.info("=" * 50)
    logger.info("Pipeline start")

    # Initialize DB if needed
    tracker.init_db()

    # Stage 1: Crawl all sources
    raw_roles = []
    errors = []

    crawlers = [
        ("JobSpy", jobspy_crawler.run),
        ("Greenhouse", greenhouse_crawler.run),
        ("Ashby", ashby_crawler.run),
    ]

    for name, crawl_fn in crawlers:
        try:
            results = crawl_fn()
            raw_roles.extend(results)
            logger.info(f"[CRAWL] {name}: {len(results)} roles")
        except Exception as e:
            logger.error(f"[CRAWL] {name} failed: {e}")
            errors.append(f"{name} crawler failed: {e}")

    logger.info(f"[CRAWL] Total raw: {len(raw_roles)} roles from {len(crawlers)} sources")

    # Stage 2: Dedup against DB
    new_roles = tracker.filter_new(raw_roles)

    if not new_roles:
        logger.info("No new roles found — sending empty digest")
        send([], errors=errors if errors else None)
        write_last_run()
        logger.info("Pipeline complete")
        return

    # Stage 3: Qualify
    scored_roles = score_all(new_roles)

    # Stage 4: Write to DB
    tracker.write(scored_roles)

    # Stage 5: Discord digest
    send(scored_roles, errors=errors if errors else None)

    # Done
    write_last_run()
    logger.info("Pipeline complete")


if __name__ == "__main__":
    run()
