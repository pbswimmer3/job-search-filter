# Greenhouse — only boards confirmed active as of 2026-03-20
# Format: (company_display_name, board_token)
GREENHOUSE_COMPANIES = [
    ("Airtable", "airtable"),
    ("Brex", "brex"),
    ("Lattice", "lattice"),
    ("Figma", "figma"),
    ("Amplitude", "amplitude"),
    ("Mixpanel", "mixpanel"),
    ("Merge", "merge"),
    ("Workato", "workato"),
    ("Alchemy", "alchemy"),
    ("Hightouch", "hightouch"),
]

# Ashby — replaces Lever (most startups migrated here)
# Format: (company_display_name, slug)
ASHBY_COMPANIES = [
    ("Clerk", "clerk"),
    ("Supabase", "supabase"),
    ("Replit", "replit"),
    ("Railway", "railway"),
    ("Modal", "modal"),
    ("Linear", "linear"),
    ("Vanta", "vanta"),
    ("Notion", "notion"),
    ("Drata", "drata"),
    ("Persona", "persona"),
    ("Deel", "deel"),
    ("Stytch", "stytch"),
    ("Vercel", "vercel"),
    ("Temporal", "temporal"),
    ("Retool", "retool"),
    ("Loom", "loom"),
    # Confirmed active on Ashby (may have 0 current postings)
    ("Anyscale", "anyscale"),
    ("Prefect", "prefect"),
    ("Airbyte", "airbyte"),
    ("WorkOS", "workos"),
]

# Keywords for filtering relevant roles from ATS boards
ROLE_KEYWORDS = [
    "founder", "biz ops", "bizops", "business ops", "business operations",
    "strategy", "operations", "gtm", "go-to-market", "go to market",
    "revenue operations", "revops", "rev ops", "deal desk", "deal operations",
    "growth", "chief of staff", "general manager",
    "customer solutions", "solutions engineer", "solutions architect",
    "partnerships", "business development",
    "associate",
    "deployment strategist", "strategic project lead",
    "pmo", "program manager",
]

# Titles containing these are filtered OUT even if they match a positive keyword
NEGATIVE_KEYWORDS = [
    "security", "devops", "dev ops", "sre ", "site reliability",
    "engineering manager", "software engineer", "data engineer",
    "machine learning", "ml engineer", "backend engineer", "frontend engineer",
    "recruiter", "recruiting", "talent acquisition",
    "designer", "design manager", "product design",
    "researcher", "research scientist",
    "it operations", "it support", "system admin", "infrastructure",
    "legal", "counsel", "attorney", "paralegal",
    "accountant", "accounting", "payroll", "accounts payable",
    "executive assistant", "office manager",
    "intern", "internship",
    "vice president", " vp ", "director of engineering",
    "head of engineering", "cto", "cfo", "coo",
]
