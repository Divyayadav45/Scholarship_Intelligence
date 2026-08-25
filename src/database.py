"""
Database Engine
Handles SQLite storage, indexing, and deduplication for scholarship records and evidence.
"""

import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("scholarships.db")

class DatabaseEngine:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main scholarships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scholarships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scholarship_name TEXT NOT NULL,
                    provider TEXT,
                    source_url TEXT UNIQUE,
                    source_type TEXT,
                    amount TEXT,
                    eligibility TEXT,
                    income_criteria TEXT,
                    closing_date TEXT,
                    application_url TEXT,
                    verification_status TEXT,
                    confidence_score REAL,
                    flags TEXT,
                    warnings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Field evidence table (Traceability)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scholarship_id INTEGER,
                    field_name TEXT,
                    field_value TEXT,
                    evidence_text TEXT,
                    FOREIGN KEY (scholarship_id) REFERENCES scholarships (id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully.")

    def save_scholarship(self, record: Dict[str, Any], status: str, score: float, flags: List[str], warnings: List[str]) -> int:
        """Inserts or updates a scholarship record and its evidence list."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scholarships (
                    scholarship_name, provider, source_url, source_type, amount,
                    eligibility, income_criteria, closing_date, application_url,
                    verification_status, confidence_score, flags, warnings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_url) DO UPDATE SET
                    scholarship_name=excluded.scholarship_name,
                    provider=excluded.provider,
                    amount=excluded.amount,
                    eligibility=excluded.eligibility,
                    income_criteria=excluded.income_criteria,
                    closing_date=excluded.closing_date,
                    application_url=excluded.application_url,
                    verification_status=excluded.verification_status,
                    confidence_score=excluded.confidence_score,
                    flags=excluded.flags,
                    warnings=excluded.warnings
            """, (
                record.get("scholarship_name"),
                record.get("provider"),
                record.get("source_url"),
                str(record.get("source_type")),
                record.get("amount"),
                record.get("eligibility"),
                record.get("income_criteria"),
                record.get("closing_date"),
                record.get("application_url"),
                status,
                score,
                json.dumps(flags),
                json.dumps(warnings)
            ))
            
            scholarship_id = cursor.lastrowid
            
            # If updated via ON CONFLICT, retrieve existing ID
            if not scholarship_id:
                cursor.execute("SELECT id FROM scholarships WHERE source_url = ?", (record.get("source_url"),))
                row = cursor.fetchone()
                if row:
                    scholarship_id = row["id"]

            # Save field evidence entries
            evidence_list = record.get("evidence_list", [])
            if scholarship_id and evidence_list:
                # Clear existing evidence to prevent duplicated entries on update
                cursor.execute("DELETE FROM field_evidence WHERE scholarship_id = ?", (scholarship_id,))
                
                for ev in evidence_list:
                    field_name = getattr(ev, "field_name", ev.get("field_name") if isinstance(ev, dict) else "")
                    field_value = getattr(ev, "field_value", ev.get("field_value") if isinstance(ev, dict) else "")
                    evidence_text = getattr(ev, "evidence_text", ev.get("evidence_text") if isinstance(ev, dict) else "")
                    
                    cursor.execute("""
                        INSERT INTO field_evidence (scholarship_id, field_name, field_value, evidence_text)
                        VALUES (?, ?, ?, ?)
                    """, (scholarship_id, field_name, field_value, evidence_text))
            
            conn.commit()
            logger.info(f"Saved scholarship record ID {scholarship_id} to database.")
            return scholarship_id

    def get_all_scholarships(self) -> List[Dict[str, Any]]:
        """Retrieves all stored records ordered by confidence score."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scholarships ORDER BY confidence_score DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]