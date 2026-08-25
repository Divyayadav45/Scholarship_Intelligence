"""
Verification Engine
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

from .models import VerificationStatus, SourceType, ScholarshipRecord

logger = logging.getLogger(__name__)

TRUSTED_DOMAINS = [
    ".gov.in", ".nic.in", ".ac.in", ".edu.in", ".edu", ".gov", ".org.in"
]

class ScholarshipVerifier:
    def __init__(self):
        self.source_weights = {
            SourceType.GOVERNMENT: 0.95,
            SourceType.UNIVERSITY: 0.90,
            SourceType.TRUSTED_AGGREGATOR: 0.75,
            SourceType.CORPORATE: 0.70,
            SourceType.UNKNOWN: 0.40,
        }

    def verify_record(self, record: Dict[str, Any]) -> Tuple[VerificationStatus, List[str], List[str]]:
        flags = []
        warnings = []
        
        if not record.get("scholarship_name") or len(str(record.get("scholarship_name")).strip()) < 5:
            flags.append("MISSING_CRITICAL_NAME")
            
        if not record.get("provider"):
            warnings.append("MISSING_PROVIDER_NAME")

        app_url = record.get("application_url") or record.get("source_url") or ""
        if app_url:
            parsed = urlparse(app_url)
            domain = parsed.netloc.lower()
            
            is_trusted = any(domain.endswith(t_domain) for t_domain in TRUSTED_DOMAINS)
            if not is_trusted:
                warnings.append(f"UNVERIFIED_DOMAIN: {domain}")
                
            if any(term in app_url.lower() for term in ["login-free", "claim-now", "free-money", "telegram.me", "bit.ly"]):
                flags.append("SUSPICIOUS_APPLICATION_URL")
        else:
            warnings.append("NO_APPLICATION_URL")

        closing_date_str = record.get("closing_date")
        if closing_date_str:
            parsed_date = self._parse_date(closing_date_str)
            if parsed_date:
                today = datetime.now()
                if parsed_date < today:
                    flags.append("EXPIRED_SCHOLARSHIP")
            else:
                warnings.append("UNPARSEABLE_CLOSING_DATE")
        else:
            warnings.append("NO_CLOSING_DATE_SPECIFIED")

        full_text = str(record.get("raw_html_snippet", "")).lower()
        if any(scam_phrase in full_text for scam_phrase in ["application fee non-refundable", "pay registration fee to apply", "processing charge required"]):
            flags.append("POTENTIAL_FEE_SCAM")

        if "MISSING_CRITICAL_NAME" in flags or "SUSPICIOUS_APPLICATION_URL" in flags or "POTENTIAL_FEE_SCAM" in flags:
            status = VerificationStatus.REJECTED
        elif "EXPIRED_SCHOLARSHIP" in flags:
            status = VerificationStatus.EXPIRED
        elif flags:
            status = VerificationStatus.SUSPECT
        elif warnings:
            status = VerificationStatus.NEEDS_REVIEW
        else:
            status = VerificationStatus.VERIFIED

        logger.info(f"Verified '{record.get('scholarship_name', 'Unknown')}' -> Status: {status.value}, Flags: {len(flags)}, Warnings: {len(warnings)}")
        return status, flags, warnings

    def _parse_date(self, date_str: str) -> datetime | None:
        date_str = str(date_str).strip()
        formats = [
            "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y",
            "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None