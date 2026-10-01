"""
Business Entity Resolution - Configuration
Competition Team: Hustle Squad
"""

import os
from pathlib import Path

# Path to src/
SRC_DIR = Path(__file__).resolve().parent
# Path to code/business_entity_resolution
CODE_DIR = SRC_DIR.parent
# Path to project root (scratch/business_entity_resolution)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Dataset paths
DATASET_DIR = PROJECT_ROOT / "student_resource" / "dataset"
TRAIN_DIR = DATASET_DIR / "train"
TEST_DIR = DATASET_DIR / "test"

TRAIN_S1 = TRAIN_DIR / "train_source1.tsv"
TRAIN_S2 = TRAIN_DIR / "train_source2.tsv"
TRAIN_S3 = TRAIN_DIR / "train_source3.tsv"
TRAIN_GT = TRAIN_DIR / "train_ground_truth.tsv"

TEST_S1 = TEST_DIR / "test_source1.tsv"
TEST_S2 = TEST_DIR / "test_source2.tsv"
TEST_S3 = TEST_DIR / "test_source3.tsv"

# Output paths
OUTPUT_DIR = PROJECT_ROOT / "output"
MATCHING_RESULTS_PATH = OUTPUT_DIR / "matching_results.tsv"
CANDIDATE_PAIRS_PATH = OUTPUT_DIR / "candidate_pairs.tsv"

# Model artifact path
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "lightgbm_er_model.txt"

# Blocking hyperparameters
MAX_CANDIDATES_PER_S1 = 25
MAX_BLOCK_SIZE = 80  # Cap for single block size to avoid noisy generic words

# Classification threshold (precision-heavy for F_0.5 metric)
DEFAULT_MATCH_THRESHOLD = 0.65

# Model Training Parameters
LIGHTGBM_PARAMS = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'boosting_type': 'gbdt',
    'learning_rate': 0.08,
    'num_leaves': 45,
    'max_depth': 7,
    'min_child_samples': 30,
    'feature_fraction': 0.85,
    'bagging_fraction': 0.85,
    'bagging_freq': 3,
    'verbose': -1,
    'random_state': 42,
    'n_jobs': -1
}
NUM_BOOST_ROUNDS = 180

# Random Seed
RANDOM_SEED = 42
