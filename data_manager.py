"""
EntityPulse AI - Data Manager Module
Loads multi-source business entity records (Source 1 Reference, Source 2 ERP, Source 3 Procurement)
and enriches them with enterprise spend, contract rates, and invoice histories.
"""

import os
import json
from typing import Dict, List, Any

# Curated enterprise dataset combining real records from S1, S2, and S3 with transactional enterprise data
SAMPLE_ENTITIES = [
    {
        "golden_id": "GOLD-001",
        "canonical_name": "Moran Staffing LLC",
        "canonical_address": "1902 Shamrock Road, Dothan, AL",
        "country": "US",
        "category": "Contingent Labor & Staffing",
        "raw_records": [
            {
                "source": "Source 1 (Reference CRM)",
                "record_id": "S1-401761505",
                "business_name": "Moran Staffing LLC",
                "business_address": "1902 Shamrock Road, Dothan, AL",
                "country": "US",
                "department": "Corporate HQ",
                "contract_rate": 65.00,
                "annual_spend": 520000,
                "invoices": [
                    {"inv_no": "INV-2026-101", "amount": 42000, "date": "2026-08-15", "status": "Paid"},
                    {"inv_no": "INV-2026-102", "amount": 44500, "date": "2026-09-15", "status": "Pending"}
                ]
            },
            {
                "source": "Source 2 (Legacy ERP)",
                "record_id": "S2-422370961",
                "business_name": "Moran Staffing LLC",
                "business_address": "1902 SHAMROCK ROAD, null, DOTHAN, AL",
                "country": "US",
                "department": "Southeast Operations",
                "contract_rate": 82.50,  # PRICING ANOMALY: $17.50/hr premium!
                "annual_spend": 395000,
                "invoices": [
                    {"inv_no": "INV-9942", "amount": 33000, "date": "2026-08-18", "status": "Paid"},
                    {"inv_no": "INV-9988", "amount": 42000, "date": "2026-08-15", "status": "Duplicate Flag"}  # DUPLICATE INVOICE!
                ]
            },
            {
                "source": "Source 3 (Field Procurement)",
                "record_id": "S3-167233960",
                "business_name": "LLC Moran Staffing",  # INVERTED WORD ORDER
                "business_address": "1902 Shamrock Rd, Alabama, Dothan",
                "country": "US",
                "department": "Logistics & Fleet",
                "contract_rate": 78.00,
                "annual_spend": 280000,
                "invoices": [
                    {"inv_no": "FLT-041", "amount": 23000, "date": "2026-09-01", "status": "Paid"}
                ]
            }
        ]
    },
    {
        "golden_id": "GOLD-002",
        "canonical_name": "Modern Packaging Global PC",
        "canonical_address": "8935 Georgetown Pike, Fairfax County, VA",
        "country": "US",
        "category": "Industrial Packaging & Logistics",
        "raw_records": [
            {
                "source": "Source 1 (Reference CRM)",
                "record_id": "S1-844896591",
                "business_name": "Modern Packaging Global PC",
                "business_address": "8935 Georgetown Pike, Fairfax County, VA",
                "country": "US",
                "department": "Supply Chain Central",
                "contract_rate": 14.20,
                "annual_spend": 1250000,
                "invoices": [
                    {"inv_no": "PKG-8821", "amount": 105000, "date": "2026-07-20", "status": "Paid"},
                    {"inv_no": "PKG-8902", "amount": 112000, "date": "2026-08-25", "status": "Paid"}
                ]
            },
            {
                "source": "Source 2 (Legacy ERP)",
                "record_id": "S2-362218588",
                "business_name": "MODERN PACKAGING GLOBAL PC",
                "business_address": "8935 Georgetown Pike, FAIRFAX COUNTY, VA",
                "country": "US",
                "department": "Mid-Atlantic Warehousing",
                "contract_rate": 16.80,  # $2.60/unit higher
                "annual_spend": 640000,
                "invoices": [
                    {"inv_no": "MPG-VA-11", "amount": 54000, "date": "2026-08-10", "status": "Paid"}
                ]
            },
            {
                "source": "Source 3 (Field Procurement)",
                "record_id": "S3-11966366",
                "business_name": "Modern Packaging Global Pc",
                "business_address": "8935 Georgetown Pike, Fairfax County, Virginia",
                "country": "US",
                "department": "E-Commerce Fulfillment",
                "contract_rate": 15.50,
                "annual_spend": 410000,
                "invoices": [
                    {"inv_no": "EC-PKG-44", "amount": 34000, "date": "2026-09-02", "status": "Pending"}
                ]
            }
        ]
    },
    {
        "golden_id": "GOLD-003",
        "canonical_name": "QH Vendome, L.L.C.",
        "canonical_address": "21342 Bending Green Way, Katy, TX",
        "country": "US",
        "category": "Commercial Real Estate & Facilities",
        "raw_records": [
            {
                "source": "Source 1 (Reference CRM)",
                "record_id": "S1-378978603",
                "business_name": "QH Vendome, L.L.C.",
                "business_address": "Katy, TX, 21342 Bending Green Way",
                "country": "US",
                "department": "Facilities Management",
                "contract_rate": 18500.00,
                "annual_spend": 222000,
                "invoices": [
                    {"inv_no": "RENT-08", "amount": 18500, "date": "2026-08-01", "status": "Paid"}
                ]
            },
            {
                "source": "Source 2 (Legacy ERP)",
                "record_id": "S2-319300693",
                "business_name": "QH Vendome, LLC",
                "business_address": "21342 BENDING GREEN WAY, KATY, TX",
                "country": "US",
                "department": "Regional Office",
                "contract_rate": 18500.00,
                "annual_spend": 222000,
                "invoices": [
                    {"inv_no": "TX-LEASE-8", "amount": 18500, "date": "2026-08-01", "status": "Duplicate Flag"} # DUPLICATE RENT PAYMENT!
                ]
            }
        ]
    },
    {
        "golden_id": "GOLD-004",
        "canonical_name": "Porur Vyapar Private Limited",
        "canonical_address": "No.137 Gandhi Street, Porur, Chennai, Tamil Nadu",
        "country": "India",
        "category": "Industrial Raw Materials",
        "raw_records": [
            {
                "source": "Source 1 (Reference CRM)",
                "record_id": "S1-258353664",
                "business_name": "Porur Vyapar Private Limited",
                "business_address": "No.137, Gandhi Street, 2Nd Main Road Subhashri Nagar, Mugalivakkam, Porur, Chennai, Tamil Nadu",
                "country": "India",
                "department": "India Manufacturing",
                "contract_rate": 450.00,
                "annual_spend": 8500000,
                "invoices": [
                    {"inv_no": "PV-2026-01", "amount": 750000, "date": "2026-08-10", "status": "Paid"},
                    {"inv_no": "PV-2026-02", "amount": 800000, "date": "2026-09-12", "status": "Pending"}
                ]
            },
            {
                "source": "Source 2 (Legacy ERP)",
                "record_id": "S2-546821025",
                "business_name": "Porur Vyapar Private Private Limited", # Typo: duplicate "Private"
                "business_address": "137 Gandhi St, Mugalivakkam, Chennai",
                "country": "India",
                "department": "Chennai Plant",
                "contract_rate": 495.00,  # 10% price variance
                "annual_spend": 4200000,
                "invoices": [
                    {"inv_no": "CHN-INV-99", "amount": 350000, "date": "2026-08-15", "status": "Paid"}
                ]
            }
        ]
    },
    {
        "golden_id": "GOLD-005",
        "canonical_name": "Blue Network Corporation",
        "canonical_address": "177 1st Avenue, Nashville, TN",
        "country": "US",
        "category": "IT Infrastructure & Cloud Networking",
        "raw_records": [
            {
                "source": "Source 1 (Reference CRM)",
                "record_id": "S1-447452795",
                "business_name": "Blue Network Corporation",
                "business_address": "177 1st Avenue, Nashville, TN",
                "country": "US",
                "department": "Global IT",
                "contract_rate": 9500.00,
                "annual_spend": 114000,
                "invoices": [
                    {"inv_no": "BNC-08", "amount": 9500, "date": "2026-08-01", "status": "Paid"}
                ]
            },
            {
                "source": "Source 2 (Legacy ERP)",
                "record_id": "S2-995233298",
                "business_name": "The Blue Netw0rk Corporation", # Typo: 'Netw0rk'
                "business_address": "177 1TH AVENUE, NASHVILLE, TN",
                "country": "US",
                "department": "Digital Marketing",
                "contract_rate": 12800.00,  # $3,300/mo discrepancy
                "annual_spend": 153600,
                "invoices": [
                    {"inv_no": "NET-MKTG-1", "amount": 12800, "date": "2026-08-05", "status": "Paid"}
                ]
            }
        ]
    },
    {
        "golden_id": "GOLD-006",
        "canonical_name": "SARL Atelier Numerique Paris",
        "canonical_address": "14 Rue de Rivoli, 75001 Paris",
        "country": "France",
        "category": "Digital Product Design & UX",
        "raw_records": [
            {
                "source": "Source 1 (Reference CRM)",
                "record_id": "S1-FR-90112",
                "business_name": "SARL Atelier Numerique Paris",
                "business_address": "14 Rue de Rivoli, 75001 Paris",
                "country": "France",
                "department": "Europe Product Lab",
                "contract_rate": 95.00,
                "annual_spend": 380000,
                "invoices": [
                    {"inv_no": "AN-PARIS-01", "amount": 32000, "date": "2026-08-20", "status": "Paid"}
                ]
            },
            {
                "source": "Source 3 (Field Procurement)",
                "record_id": "S3-FR-88104",
                "business_name": "Atelier Numerique SASU",  # Legal suffix variation: SARL vs SASU
                "business_address": "14 R. de Rivoli, Paris 75001",
                "country": "France",
                "department": "Paris Innovation Hub",
                "contract_rate": 115.00,
                "annual_spend": 230000,
                "invoices": [
                    {"inv_no": "AN-FR-55", "amount": 28000, "date": "2026-08-22", "status": "Pending"}
                ]
            }
        ]
    }
]

BORDERLINE_HITL_PAIRS = [
    {
        "review_id": "HITL-701",
        "s1_id": "S1-586699005",
        "s1_name": "Advanced Intelligence Products Inc",
        "s1_addr": "300 Swift Avenue, Unit 5, Durham, NC",
        "cand_id": "S2-481348736",
        "cand_name": "DREXTAVO AI LLC",
        "cand_addr": "300 SWIFT AVE, DURHAM, NC",
        "country": "US",
        "model_confidence": 0.764,
        "match_tier": "Tier 4 (Same Commercial Address)",
        "features_summary": {
            "address_similarity": "98%",
            "name_similarity": "18%",
            "exact_street_number": "Match (300)",
            "risk_notes": "Possible trade name / DBA sharing identical building premises. Requires human verification before merging vendor accounts."
        }
    },
    {
        "review_id": "HITL-702",
        "s1_id": "S1-205963340",
        "s1_name": "Secure Marketing Technologies LLC",
        "s1_addr": "982 Willman Pike, Hartford City, IN",
        "cand_id": "S2-616502408",
        "cand_name": "technologiesmarketing.com",
        "cand_addr": "HARTFORD CITY, WILLMAN PIKE, IN",
        "country": "US",
        "model_confidence": 0.728,
        "match_tier": "Tier 5 (Token Overlap & Road Match)",
        "features_summary": {
            "address_similarity": "84%",
            "name_similarity": "62%",
            "exact_street_number": "Missing in ERP",
            "risk_notes": "ERP record stored vendor URL instead of formal company name. Address road matches."
        }
    }
]

def _enrich_entity(e: Dict[str, Any]) -> Dict[str, Any]:
    e_copy = dict(e)
    raw = e.get("raw_records", [])
    total_spend = sum(r.get("annual_spend", 0) for r in raw)
    
    linked = []
    grounded = []
    anomalies = []
    
    rates = [r.get("contract_rate", 0) for r in raw if r.get("contract_rate")]
    if len(rates) > 1 and max(rates) > min(rates):
        diff = max(rates) - min(rates)
        anomalies.append({
            "type": "Contract Rate Disparity",
            "description": f"Rate variance of ${diff:.2f}/hr detected across operational divisions."
        })
        
    for r in raw:
        rid = r.get("record_id", "")
        grounded.append(rid)
        linked.append({
            "source": r.get("source", ""),
            "source_id": rid,
            "raw_name": r.get("business_name", ""),
            "raw_address": r.get("business_address", ""),
            "spend": r.get("annual_spend", 0),
            "contract_rate": r.get("contract_rate", 0.0),
            "invoices": r.get("invoices", [])
        })
        for inv in r.get("invoices", []):
            if inv.get("status") == "Duplicate Flag":
                anomalies.append({
                    "type": "Duplicate Invoice Flag",
                    "description": f"Invoice {inv.get('inv_no')} (${inv.get('amount'):,}) matches corporate invoice date and sum."
                })
                
    e_copy["total_spend"] = total_spend
    e_copy["linked_source_records"] = linked
    e_copy["grounded_sources"] = grounded
    e_copy["anomalies"] = anomalies
    return e_copy

def get_all_golden_entities() -> List[Dict[str, Any]]:
    return [_enrich_entity(e) for e in SAMPLE_ENTITIES]

def get_golden_entity_by_id(golden_id: str) -> Dict[str, Any]:
    for e in SAMPLE_ENTITIES:
        if e["golden_id"] == golden_id:
            return _enrich_entity(e)
    return None

def get_hitl_queue() -> List[Dict[str, Any]]:
    queue = []
    for item in BORDERLINE_HITL_PAIRS:
        queue.append({
            "review_id": item["review_id"],
            "variance_reason": item["features_summary"].get("risk_notes", ""),
            "model_probability": item["model_confidence"],
            "match_tier": item.get("match_tier", ""),
            "features_summary": item.get("features_summary", {}),
            "entity_candidate_1": {
                "source": "Source 1 (Reference CRM)",
                "id": item["s1_id"],
                "name": item["s1_name"],
                "address": item["s1_addr"],
                "spend": 145000
            },
            "entity_candidate_2": {
                "source": "Source 2 (Legacy ERP)",
                "id": item["cand_id"],
                "name": item["cand_name"],
                "address": item["cand_addr"],
                "spend": 98000
            }
        })
    return queue

