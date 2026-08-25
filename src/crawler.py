import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

from config.settings import USER_AGENT, CRAWL_TIMEOUT, CRAWL_DELAY, MAX_RETRIES
from src.utils import setup_logger, generate_hash

logger = setup_logger("crawler")

class Crawler:
    """
    Polite HTTP Crawler with content hashing, domain rate-limiting, and local fixture fallback.
    """
    def __init__(self, delay: float = CRAWL_DELAY, timeout: int = CRAWL_TIMEOUT):
        self.delay = delay
        self.timeout = timeout
        self.last_request_time: Dict[str, float] = {}
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }

    def _enforce_politeness(self, domain: str):
        """Enforces a per-domain delay between consecutive HTTP requests."""
        now = time.time()
        last_time = self.last_request_time.get(domain, 0)
        elapsed = now - last_time
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time[domain] = time.time()

    def fetch(self, url: str, local_fixture_path: Optional[Path] = None) -> Tuple[Optional[str], Optional[str], int]:
        """
        Fetches page content from a live URL or reads from a local test fixture.
        
        Returns:
            Tuple[raw_html, content_hash, http_status_code]
        """
        # Option B: Local Test Fixture Path (Fallback/Development)
        if local_fixture_path and Path(local_fixture_path).exists():
            logger.info(f"[FIXTURE FALLBACK] Reading content from local fixture: {local_fixture_path}")
            try:
                with open(local_fixture_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content_hash = generate_hash(content)
                return content, content_hash, 200
            except Exception as e:
                logger.error(f"Failed to read local fixture {local_fixture_path}: {e}")
                return None, None, 500

        # Option A: Real HTTP Request Implementation
        domain = urlparse(url).netloc
        self._enforce_politeness(domain)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Crawling URL (Attempt {attempt}/{MAX_RETRIES}): {url}")
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    html_content = response.text
                    content_hash = generate_hash(html_content)
                    logger.info(f"Successfully fetched {url} (Hash: {content_hash[:10]}...)")
                    return html_content, content_hash, 200
                
                logger.warning(f"HTTP {response.status_code} received for {url}")
                if response.status_code in [403, 404, 500, 503]:
                    # Don't retry client/server errors unnecessarily
                    break

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout occurred while requesting {url}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while crawling {url}: {e}")

            time.sleep(self.delay * attempt)  # Exponential backoff delay

        logger.error(f"Failed to crawl {url} after {MAX_RETRIES} attempts.")
        return None, None, 404