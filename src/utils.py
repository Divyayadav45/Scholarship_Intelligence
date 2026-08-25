import logging
import hashlib
import re
from typing import Optional
from datetime import datetime
from config.settings import BASE_DIR

def setup_logger(name: str = "scholarship_crawler") -> logging.Logger:
    """Configures structured Python logging."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Console Handler
        c_handler = logging.StreamHandler()
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)
        
        # File Handler
        log_file = BASE_DIR / "crawler.log"
        f_handler = logging.FileHandler(log_file)
        f_handler.setFormatter(c_format)
        logger.addHandler(f_handler)
        
    return logger

def generate_hash(text: str) -> str:
    """Computes SHA256 content hash for deduplication and change detection."""
    return hashlib.sha256(text.strip().encode('utf-8')).hexdigest()

def normalize_text(text: Optional[str]) -> str:
    """Removes extra whitespaces and standardizes text strings."""
    if not text:
        return "Not specified"
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned if cleaned else "Not specified"