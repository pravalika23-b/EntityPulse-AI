"""
Business Entity Resolution - Candidate Blocking Module
High-recall, memory-efficient candidate generation using tiered multi-key indexing.
"""

from collections import defaultdict
from typing import Dict, List, Set, Tuple
from preprocessing import normalize_business_name, normalize_business_address

# Broad noise and domain-generic terms to filter from single-token blocks
GENERIC_BUSINESS_TERMS = {
    'enterprises', 'services', 'solutions', 'group', 'holdings', 'international',
    'global', 'consulting', 'management', 'tech', 'technologies', 'ventures',
    'systems', 'products', 'industries', 'trading', 'associates', 'properties',
    'development', 'investments', 'financial', 'commercial', 'india', 'national',
    'corporation', 'private', 'limited', 'centre', 'center', 'agency', 'works',
    'france', 'paris', 'delhi', 'mumbai', 'new', 'york', 'texas', 'california'
}

def extract_blocking_keys(name: str, addr: str) -> List[Tuple[str, str]]:
    """
    Extracts multi-tiered blocking keys for candidate generation.
    Returns: list of (tier, key_string)
    """
    norm_name, core_tokens = normalize_business_name(name)
    norm_addr, addr_tokens, num_tokens = normalize_business_address(addr)
    
    keys = []
    
    # Tier 1: Exact core name
    if core_tokens:
        keys.append(('1_cn', 'cn:' + '_'.join(core_tokens[:4])))
        
    # Tier 2: Sorted first 2 core tokens
    if len(core_tokens) >= 2:
        keys.append(('2_s2', 's2:' + '_'.join(sorted(core_tokens[:2]))))
    elif core_tokens:
        keys.append(('2_s2', 's2:' + core_tokens[0]))
        
    # Tier 3: Core token prefix (first 3 chars of tok1 + tok2)
    if len(core_tokens) >= 2 and len(core_tokens[0]) >= 3 and len(core_tokens[1]) >= 3:
        keys.append(('3_pfx', 'pfx:' + core_tokens[0][:3] + '_' + core_tokens[1][:3]))
        
    # Tier 4: Street number + significant street word
    street_words = [
        t for t in addr_tokens
        if not t.isdigit() and len(t) >= 4 and t not in GENERIC_BUSINESS_TERMS
    ]
    if num_tokens and street_words:
        keys.append(('4_num_st', 'num_st:' + num_tokens[0] + '_' + street_words[0]))
        
    # Tier 5: Individual significant tokens (len >= 5, not generic)
    for t in core_tokens[:2]:
        if len(t) >= 5 and t not in GENERIC_BUSINESS_TERMS:
            keys.append(('5_tok', 'tok:' + t))
            
    return keys

def build_s1_index(s1_records: Dict[str, Tuple[str, str]], max_block_size: int = 100):
    """
    Builds an inverted index: key -> list of s1_ids.
    Filters out ultra-large blocks exceeding max_block_size to maintain fast, clean candidate sets.
    """
    raw_index = defaultdict(list)
    for s1_id, (name, addr) in s1_records.items():
        keys = extract_blocking_keys(name, addr)
        # Deduplicate keys per entity
        seen = set()
        for tier, k in keys:
            if k not in seen:
                seen.add(k)
                raw_index[k].append(s1_id)
                
    # Filter out oversaturated buckets
    valid_index = {k: v for k, v in raw_index.items() if len(v) <= max_block_size}
    return valid_index
