"""
Business Entity Resolution - Feature Engineering Module
Computes robust string similarity and token overlap features between entity pairs using rapidfuzz.
"""

import re
from typing import List
from rapidfuzz import fuzz

FEATURE_NAMES = [
    'name_token_set_ratio',
    'name_token_sort_ratio',
    'name_levenshtein_ratio',
    'name_partial_ratio',
    'name_token_jaccard',
    'name_first_tok_match',
    'name_len_diff_ratio',
    'addr_token_set_ratio',
    'addr_token_sort_ratio',
    'addr_is_empty',
    'addr_num_overlap',
    'combined_score',
    'source_is_s3'
]

def extract_pair_features(n1: str, a1: str, n2: str, a2: str, candidate_id: str) -> List[float]:
    """
    Extracts high-signal similarity features between a Source 1 entity and a candidate S2/S3 entity.
    """
    # Token sets
    tok1 = set(n1.split())
    tok2 = set(n2.split())
    union_tok = tok1 | tok2
    jaccard_name = (len(tok1 & tok2) / len(union_tok)) if union_tok else 0.0
    
    first_tok_match = 1.0 if (n1 and n2 and n1.split()[0] == n2.split()[0]) else 0.0
    
    # Rapidfuzz name similarities
    fuzz_tsr = fuzz.token_sort_ratio(n1, n2) / 100.0
    fuzz_tset = fuzz.token_set_ratio(n1, n2) / 100.0
    fuzz_ratio = fuzz.ratio(n1, n2) / 100.0
    fuzz_partial = fuzz.partial_ratio(n1, n2) / 100.0
    
    len_diff = abs(len(n1) - len(n2)) / max(len(n1), len(n2), 1)
    
    # Address features
    addr_empty = 1.0 if not a2 else 0.0
    if a1 and a2:
        addr_tset = fuzz.token_set_ratio(a1, a2) / 100.0
        addr_tsr = fuzz.token_sort_ratio(a1, a2) / 100.0
    else:
        addr_tset = 0.0
        addr_tsr = 0.0
        
    # Numeric token overlap (house numbers, postal codes)
    nums1 = set(re.findall(r'\b\d+\b', a1))
    nums2 = set(re.findall(r'\b\d+\b', a2))
    if nums1 and nums2:
        num_overlap = 1.0 if (nums1 & nums2) else 0.0
    elif not nums1 and not nums2:
        num_overlap = 0.5
    else:
        num_overlap = 0.2
        
    # Combined score
    combined = 0.60 * fuzz_tset + 0.40 * addr_tset
    source_is_s3 = 1.0 if candidate_id.startswith('S3-') else 0.0
    
    return [
        fuzz_tset,
        fuzz_tsr,
        fuzz_ratio,
        fuzz_partial,
        jaccard_name,
        first_tok_match,
        len_diff,
        addr_tset,
        addr_tsr,
        addr_empty,
        num_overlap,
        combined,
        source_is_s3
    ]
