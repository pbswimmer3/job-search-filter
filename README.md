# Job Search Pipeline

Automated daily job search pipeline that crawls multiple sources, scores roles against a candidate profile using Kimi K2.5, and serves a tracking dashboard.

## Setup

```bash
cd ~/job_search
source .venv/bin/activate
cp .env.example .env       # Add your API keys
```

Required env vars in `.env`:
- `DISCORD_WEBHOOK_URL` — Discord webhook for daily digest
- `MOONSHOT_API_KEY` — Moonshot API key for qualification scoring

## Run Pipeline

```bash
cd ~/job_search
source .venv/bin/activate
python pipeline/orchestrator.py
```

Runs automatically at 07:00 daily via HEARTBEAT cron.

## Dashboard

```bash
cd ~/job_search/dashboard
node server.js &
```

Accessible at http://localhost:8082. Runs as a persistent background service.

## Sources

| Source | Method | Active Boards |
|--------|--------|---------------|
| LinkedIn, Indeed, Google | JobSpy library | N/A |
| Greenhouse | Public Board API | 10 companies |
| Ashby | Public Posting API | 20 companies |

## Maintenance

- Refresh `pipeline/company_list.py` every few weeks as companies change ATS
- Test board tokens: `python -m pipeline.crawlers.greenhouse_crawler` or `ashby_crawler`
- 404s are handled silently — stale tokens don't break the pipeline

## Architecture

```
orchestrator.py → crawlers → qualify.py (Kimi K2.5) → tracker.py (SQLite) → digest.py (Discord)
                                                         ↕
                                                    dashboard/ (Express, port 8082)
```

## How to Change What Roles Are Searched

Role filtering happens in two places:

**1. ATS board crawlers (Greenhouse, Ashby)** — Edit `pipeline/company_list.py`. The `ROLE_KEYWORDS` list near the bottom of the file controls which job titles are kept. Any job whose title contains one of these keywords (case-insensitive) passes the filter. For example, adding `"product ops"` would match "Senior Product Ops Manager". The `NEGATIVE_KEYWORDS` list below it filters *out* titles that match — so "Security Operations" gets removed even though it contains "operations". Add or remove entries from either list as needed.

**2. JobSpy crawler (LinkedIn, Indeed, Google)** — Edit `pipeline/crawlers/jobspy_crawler.py`. The `SEARCH_TERMS` list at the top contains the actual search queries sent to job boards. These use `OR` syntax — e.g. `"biz ops OR GTM strategy OR deal desk"`. Add new terms to an existing query string, or add a new string to the list to run a separate search pass. Each entry runs two searches (one local SF, one remote US), so adding entries increases crawl time slightly.

Both files are plain Python — just edit the strings and save. No restart needed; changes take effect on the next pipeline run.

## How to Update the Candidate Profile (Scoring Criteria)

The scoring agent reads `PRAD_PROFILE.md` in the project root (`~/job_search/PRAD_PROFILE.md`) every time the pipeline runs. This file contains the full candidate background, target roles, experience details, and scoring signals that Kimi K2.5 uses to score each job posting from 0–100.

**When to update it:**
- You gain new experience or complete a project worth highlighting
- Your target role types or company stage preferences change
- You want to adjust what counts as a "strong positive" or "hard penalty" in scoring
- You notice the scorer is consistently over- or under-valuing certain types of roles

**How to edit it:**
Open `~/job_search/PRAD_PROFILE.md` in any text editor. It's standard Markdown. The most impactful sections to change are:

- **Identity & Target** — Controls what role types and company stages the scorer looks for. If you start targeting Product Management roles, add them here.
- **Key Scoring Signals** — The "strong positive signals" and "hard penalties" at the bottom directly influence how the scorer weights JD language. If you want it to stop penalizing large companies, remove that penalty.
- **Professional Experience** — More detail here means more accurate functional matching. If you complete a new project, add it so the scorer can recognize relevant JD overlap.

Changes take effect on the next pipeline run — no code changes or restarts needed.

**How to set up remote access to dashboard:**

```bash
sudo tailscale funnel --bg 8082
```
Once it runs, your dashboard will be live at:
https://openclaw-vm.tail07c89.ts.net

The exact domain is based on your tailnet name — the command output will confirm the full URL.

Also make sure the dashboard server is running first:

```bash
cd ~/job_search/dashboard && node server.js &
```
