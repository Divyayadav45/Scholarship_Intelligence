import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.models import SourceType, FieldEvidence
from src.utils import setup_logger, normalize_text, generate_hash

logger = setup_logger("extractor")

class Extractor:
    """
    Deterministic Extraction Engine that converts raw HTML into normalized data fields
    and verbatim traceable evidence snippets.
    """

    # Regex heuristics for critical scholarship fields
    DATE_PATTERNS = [
        r"(?:closing|last|deadline|end)\s*date\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"(?:closing|last|deadline|end)\s*date\s*[:\-]?\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})",
        r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
    ]

    AMOUNT_PATTERNS = [
        r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\s*(?:per|/)\s*(?:annum|year|month))?",
        r"Rs\.?\s*[\d,]+",
        r"[\d,]+\s*(?:per|/)\s*(?:annum|year)"
    ]

    INCOME_PATTERNS = [
        r"(?:family|annual)\s*income\s*(?:less than|below|up to|not exceeding)?\s*(?:₹|Rs\.?|INR)?\s*[\d,]+(?:\s*lakh|lakhs)?",
        r"less than\s*(?:₹|Rs\.?|INR)?\s*[\d,]+(?:\s*lakh|lakhs)?"
    ]

    def extract_from_html(
        self,
        html_content: str,
        source_url: str,
        default_provider: str = "Official Source",
        source_type: SourceType = SourceType.GOVERNMENT
    ) -> Dict[str, Any]:
        """
        Parses raw HTML and returns extracted fields along with traceable field evidence.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Clean script and style tags for readable text analysis
        for element in soup(["script", "style", "nav", "footer"]):
            element.extract()
            
        page_text = soup.get_text(separator=" ")
        normalized_page_text = normalize_text(page_text)

        evidence_list: List[FieldEvidence] = []

        # 1. Extract Title / Scholarship Name
        scholarship_name = self._extract_title(soup)
        
        # 2. Extract Deadline / Closing Date
        closing_date, date_ev = self._extract_closing_date(normalized_page_text, source_url)
        if date_ev:
            evidence_list.append(date_ev)

        # 3. Extract Amount
        amount, amount_ev = self._extract_amount(normalized_page_text, source_url)
        if amount_ev:
            evidence_list.append(amount_ev)

        # 4. Extract Eligibility Criteria
        eligibility, elig_ev = self._extract_eligibility(soup, normalized_page_text, source_url)
        if elig_ev:
            evidence_list.append(elig_ev)

        # 5. Extract Income Criteria
        income_criteria, inc_ev = self._extract_income(normalized_page_text, source_url)
        if inc_ev:
            evidence_list.append(inc_ev)

        # 6. Extract Application Link
        application_url, app_ev = self._extract_application_url(soup, source_url)
        if app_ev:
            evidence_list.append(app_ev)

        # Generate unique record ID based on scholarship name & provider
        record_id = generate_hash(f"{scholarship_name}_{default_provider}")

        extracted_payload = {
            "id": record_id,
            "scholarship_name": scholarship_name,
            "provider": default_provider,
            "official_source_url": source_url,
            "application_url": application_url,
            "source_type": source_type,
            "amount": amount,
            "eligibility": eligibility,
            "academic_requirements": "Not specified",
            "income_criteria": income_criteria,
            "closing_date": closing_date,
            "evidence_list": evidence_list
        }

        logger.info(f"Extracted record '{scholarship_name}' with {len(evidence_list)} evidence quotes.")
        return extracted_payload

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extracts the main heading or title element."""
        h1 = soup.find("h1")
        if h1 and len(h1.get_text(strip=True)) > 5:
            return normalize_text(h1.get_text())
        title = soup.find("title")
        if title and len(title.get_text(strip=True)) > 5:
            return normalize_text(title.get_text().split("-")[0].split("|")[0])
        return "National Scholarship Scheme"

    def _extract_closing_date(self, text: str, source_url: str) -> Tuple[str, Optional[FieldEvidence]]:
        """Matches closing dates and returns verbatim evidence snippet."""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_val = match.group(1) if match.groups() else match.group(0)
                # Capture surrounding context snippet (up to 100 chars)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 40)
                snippet = text[start:end].strip()

                evidence = FieldEvidence(
                    field_name="closing_date",
                    field_value=date_val,
                    evidence_text=snippet,
                    source_url=source_url
                )
                return date_val, evidence

        return "Not specified", None

    def _extract_amount(self, text: str, source_url: str) -> Tuple[str, Optional[FieldEvidence]]:
        """Matches scholarship amounts and returns verbatim evidence snippet."""
        for pattern in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amt_val = match.group(0)
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 30)
                snippet = text[start:end].strip()

                evidence = FieldEvidence(
                    field_name="amount",
                    field_value=amt_val,
                    evidence_text=snippet,
                    source_url=source_url
                )
                return amt_val, evidence

        return "Not specified", None

    def _extract_eligibility(
        self, soup: BeautifulSoup, text: str, source_url: str
    ) -> Tuple[str, Optional[FieldEvidence]]:
        """Scrapes eligibility section or paragraphs containing relevant keywords."""
        keywords = ["eligibility", "eligible", "qualification", "criteria"]
        for kw in keywords:
            # Look for headers containing eligibility keyword
            header = soup.find(lambda tag: tag.name in ["h2", "h3", "h4", "strong", "b"] and kw in tag.get_text().lower())
            if header:
                parent = header.parent
                if parent:
                    snippet = normalize_text(parent.get_text())[:250]
                    evidence = FieldEvidence(
                        field_name="eligibility",
                        field_value=snippet[:100] + "...",
                        evidence_text=snippet,
                        source_url=source_url
                    )
                    return snippet, evidence

        # Text Regex Fallback
        match = re.search(r"(?:eligibility|eligible\s+if)\s*[:\-]?\s*([^.]{20,150}\.)", text, re.IGNORECASE)
        if match:
            snippet = match.group(0).strip()
            evidence = FieldEvidence(
                field_name="eligibility",
                field_value=match.group(1).strip(),
                evidence_text=snippet,
                source_url=source_url
            )
            return match.group(1).strip(), evidence

        return "Not specified", None

    def _extract_income(self, text: str, source_url: str) -> Tuple[str, Optional[FieldEvidence]]:
        """Matches income criteria limits."""
        for pattern in self.INCOME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                inc_val = match.group(0)
                start = max(0, match.start() - 15)
                end = min(len(text), match.end() + 25)
                snippet = text[start:end].strip()

                evidence = FieldEvidence(
                    field_name="income_criteria",
                    field_value=inc_val,
                    evidence_text=snippet,
                    source_url=source_url
                )
                return inc_val, evidence

        return "Not specified", None

    def _extract_application_url(
        self, soup: BeautifulSoup, source_url: str
    ) -> Tuple[str, Optional[FieldEvidence]]:
        """Finds direct application links within the DOM."""
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text().lower()
            if any(k in text for k in ["apply online", "apply now", "application portal", "register"]):
                app_url = a_tag["href"]
                if not app_url.startswith("http"):
                    # Resolve relative links
                    from urllib.parse import urljoin
                    app_url = urljoin(source_url, app_url)
                
                evidence = FieldEvidence(
                    field_name="application_url",
                    field_value=app_url,
                    evidence_text=f"Link text: '{a_tag.get_text().strip()}' pointing to {app_url}",
                    source_url=source_url
                )
                return app_url, evidence

        return source_url, None