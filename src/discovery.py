import re
from urllib.parse import urlparse
from typing import List, Dict, Any, Tuple
from src.models import SourceType
from src.utils import setup_logger, normalize_text

logger = setup_logger("discovery")

# Official Seed Sources for Indian Scholarships
SEED_SOURCES = [
    {
        "url": "https://scholarships.gov.in/",
        "label": "National Scholarship Portal (NSP)",
        "default_type": SourceType.GOVERNMENT
    },
    {
        "url": "https://www.tatacapital.com/scholarship/disclaimer.html",
        "label": "Tata Capital Scholarship Portal",
        "default_type": SourceType.CORPORATE
    },
    {
        "url": "https://www.sitaramjindalfoundation.org/scholarships.php",
        "label": "Sitaram Jindal Foundation",
        "default_type": SourceType.FOUNDATION
    },
    {
        "url": "https://www.iitb.ac.in/newen/scholarship",
        "label": "IIT Bombay Financial Aid",
        "default_type": SourceType.UNIVERSITY
    },
    {
        "url": "https://www.buddy4study.com/scholarships",
        "label": "Buddy4Study Aggregator Feed",
        "default_type": SourceType.AGGREGATOR
    }
]

# Domain Classification Rules
GOVT_DOMAINS = [".gov.in", ".nic.in", ".dharani.gov.in", "scholarships.gov.in", "aicte-india.org", "ugc.ac.in"]
UNI_DOMAINS = [".edu.in", ".ac.in", "iitb.ac.in", "iitd.ac.in", "du.ac.in"]
CORP_FOUNDATION_DOMAINS = ["tatacapital.com", "sitaramjindalfoundation.org", "reliancefoundation.org", "hdfcbank.com"]
AGGREGATOR_DOMAINS = ["buddy4study.com", "scholarshipsinindia.com", "nationalfinder.com"]

def classify_source(url: str) -> SourceType:
    """
    Deterministically classifies a URL source based on domain suffix and known registries.
    RULE 2 Compliance: AGGREGATOR sites can discover candidates but cannot mark them VERIFIED.
    """
    if not url:
        return SourceType.OTHER

    parsed = urlparse(url.lower())
    domain = parsed.netloc or parsed.path

    # Check Government
    if any(g in domain for g in GOVT_DOMAINS):
        return SourceType.GOVERNMENT

    # Check University / Academic
    if any(u in domain for u in UNI_DOMAINS):
        return SourceType.UNIVERSITY

    # Check Corporate / Foundation
    if any(c in domain for c in CORP_FOUNDATION_DOMAINS):
        if "foundation" in domain or "jindal" in domain:
            return SourceType.FOUNDATION
        return SourceType.CORPORATE

    # Check Known Aggregators
    if any(a in domain for a in AGGREGATOR_DOMAINS):
        return SourceType.AGGREGATOR

    return SourceType.OTHER

def discover_scholarships() -> List[Dict[str, Any]]:
    """
    Executes discovery across seed feeds and extracts candidate scholarship targets.
    Returns a list of discovery candidate payloads.
    """
    candidates = []
    logger.info("Executing Discovery Engine across seed sources...")

    for seed in SEED_SOURCES:
        url = seed["url"]
        classified_type = classify_source(url)
        
        candidates.append({
            "candidate_url": url,
            "title": seed["label"],
            "discovered_source_type": classified_type,
            "is_aggregator": classified_type == SourceType.AGGREGATOR,
            "seed_origin": url
        })

    logger.info(f"Discovery Engine identified {len(candidates)} candidate seeds.")
    return candidates