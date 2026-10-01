"""
EntityPulse AI Runner Script
Launches the Flask application on http://127.0.0.1:5000
"""

import sys
import os

# Ensure UTF-8 console output on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add entitypulse_app directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  ENTITYPULSE AI - AI DECISION ENGINE FOR BUSINESS DATA")
    print("  Problem Statement 4 | Team: Hustle Squad")
    print("  Local Dashboard: http://127.0.0.1:5000")
    print("  REST APIs: /api/kpis, /api/entities, /api/actions, /api/upload")
    print("="*70 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
