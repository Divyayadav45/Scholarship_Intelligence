import sys
from pathlib import Path

# Force the directory containing main.py into sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import logging
from src.pipeline import ScholarshipPipeline
from src.models import SourceType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def main():
    print("\n==================================================")
    print("   Scholarship Intelligence Platform Engine")
    print("==================================================\n")

    pipeline = ScholarshipPipeline()

    # Valid working targets
    targets = [
        {
            "url": "https://scholarships.gov.in/",
            "provider": "Government of India",
            "source_type": SourceType.GOVERNMENT
        },
        {
            "url": "https://www.aicte-india.org/schemes/students-development-schemes",
            "provider": "AICTE",
            "source_type": SourceType.GOVERNMENT
        }
    ]

    for target in targets:
        print(f"[*] Processing Target URL: {target['url']}")
        result = pipeline.process_url(
            url=target["url"],
            default_provider=target["provider"],
            source_type=target["source_type"]
        )
        
        if "error" in result:
            print(f"❌ Execution Error: {result['error']}\n")
            continue

        print("\n--- Pipeline Execution Result ---")
        print(f" Database ID    : {result.get('id')}")
        print(f" Scholarship    : {result.get('scholarship_name')}")
        print(f" Provider       : {result.get('provider')}")
        print(f" Status         : {result.get('status')}")
        print(f" Confidence     : {result.get('confidence_score')} / 100.0")
        print(f" Anomaly Flags  : {result.get('flags')}")
        print(f" Warnings       : {result.get('warnings')}")
        print("---------------------------------\n")

if __name__ == "__main__":
    main()