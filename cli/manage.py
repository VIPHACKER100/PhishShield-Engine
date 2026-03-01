"""
CLI Management Tool — Orchestrate the email security system (Phase 79).
"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import uvicorn
import sqlite3
from src.utils.logger import logger
from src.utils.config_loader import settings

def main():
    parser = argparse.ArgumentParser(description="Email Phishing Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # 1. Run Server
    server_parser = subparsers.add_parser("serve", help="Start the FastAPI server")
    server_parser.add_argument("--port", type=int, default=settings.get("api.port", 8000))

    # 2. Add Bad Domain
    domain_parser = subparsers.add_parser("block", help="Add domain to threat intelligence blocklist")
    domain_parser.add_argument("domain", help="Domain to block")
    domain_parser.add_argument("--reason", default="Manual block", help="Reason for blocking")

    # 3. View Metrics
    subparsers.add_parser("metrics", help="Display system metrics and threat logs")

    args = parser.parse_args()

    if args.command == "serve":
        logger.info("Starting production server on port %d...", args.port)
        uvicorn.run("src.api.app:app", host="127.0.0.1", port=args.port, reload=True)

    elif args.command == "block":
        from src.security.threat_intel import report_malicious_domain
        report_malicious_domain(args.domain, args.reason)
        print(f"Domain '{args.domain}' added to local blocklist.")

    elif args.command == "metrics":
        print("--- System Intelligence Metrics ---")
        # Query local threat DB
        db_path = os.path.join("data", "threat_intel.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM bad_domains")
            count = c.fetchone()[0]
            print(f"Blocked Domains: {count}")
            conn.close()
        else:
            print("Threat Intelligence DB not initialised.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
