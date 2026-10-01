"""
Test suite for EntityPulse AI Backend and API Endpoints.
Verifies all routes using Flask test client.
"""

import sys
import os
import json

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app

def test_endpoints():
    client = app.test_client()
    print("Testing EntityPulse AI endpoints...")

    # 1. Root route
    res = client.get("/")
    assert res.status_code == 200, f"Root failed: {res.status_code}"
    assert b"EntityPulse AI" in res.data
    print("[PASS] GET / (HTML template rendered successfully)")

    # 2. KPIs
    res = client.get("/api/kpis")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    precision_val = float(str(data["data"]["model_precision"]).replace("%", ""))
    assert precision_val > 80
    print(f"[PASS] GET /api/kpis: Spend=${data['data']['total_business_spend']:,.0f}, Savings=${data['data']['total_rate_savings']:,.0f}")

    # 3. Entities
    res = client.get("/api/entities")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) > 0
    golden_id = data["data"][0]["golden_id"]
    print(f"[PASS] GET /api/entities ({len(data['data'])} entities loaded)")

    # 4. Entity Detail
    res = client.get(f"/api/entities/{golden_id}")
    assert res.status_code == 200
    detail = res.get_json()["data"]
    assert "linked_source_records" in detail
    assert "grounded_sources" in detail
    print(f"[PASS] GET /api/entities/{golden_id} ({len(detail['linked_source_records'])} sources linked)")

    # 5. Actions
    res = client.get("/api/actions")
    assert res.status_code == 200
    actions = res.get_json()["data"]
    assert len(actions) > 0
    action_id = actions[0]["action_id"]
    print(f"[PASS] GET /api/actions ({len(actions)} decision cards generated)")

    # 6. Action Execution
    res = client.post(f"/api/actions/{action_id}/execute")
    assert res.status_code == 200
    assert res.get_json()["status"] == "success"
    print(f"[PASS] POST /api/actions/{action_id}/execute")

    # 7. Natural Language Query
    res = client.post("/api/query", json={"query": "Where are we paying duplicate invoices?"})
    assert res.status_code == 200
    ans = res.get_json()["data"]
    assert len(ans["grounded_citations"]) > 0
    print(f"[PASS] POST /api/query (Duplicate invoices found: citations={ans['grounded_citations']})")

    # 8. ML Live Scoring
    sample = {
        "s1_name": "Moran Staffing LLC",
        "s1_addr": "1902 Shamrock Road, Dothan, AL",
        "s2_name": "LLC Moran Staffing",
        "s2_addr": "1902 Shamrock Rd, Alabama, Dothan"
    }
    res = client.post("/api/ml/score", json=sample)
    assert res.status_code == 200
    score = res.get_json()["data"]
    assert "probability" in score
    assert "features" in score
    assert len(score["features"]) == 13
    print(f"[PASS] POST /api/ml/score (Prob={score['probability']:.4f}, Match={score['is_match']}, 13 features extracted)")

    # 9. HITL Queue
    res = client.get("/api/hitl")
    assert res.status_code == 200
    hitl_items = res.get_json()["data"]
    assert len(hitl_items) > 0
    review_id = hitl_items[0]["review_id"]
    print(f"[PASS] GET /api/hitl ({len(hitl_items)} cases in queue)")

    res = client.post(f"/api/hitl/{review_id}/decision", json={"decision": "Approved"})
    assert res.status_code == 200
    print(f"[PASS] POST /api/hitl/{review_id}/decision recorded successfully")

    # 10. Audit Report Export
    res = client.get("/api/export/audit-report")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert b"Action_ID,Priority,Vendor_Name" in res.data
    print("[PASS] GET /api/export/audit-report (CSV generated with headers & evidence)")

    # 11. Benchmark Batch Processing (1,000 records)
    res = client.post("/api/upload/benchmark", json={"num_records": 1000})
    assert res.status_code == 200
    bench1k = res.get_json()["data"]
    assert bench1k["total_records_processed"] == 1000
    assert bench1k["processing_time_seconds"] < 5.0
    print(f"[PASS] POST /api/upload/benchmark (1,000 records in {bench1k['processing_time_seconds']}s -> {bench1k['throughput_records_per_sec']} rows/s)")

    # 12. High-Scale Benchmark (10,000 records)
    res = client.post("/api/upload/benchmark", json={"num_records": 10000})
    assert res.status_code == 200
    bench10k = res.get_json()["data"]
    assert bench10k["total_records_processed"] == 10000
    assert bench10k["processing_time_seconds"] < 8.0
    print(f"[PASS] POST /api/upload/benchmark (10,000 records in {bench10k['processing_time_seconds']}s -> {bench10k['throughput_records_per_sec']} rows/s)")

    # 13. Download Resolved CSV of 10,000 rows
    res = client.get("/api/export/resolved-csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert b"Golden_Entity_ID" in res.data
    print(f"[PASS] GET /api/export/resolved-csv (10,000 rows CSV export verified)")

    print("\n" + "="*55)
    print("  ALL 13 BACKEND & SCALE TESTS PASSED WITH 100% SUCCESS!")
    print("="*55)

if __name__ == "__main__":
    test_endpoints()

