"""
EntityPulse AI - Machine Learning Entity Resolution Service
Connects to our competition-trained LightGBM model and Rapidfuzz feature pipeline.
Scores pairs and classifies them into Auto-Match, Human-In-The-Loop Review, or Non-Match.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# Ensure local and root src are accessible
APP_DIR = Path(__file__).resolve().parent
LOCAL_SRC = APP_DIR / "src"
if LOCAL_SRC.exists() and str(LOCAL_SRC) not in sys.path:
    sys.path.insert(0, str(LOCAL_SRC))

ROOT_DIR = APP_DIR.parent
PARENT_SRC = ROOT_DIR / "code" / "business_entity_resolution" / "src"
if PARENT_SRC.exists() and str(PARENT_SRC) not in sys.path:
    sys.path.insert(0, str(PARENT_SRC))

from preprocessing import clean_text, normalize_business_name, normalize_business_address
from features import extract_pair_features, FEATURE_NAMES
from model import load_model

LOCAL_MODEL = APP_DIR / "models" / "lightgbm_er_model.txt"
PARENT_MODEL = ROOT_DIR / "models" / "lightgbm_er_model.txt"
MODEL_PATH = LOCAL_MODEL if LOCAL_MODEL.exists() else PARENT_MODEL

class ERModelService:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        if MODEL_PATH.exists():
            try:
                self.model = load_model(str(MODEL_PATH))
                print(f"[ERService] Loaded LightGBM model from {MODEL_PATH}")
            except Exception as e:
                print(f"[ERService] Warning: Could not load LightGBM model: {e}")
                self.model = None
        else:
            print(f"[ERService] Model file not found at {MODEL_PATH}")

    def score_pair(self, s1_name: str, s1_addr: str, s2_name: str, s2_addr: str, candidate_id: str = "S2-001") -> Dict[str, Any]:
        """
        Extracts 13 features and scores pair using our LightGBM ER model.
        Returns probability, decision classification, and feature breakdown.
        """
        n1 = clean_text(s1_name)
        a1 = clean_text(s1_addr)
        n2 = clean_text(s2_name)
        a2 = clean_text(s2_addr)

        features = extract_pair_features(n1, a1, n2, a2, candidate_id)
        feature_dict = {name: round(float(val), 4) for name, val in zip(FEATURE_NAMES, features)}

        prob = None
        if self.model:
            try:
                # num_threads=1 prevents OpenMP deadlock/crash in forked Linux workers
                preds = self.model.predict(np.array([features], dtype=np.float32), num_threads=1)
                prob = float(preds[0])
            except Exception as e:
                print(f"[ERService] Model predict warning: {e}, falling back to combined score")
                prob = None

        if prob is None:
            # Fallback heuristic using combined feature score
            prob = float(feature_dict.get("combined_score", 0.0))

        # Classification decision based on our competition-optimized threshold
        if prob >= 0.85:
            decision = "Auto-Match (High Confidence)"
            badge_class = "badge-success"
            action_needed = "Verified Golden Record Merge"
        elif prob >= 0.65:
            decision = "HITL-Review (Borderline Confidence)"
            badge_class = "badge-warning"
            action_needed = "Requires Human-in-the-Loop Sign-Off"
        else:
            decision = "Non-Match (Distinct Entities)"
            badge_class = "badge-danger"
            action_needed = "Separate Entity Accounts"

        return {
            "probability": round(prob, 4),
            "percentage": f"{prob*100:.1f}%",
            "is_match": bool(prob >= 0.85),
            "threshold": 0.85,
            "decision": decision,
            "badge_class": badge_class,
            "action_needed": action_needed,
            "features": feature_dict,
            "normalized": {
                "s1_name": n1,
                "s1_addr": a1,
                "s2_name": n2,
                "s2_addr": a2
            }
        }

# Global singleton
er_service = ERModelService()
