"""
Business Entity Resolution - Preprocessing Module
Implements fast, robust text normalization for names and addresses across US, India, and France.
Zero external APIs or internet lookups.
"""

import re
import unicodedata

# Comprehensive legal suffixes across US, India, France, and international entities
LEGAL_SUFFIXES = {
    # US & General
    'llc', 'inc', 'corp', 'corporation', 'incorporated', 'co', 'company',
    'ltd', 'limited', 'pvt', 'private', 'pvt ltd', 'plc', 'gmbh', 'pc', 'llp',
    'lp', 'pa', 'chartered', 'holdings', 'group',
    # France
    'sarl', 'sas', 'sasu', 'eurl', 'sa', 'sci', 'snc', 'gie', 'sca', 'scs',
    'selarl', 'earl', 'gaec', 'associes', 'associe'
}

# Common noise words in names
NAME_STOPWORDS = {
    'the', 'a', 'an', 'and', 'of', 'in', 'at', 'on', 'for', 'to', 'from',
    # French articles
    'le', 'la', 'les', 'du', 'des', 'de', 'et'
}

# Address abbreviation mappings
ADDR_ABBREVIATIONS = {
    'st': 'street',
    'rd': 'road',
    'ave': 'avenue',
    'av': 'avenue',
    'blvd': 'boulevard',
    'bd': 'boulevard',
    'dr': 'drive',
    'ln': 'lane',
    'ct': 'court',
    'pl': 'place',
    'pkwy': 'parkway',
    'hwy': 'highway',
    'apt': 'apartment',
    'ste': 'suite',
    'bldg': 'building',
    'fl': 'floor',
    'all': 'allee',
    'imp': 'impasse',
    'chem': 'chemin'
}

def clean_text(s: str) -> str:
    """Normalize unicode, lowercase, standardize ampersands, and strip symbols."""
    if not s or s.lower() == 'null' or s.lower() == 'nan':
        return ''
    # Unicode NFKD decomposition and ASCII transliteration
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8').lower()
    s = s.replace('&', ' and ')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    return ' '.join(s.split())

def normalize_business_name(name: str):
    """
    Returns:
        norm_name: string with punctuation removed, lowercased
        core_tokens: list of non-stopword, non-legal-suffix core business name tokens
    """
    cleaned = clean_text(name)
    tokens = cleaned.split()
    core_tokens = [t for t in tokens if t not in LEGAL_SUFFIXES and t not in NAME_STOPWORDS]
    if not core_tokens:
        core_tokens = [t for t in tokens if t not in NAME_STOPWORDS]
    if not core_tokens:
        core_tokens = tokens
    return cleaned, core_tokens

def normalize_business_address(addr: str):
    """
    Returns:
        norm_addr: normalized address with expanded abbreviations and removed noise
        addr_tokens: list of words in address
        num_tokens: list of numeric tokens (house number, postal/PIN code)
    """
    cleaned = clean_text(addr)
    # Remove null tokens
    cleaned = re.sub(r'\bnull\b', ' ', cleaned)
    tokens = cleaned.split()
    
    # Standardize road / unit abbreviations
    expanded = [ADDR_ABBREVIATIONS.get(t, t) for t in tokens]
    norm_addr = ' '.join(expanded)
    
    # Extract numbers
    nums = [t for t in tokens if t.isdigit() and len(t) <= 6]
    
    return norm_addr, expanded, nums
