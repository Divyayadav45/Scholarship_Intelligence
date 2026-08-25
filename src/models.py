"""
Data Models and Enums
Defines core data structures for scholarship records, verification statuses, and evidence items.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List

class SourceType(str, Enum):
    GOVERNMENT = "GOVERNMENT"
    UNIVERSITY = "UNIVERSITY"
    TRUSTED_AGGREGATOR = "TRUSTED_AGGREGATOR"
    CORPORATE = "CORPORATE"
    UNKNOWN = "UNKNOWN"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SUSPECT = "SUSPECT"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"

@dataclass
class FieldEvidence:
    field_name: str
    field_value: str
    evidence_text: str
    source_url: Optional[str] = None

@dataclass
class ScholarshipRecord:
    scholarship_name: str
    provider: Optional[str] = None
    source_url: Optional[str] = None
    source_type: SourceType = SourceType.UNKNOWN
    amount: Optional[str] = None
    eligibility: Optional[str] = None
    income_criteria: Optional[str] = None
    closing_date: Optional[str] = None
    application_url: Optional[str] = None
    evidence_list: List[FieldEvidence] = field(default_factory=list)