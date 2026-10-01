"""
Business Entity Resolution - Data Loader Module
Memory-efficient streaming and country partitioning for multi-million row TSV files.
Strictly uses tab separator (sep="\t").
"""

import os
from collections import defaultdict
from typing import Dict, Iterator, Set, Tuple, Optional

def load_source1_records(path: str) -> Dict[str, Dict[str, Tuple[str, str]]]:
    """
    Loads Source 1 records partitioned by country.
    Returns: {country_name: {s1_id: (business_name, business_address)}}
    """
    country_partitions = defaultdict(dict)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline().rstrip('\r\n').split('\t')
        for line in f:
            parts = line.rstrip('\r\n').split('\t')
            if len(parts) >= 4:
                s1_id, name, addr, country = parts[0], parts[1], parts[2], parts[3]
                country_partitions[country.strip()][s1_id.strip()] = (name, addr)
    return country_partitions

def stream_source_records(path: str, target_country: Optional[str] = None) -> Iterator[Tuple[str, str, str, str]]:
    """
    Streams records from S2 or S3.
    Yields: (entity_id, business_name, business_address, country)
    """
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline()
        for line in f:
            parts = line.rstrip('\r\n').split('\t')
            if len(parts) >= 4:
                entity_id, name, addr, country = parts[0].strip(), parts[1], parts[2], parts[3].strip()
                if target_country is None or country == target_country:
                    yield entity_id, name, addr, country

def load_ground_truth(path: str, filter_s1_ids: Optional[Set[str]] = None) -> Dict[str, Set[str]]:
    """
    Loads ground truth mapping: source1_entity_id -> set of matched_entity_ids.
    """
    gt = {}
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline()
        for line in f:
            parts = line.rstrip('\r\n').split('\t')
            if parts:
                s1_id = parts[0].strip()
                if filter_s1_ids is not None and s1_id not in filter_s1_ids:
                    continue
                matches = parts[1].split(',') if len(parts) > 1 and parts[1].strip() else []
                gt[s1_id] = {m.strip() for m in matches if m.strip()}
    return gt
