import sqlite3
from pipeline.utils import get_db, logger, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS qualified_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    source TEXT,
    url TEXT UNIQUE NOT NULL,
    date_found TEXT,
    job_description TEXT,
    location TEXT,
    remote INTEGER DEFAULT 0,
    score INTEGER,
    score_rationale TEXT,
    status TEXT DEFAULT 'new',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS unqualified_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    source TEXT,
    url TEXT UNIQUE NOT NULL,
    date_found TEXT,
    job_description TEXT,
    location TEXT,
    remote INTEGER DEFAULT 0,
    score INTEGER,
    score_rationale TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def get_existing_urls():
    conn = get_db()
    urls = set()
    for table in ("qualified_roles", "unqualified_roles"):
        rows = conn.execute(f"SELECT url FROM {table}").fetchall()
        urls.update(row["url"] for row in rows)
    conn.close()
    return urls

def filter_new(roles):
    existing = get_existing_urls()
    new = [r for r in roles if r.get("url") and r["url"] not in existing]
    logger.info(f"{len(new)} new roles after dedup (from {len(roles)} total)")
    return new

def write(scored_roles):
    conn = get_db()
    qualified = 0
    unqualified = 0
    for role in scored_roles:
        score = role.get("score", 0)
        table = "qualified_roles" if score >= 50 else "unqualified_roles"
        try:
            if table == "qualified_roles":
                conn.execute(
                    """INSERT OR IGNORE INTO qualified_roles
                       (title, company, source, url, date_found, job_description,
                        location, remote, score, score_rationale)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (role["title"], role["company"], role["source"], role["url"],
                     role["date_found"], role["job_description"], role["location"],
                     role["remote"], score, role.get("score_rationale", "")),
                )
                qualified += 1
            else:
                conn.execute(
                    """INSERT OR IGNORE INTO unqualified_roles
                       (title, company, source, url, date_found, job_description,
                        location, remote, score, score_rationale)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (role["title"], role["company"], role["source"], role["url"],
                     role["date_found"], role["job_description"], role["location"],
                     role["remote"], score, role.get("score_rationale", "")),
                )
                unqualified += 1
        except sqlite3.Error as e:
            logger.error(f"DB write error for {role.get('url', 'unknown')}: {e}")
    conn.commit()
    conn.close()
    logger.info(f"Wrote {qualified} qualified, {unqualified} unqualified roles to DB")

if __name__ == "__main__":
    from pipeline.utils import setup_logging
    setup_logging()
    init_db()
    print(f"Database initialized at {DB_PATH}")
