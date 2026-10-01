"""
Business Entity Resolution - Main Pipeline
Team: Hustle Squad
End-to-end CLI for training, validation, and country-partitioned streaming test inference.
Generates output/matching_results.tsv and output/candidate_pairs.tsv.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from collections import defaultdict
import numpy as np

# Ensure src directory is in sys.path
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config
from preprocessing import clean_text, normalize_business_name, normalize_business_address
from blocking import extract_blocking_keys
from features import extract_pair_features, FEATURE_NAMES
from model import train_model, save_model, load_model, predict_probabilities
from evaluation import evaluate_macro_f05

def run_test_inference(model_path: Path, test_dir: Path, output_dir: Path, threshold: float = 0.85):
    """
    Streams test data partitioned by country (France, US, India) to maintain lean memory
    and writes matching_results.tsv and candidate_pairs.tsv.
    """
    print("\n" + "="*75)
    print("  RUNNING TEST INFERENCE (Country-Partitioned Streaming)")
    print(f"  Test Directory: {test_dir}")
    print(f"  Output Directory: {output_dir}")
    print(f"  Decision Threshold: {threshold}")
    print("="*75)

    os.makedirs(output_dir, exist_ok=True)
    matching_out_path = output_dir / "matching_results.tsv"
    candidate_out_path = output_dir / "candidate_pairs.tsv"

    test_s1_path = test_dir / "test_source1.tsv"
    test_s2_path = test_dir / "test_source2.tsv"
    test_s3_path = test_dir / "test_source3.tsv"

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. Train the model first.")

    print("\nLoading trained LightGBM model...")
    booster = load_model(str(model_path))
    print("Model loaded successfully.")

    # 1. Read all S1 entities to guarantee order and complete coverage
    print("\n[Step 1] Reading test_source1.tsv and partitioning by country...")
    s1_all_ids = []
    s1_by_country = defaultdict(dict)

    with open(test_s1_path, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline().rstrip('\r\n').split('\t')
        for line in f:
            parts = line.rstrip('\r\n').split('\t')
            if len(parts) >= 4:
                s1_id = parts[0].strip()
                name = clean_text(parts[1])
                addr = clean_text(parts[2])
                country = parts[3].strip()
                s1_all_ids.append(s1_id)
                s1_by_country[country][s1_id] = (name, addr)

    total_test_s1 = len(s1_all_ids)
    print(f"Total Test Source 1 entities: {total_test_s1:,}")
    for c, recs in s1_by_country.items():
        print(f"  Country '{c}': {len(recs):,} entities ({len(recs)/total_test_s1*100:.2f}%)")

    # Storage for final predictions: s1_id -> (candidate_ids_set, matched_ids_set)
    final_matches = {}
    final_candidates = {}

    # 2. Process each country sequentially
    for country, s1_recs in s1_by_country.items():
        print("\n" + "-"*65)
        print(f"  Processing Country: {country} ({len(s1_recs):,} entities)")
        print("-"*65)

        t_c_start = time.time()

        # Build tiered inverted index for S1 entities in this country
        # key -> list of (tier, s1_id)
        print("  Building S1 blocking index...")
        tier_index = defaultdict(list)
        for s1_id, (n, a) in s1_recs.items():
            for tier, k in extract_blocking_keys(n, a):
                tier_index[k].append((tier, s1_id))

        # Filter out blocks with > 100 entities to avoid noisy terms
        valid_tier_index = {k: v for k, v in tier_index.items() if len(v) <= 100}
        print(f"  Retained {len(valid_tier_index):,} blocking keys.")

        # Candidate buckets per S1 entity
        # High-priority: tier 1 & 2 (cn, s2) up to 8
        # Secondary: tier 3, 4, 5 (pfx, num_st, tok) up to 6
        cands_high = defaultdict(dict)  # s1_id -> {mid: (name, addr)}
        cands_sec = defaultdict(dict)

        # Stream test_source2 and test_source3 for this country
        print(f"  Streaming {test_s2_path.name} and {test_s3_path.name} for country '{country}'...")
        t_stream = time.time()
        scanned_s2_s3 = 0

        for fn in [test_s2_path, test_s3_path]:
            with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
                f.readline()
                for line in f:
                    parts = line.rstrip('\r\n').split('\t')
                    if len(parts) >= 4 and parts[3].strip() == country:
                        scanned_s2_s3 += 1
                        mid = parts[0].strip()
                        n2 = clean_text(parts[1])
                        a2 = clean_text(parts[2])

                        keys = extract_blocking_keys(n2, a2)
                        for tier, k in keys:
                            matches = valid_tier_index.get(k)
                            if matches:
                                for s1_tier, s1_id in matches:
                                    if s1_tier in ('1_cn', '2_s2'):
                                        if len(cands_high[s1_id]) < 8:
                                            cands_high[s1_id][mid] = (n2, a2)
                                    else:
                                        if len(cands_sec[s1_id]) < 6:
                                            cands_sec[s1_id][mid] = (n2, a2)

        print(f"  Streaming finished in {time.time()-t_stream:.1f}s. Scanned {scanned_s2_s3:,} {country} records.")

        # Score candidates for each S1 entity in this country
        print("  Scoring candidate pairs with LightGBM...")
        t_score = time.time()
        for s1_id, (n1, a1) in s1_recs.items():
            # Combine high-priority and secondary candidates
            all_cands_dict = {}
            all_cands_dict.update(cands_high.get(s1_id, {}))
            all_cands_dict.update(cands_sec.get(s1_id, {}))

            if not all_cands_dict:
                final_candidates[s1_id] = []
                final_matches[s1_id] = []
                continue

            cand_items = list(all_cands_dict.items())
            cand_ids = [mid for mid, _ in cand_items]
            final_candidates[s1_id] = cand_ids

            # Extract features for all candidates of this entity
            feats = [
                extract_pair_features(n1, a1, n2, a2, mid)
                for mid, (n2, a2) in cand_items
            ]
            probs = booster.predict(np.array(feats, dtype=np.float32))

            # Filter by threshold
            matched_ids = [mid for mid, prob in zip(cand_ids, probs) if prob >= threshold]
            final_matches[s1_id] = matched_ids

        print(f"  Scoring finished in {time.time()-t_score:.1f}s. Country {country} took {time.time()-t_c_start:.1f}s total.")

        # Clear country indices from memory
        del tier_index, valid_tier_index, cands_high, cands_sec

    # 3. Write final output files in exact S1 order
    print("\n[Step 3] Writing final submission files...")
    print(f"  Writing {matching_out_path}...")
    with open(matching_out_path, 'w', encoding='utf-8') as f:
        f.write("source1_entity_id\tmatched_entity_ids\n")
        for s1_id in s1_all_ids:
            m_list = final_matches.get(s1_id, [])
            m_str = ",".join(m_list)
            f.write(f"{s1_id}\t{m_str}\n")

    print(f"  Writing {candidate_out_path}...")
    with open(candidate_out_path, 'w', encoding='utf-8') as f:
        f.write("source1_entity_id\tcandidate_entity_ids\n")
        for s1_id in s1_all_ids:
            c_list = final_candidates.get(s1_id, [])
            c_str = ",".join(c_list)
            f.write(f"{s1_id}\t{c_str}\n")

    print(f"\nSuccessfully generated:")
    print(f"  1. {matching_out_path} ({os.path.getsize(matching_out_path):,} bytes)")
    print(f"  2. {candidate_out_path} ({os.path.getsize(candidate_out_path):,} bytes)")

    # Output sanity checks
    total_matched_links = sum(len(m) for m in final_matches.values())
    total_candidate_links = sum(len(c) for c in final_candidates.values())
    empty_matches = sum(1 for m in final_matches.values() if len(m) == 0)
    print(f"\nFinal Statistics:")
    print(f"  Total S1 rows written : {len(s1_all_ids):,}")
    print(f"  Entities with 0 matches (singletons): {empty_matches:,} ({empty_matches/len(s1_all_ids)*100:.2f}%)")
    print(f"  Total predicted matches: {total_matched_links:,}")
    print(f"  Total candidate pairs  : {total_candidate_links:,}")
    print("="*75)

def main():
    parser = argparse.ArgumentParser(description="Business Entity Resolution Pipeline - Team Hustle Squad")
    parser.add_argument("--mode", choices=["train", "infer", "all"], default="infer",
                        help="Execution mode: train, infer, or all (default: infer)")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="Match probability decision threshold (default: 0.85)")
    parser.add_argument("--model-path", type=str, default=str(config.MODEL_PATH),
                        help="Path to LightGBM model file")
    parser.add_argument("--test-dir", type=str, default=str(config.TEST_DIR),
                        help="Path to dataset/test directory")
    parser.add_argument("--output-dir", type=str, default=str(config.OUTPUT_DIR),
                        help="Path to output directory")
    args = parser.parse_args()

    model_path = Path(args.model_path)
    test_dir = Path(args.test_dir)
    output_dir = Path(args.output_dir)

    if args.mode in ["infer", "all"]:
        run_test_inference(model_path, test_dir, output_dir, threshold=args.threshold)

if __name__ == '__main__':
    main()
