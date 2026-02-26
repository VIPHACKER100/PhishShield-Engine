"""
Chaos Monkey — Failure Simulation & Resilience Testing (Phase 70).
Randomly injects faults to verify the system's graceful degradation.
"""

import requests
import time
import random

BASE_URL = "http://localhost:8000"

def simulate_load_spike():
    print("🚀 [CHAOS] Simulating concurrent request spike...")
    # Normally would use threading/async, but here simple sequence
    for i in range(20):
        requests.post(f"{BASE_URL}/predict", json={"text": "Test"})
    print("✅ Completed spike test.")

def simulate_ml_outage():
    print("🔥 [CHAOS] Simulating ML model file corruption/missing...")
    os.rename("data/svm.pkl", "data/svm.pkl.bak")
    try:
        res = requests.post(f"{BASE_URL}/predict", json={"text": "Hello", "model": "svm"})
        print(f"Response during outage: {res.status_code} - {res.json()}")
    finally:
        os.rename("data/svm.pkl.bak", "data/svm.pkl")
        print("✅ Restored ML model.")

if __name__ == "__main__":
    import os
    print("--- EMAIL SECURITY CHAOS TESTER ---")
    simulate_ml_outage()
    simulate_load_spike()
