"""
Business Entity Resolution - Model Module
LightGBM gradient-boosted decision trees for precision-oriented candidate pair classification.
Complies with MIT license and parameter limits (< 8 billion parameters).
"""

import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import lightgbm as lgb
from config import LIGHTGBM_PARAMS, NUM_BOOST_ROUNDS, MODEL_PATH
from features import FEATURE_NAMES

def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: Optional[np.ndarray] = None,
    y_val: Optional[np.ndarray] = None,
    params: Optional[Dict] = None,
    num_rounds: int = NUM_BOOST_ROUNDS
) -> lgb.Booster:
    """
    Trains a LightGBM binary classifier on candidate pair features.
    """
    train_params = params or LIGHTGBM_PARAMS
    train_data = lgb.Dataset(X_train, label=y_train, feature_name=FEATURE_NAMES)
    
    valid_sets = [train_data]
    if X_val is not None and y_val is not None:
        val_data = lgb.Dataset(X_val, label=y_val, feature_name=FEATURE_NAMES, reference=train_data)
        valid_sets.append(val_data)
        
    booster = lgb.train(
        train_params,
        train_data,
        num_boost_round=num_rounds,
        valid_sets=valid_sets
    )
    return booster

def save_model(booster: lgb.Booster, path: str = str(MODEL_PATH)) -> None:
    """Saves the LightGBM model to text format."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    booster.save_model(path)

def load_model(path: str = str(MODEL_PATH)) -> lgb.Booster:
    """Loads the trained LightGBM model from text format."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Model file not found at {path}")
    return lgb.Booster(model_file=path)

def predict_probabilities(booster: lgb.Booster, X: np.ndarray) -> np.ndarray:
    """Predicts match probabilities for a matrix of candidate pair features."""
    if len(X) == 0:
        return np.array([], dtype=np.float32)
    return booster.predict(X)

def get_feature_importances(booster: lgb.Booster) -> List[Tuple[str, float]]:
    """Returns sorted feature importances (gain-based)."""
    gains = booster.feature_importance(importance_type='gain')
    total_gain = sum(gains) if sum(gains) > 0 else 1.0
    relative_gains = [g / total_gain for g in gains]
    return sorted(zip(FEATURE_NAMES, relative_gains), key=lambda x: x[1], reverse=True)
