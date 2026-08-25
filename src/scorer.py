"""
Confidence Scorer
"""

import logging
from typing import Dict, Any, List
from .models import VerificationStatus, SourceType

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    def __init__(self):
        self.source_weights = {
            SourceType.GOVERNMENT: 40,
            SourceType.UNIVERSITY: 35,
            SourceType.TRUSTED_AGGREGATOR: 25,
            SourceType.CORPORATE: 20,
            SourceType.UNKNOWN: 10,
        }

    def compute_score(self, record: Dict[str, Any], status: VerificationStatus, flags: List[str], warnings: List[str]) -> float:
        score = 0.0

        source_type = record.get("source_type", SourceType.UNKNOWN)
        if isinstance(source_type, str):
            try:
                source_type = SourceType(source_type)
            except ValueError:
                source_type = SourceType.UNKNOWN

        score += self.source_weights.get(source_type, 10)

        key_fields = ["scholarship_name", "provider", "amount", "eligibility", "closing_date", "application_url"]
        present_fields = sum(1 for f in key_fields if record.get(f))
        completeness_score = (present_fields / len(key_fields)) * 30
        score += completeness_score

        evidence_list = record.get("evidence_list", [])
        if evidence_list:
            evidence_count = len(evidence_list)
            score += min(20.0, evidence_count * 4.0)

        if status == VerificationStatus.VERIFIED:
            score += 10.0
        elif status == VerificationStatus.NEEDS_REVIEW:
            score += 0.0
        elif status == VerificationStatus.SUSPECT:
            score -= 25.0
        elif status == VerificationStatus.EXPIRED:
            score -= 40.0
        elif status == VerificationStatus.REJECTED:
            score = 0.0

        score -= len(warnings) * 3.0

        final_score = round(max(0.0, min(100.0, score)), 2)
        logger.info(f"Calculated Score: {final_score}/100 for record '{record.get('scholarship_name', 'Unknown')}'")
        return final_score