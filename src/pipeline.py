"""
Pipeline Orchestrator
Coordinates crawling, extraction, verification, scoring, and storage.
"""

import logging
from typing import Dict, Any

from .crawler import Crawler
from .extractor import Extractor
from .verifier import ScholarshipVerifier
from .scorer import ConfidenceScorer
from .database import DatabaseEngine
from .models import SourceType

logger = logging.getLogger(__name__)

class ScholarshipPipeline:
    def __init__(self):
        self.crawler = Crawler()
        self.extractor = Extractor()
        self.verifier = ScholarshipVerifier()
        self.scorer = ConfidenceScorer()
        self.db = DatabaseEngine()

    def process_url(self, url: str, default_provider: str = "Unknown", source_type: SourceType = SourceType.UNKNOWN) -> Dict[str, Any]:
        logger.info(f"Starting pipeline processing for URL: {url}")
        
        # 1. Fetch web page content
        raw_crawl_result = self.crawler.fetch(url)
        
        # Unpack tuple if crawler returns (content, status_code)
        if isinstance(raw_crawl_result, tuple):
            html_content = raw_crawl_result[0]
        else:
            html_content = raw_crawl_result

        # Guard clause: stop pipeline cleanly if fetch failed or returned invalid markup
        if not html_content or not isinstance(html_content, (str, bytes)):
            logger.error(f"Failed to fetch valid HTML content from {url}")
            return {"error": f"Failed to fetch valid content from {url}"}

        # 2. Extract structured fields
        extracted_record = self.extractor.extract_from_html(
            html_content, 
            source_url=url, 
            default_provider=default_provider, 
            source_type=source_type
        )

        # 3. Verify record integrity
        status, flags, warnings = self.verifier.verify_record(extracted_record)

        # 4. Calculate confidence score
        confidence_score = self.scorer.compute_score(extracted_record, status, flags, warnings)

        # 5. Persist record & evidence into SQLite database
        db_id = self.db.save_scholarship(
            record=extracted_record,
            status=status.value,
            score=confidence_score,
            flags=flags,
            warnings=warnings
        )

        return {
            "id": db_id,
            "scholarship_name": extracted_record.get("scholarship_name"),
            "provider": extracted_record.get("provider"),
            "status": status.value,
            "confidence_score": confidence_score,
            "flags": flags,
            "warnings": warnings,
            "record": extracted_record
        }