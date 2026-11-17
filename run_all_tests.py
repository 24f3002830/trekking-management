"""
Master Test Runner for Trekking Management Application (TMA) - V2.
Runs all milestone verification suites consecutively:
- Milestone 1: Database Models & JWT RBAC Authentication
- Milestone 2: Admin/Staff/User APIs, Slot Management & Redis Caching
- Milestone 3: Celery Batch Jobs, Scheduled Reminders, Monthly Reports & CSV Export
- Milestone 4: Vue.js 3 + Bootstrap 5 Single Page Application & SFC Components
- Milestone 5: End-to-End System Integration Checks
- Milestone 6: Payment Simulation, In-App Notifications & Interactive Analytics
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.test_milestone1 import run_tests as test_m1
from backend.test_milestone2 import run_tests as test_m2
from backend.test_milestone3 import run_tests as test_m3
from backend.test_milestone4 import run_tests as test_m4
from backend.test_milestone5 import run_e2e_tests as test_m5
from backend.test_milestone6 import run_tests as test_m6


def main():
    print("\n" + "#"*70)
    print("🚀 TREKKING MANAGEMENT APPLICATION - COMPLETE PROJECT TEST SUITE")
    print("#"*70)

    try:
        print("\n🔹 [1/6] Running Milestone 1 Tests (Models & Authentication)...")
        test_m1()

        print("\n🔹 [2/6] Running Milestone 2 Tests (CRUD, Overbooking, & Redis Cache)...")
        test_m2()

        print("\n🔹 [3/6] Running Milestone 3 Tests (Celery Tasks & Batch Jobs)...")
        test_m3()

        print("\n🔹 [4/6] Running Milestone 4 Tests (Vue.js 3 SPA & Components)...")
        test_m4()

        print("\n🔹 [5/6] Running Milestone 5 Tests (Master E2E System Checks)...")
        test_m5()

        print("\n🔹 [6/6] Running Milestone 6 Tests (Payment Simulation & Notifications)...")
        test_m6()

        print("\n" + "#"*70)
        print("🏆 ALL 6 MILESTONE TEST SUITES COMPLETED WITH 100% SUCCESS!")
        print("#"*70 + "\n")

    except Exception as e:
        print(f"\n Test suite failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
