"""
Threat Intelligence Knowledge Base — Local database for known malicious domains and patterns.
"""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "threat_intel.db")

def init_threat_db():
    """Initialise the threat intelligence database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Table for malicious domains
    c.execute('''CREATE TABLE IF NOT EXISTS bad_domains
                 (domain TEXT PRIMARY KEY, reason TEXT, added_at DATETIME)''')
                 
    # Table for known phishing patterns (regex/keywords)
    c.execute('''CREATE TABLE IF NOT EXISTS bad_patterns
                 (pattern TEXT PRIMARY KEY, type TEXT, added_at DATETIME)''')
                 
    # Seed with some defaults
    defaults = [
        ('earn-money.xyz', 'Phishing TLD variation'),
        ('login-verification.top', 'Credential harvesting'),
        ('gift-card-claim.click', 'Reward bait domain'),
    ]
    c.executemany("INSERT OR IGNORE INTO bad_domains VALUES (?, ?, ?)", 
                 [(d, r, datetime.now(timezone.utc).isoformat()) for d, r in defaults])
    
    conn.commit()
    conn.close()

def check_domain_reputation(domain: str) -> dict:
    """Check if a domain exists in our knowledge base."""
    if not os.path.exists(DB_PATH):
        init_threat_db()
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT reason FROM bad_domains WHERE domain = ?", (domain.lower(),))
    res = c.fetchone()
    conn.close()
    
    if res:
        return {"known_threat": True, "reason": res[0]}
    return {"known_threat": False}

def report_malicious_domain(domain: str, reason: str):
    """Add a domain to the local blocklist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bad_domains VALUES (?, ?, ?)",
              (domain.lower(), reason, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_threat_db()
    print("Threat Intel DB initialised.")
