import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "scholarships.db"
DATA_DIR = BASE_DIR / "data"
FIXTURES_DIR = BASE_DIR / "tests" / "fixtures"

# Ensure essential directories exist
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

# Crawler Settings
USER_AGENT = "ScholarshipIntelligenceBot/1.0 (+https://scholarships.gov.in/)"
CRAWL_TIMEOUT = 10  # Seconds
CRAWL_DELAY = 1.0   # Politeness delay between requests
MAX_RETRIES = 3

# Official Domain Whitelist for Verification Scoring (+30 points)
OFFICIAL_DOMAINS = [
    ".gov.in",
    ".edu.in",
    ".ac.in",
    "scholarships.gov.in",
    "tatacapital.com",
    "sitaramjindalfoundation.org",
    "iitb.ac.in",
    "iitd.ac.in"
]

# Scoring Constants
CONFIDENCE_THRESHOLD_VERIFIED = 95