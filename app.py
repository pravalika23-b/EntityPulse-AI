"""
EntityPulse AI - Full-Stack Web Application Backend
Flask REST API connecting ML Entity Resolution, Knowledge Graph, Batch CSV Engine, and Traceable Decision Engine.
"""

import os
import io
import csv
import json
from flask import Flask, render_template, jsonify, request, Response
from data_manager import get_all_golden_entities, get_golden_entity_by_id, get_hitl_queue
from decision_engine import calculate_executive_kpis, generate_action_recommendations, query_traceable_insights
from er_service import er_service
from batch_processor import batch_processor

app = Flask(__name__)

# State tracking for executed actions and HITL decisions
EXECUTED_ACTIONS = set()
HITL_DECISIONS = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/kpis", methods=["GET"])
def get_kpis():
    kpis = calculate_executive_kpis()
    return jsonify({"status": "success", "data": kpis})

@app.route("/api/entities", methods=["GET"])
def get_entities():
    entities = get_all_golden_entities()
    return jsonify({"status": "success", "data": entities})

@app.route("/api/entities/<golden_id>", methods=["GET"])
def get_entity_detail(golden_id):
    entity = get_golden_entity_by_id(golden_id)
    if entity:
        return jsonify({"status": "success", "data": entity})
    return jsonify({"status": "error", "message": "Entity not found"}), 404

@app.route("/api/actions", methods=["GET"])
def get_actions():
    actions = generate_action_recommendations()
    # Mark executed actions
    for a in actions:
        if a["action_id"] in EXECUTED_ACTIONS:
            a["status"] = "Approved & Executed"
            a["executed"] = True
        else:
            a["executed"] = False
    return jsonify({"status": "success", "data": actions})

@app.route("/api/actions/<action_id>/execute", methods=["POST"])
def execute_action(action_id):
    EXECUTED_ACTIONS.add(action_id)
    return jsonify({
        "status": "success",
        "action_id": action_id,
        "message": f"Action {action_id} successfully approved and queued for ERP execution."
    })

@app.route("/api/query", methods=["POST"])
def process_query():
    body = request.get_json() or {}
    query_text = body.get("query", "").strip()
    if not query_text:
        return jsonify({"status": "error", "message": "Query cannot be empty"}), 400
    
    result = query_traceable_insights(query_text)
    return jsonify({"status": "success", "data": result})

@app.route("/api/hitl", methods=["GET"])
def get_hitl():
    queue = get_hitl_queue()
    # Include existing decisions
    for item in queue:
        item["user_decision"] = HITL_DECISIONS.get(item["review_id"], "Pending")
    return jsonify({"status": "success", "data": queue})

@app.route("/api/hitl/<review_id>/decision", methods=["POST"])
def record_hitl_decision(review_id):
    body = request.get_json() or {}
    decision = body.get("decision", "Approved")
    HITL_DECISIONS[review_id] = decision
    return jsonify({
        "status": "success",
        "review_id": review_id,
        "decision": decision,
        "message": f"Match {review_id} {decision.lower()} by human reviewer."
    })

@app.route("/api/ml/score", methods=["POST"])
def score_pair():
    body = request.get_json() or {}
    s1_name = body.get("s1_name", "").strip()
    s1_addr = body.get("s1_addr", "").strip()
    s2_name = body.get("s2_name", "").strip()
    s2_addr = body.get("s2_addr", "").strip()

    if not s1_name or not s2_name:
        return jsonify({"status": "error", "message": "Business names are required"}), 400

    result = er_service.score_pair(s1_name, s1_addr, s2_name, s2_addr)
    return jsonify({"status": "success", "data": result})

# =========================================================================
# NEW HIGH-IMPACT FEATURES: CSV UPLOAD, BENCHMARK & AUDIT EXPORT
# =========================================================================

@app.route("/api/upload", methods=["POST"])
def upload_csv():
    """
    Accepts CSV file upload up to 10,000+ rows and runs fast entity resolution.
    """
    if "file" in request.files:
        uploaded_file = request.files["file"]
        filename = uploaded_file.filename
        content = uploaded_file.read().decode("utf-8", errors="ignore")
    else:
        body = request.get_json() or {}
        content = body.get("content", "")
        filename = body.get("filename", "custom_input.csv")

    if not content.strip():
        return jsonify({"status": "error", "message": "No CSV content provided"}), 400

    summary = batch_processor.process_csv_stream(content, filename=filename)
    return jsonify({"status": "success", "data": summary})

@app.route("/api/upload/benchmark", methods=["POST"])
def benchmark_batch():
    """
    Generates and processes synthetic enterprise dataset (1,000 or 10,000 rows live).
    """
    body = request.get_json() or {}
    num_records = int(body.get("num_records", 1000))
    # Cap at 20,000 for safety
    num_records = min(max(num_records, 100), 20000)

    csv_data = batch_processor.generate_synthetic_dataset(num_records)
    summary = batch_processor.process_csv_stream(csv_data, filename=f"benchmark_{num_records}_rows.csv")
    return jsonify({"status": "success", "data": summary})

@app.route("/api/export/audit-report", methods=["GET"])
def export_audit_report():
    """
    Exports executive decision audit report as downloadable CSV.
    """
    actions = generate_action_recommendations()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV Header
    writer.writerow([
        "Action_ID", "Priority", "Vendor_Name", "Golden_ID", "Category", 
        "Annual_Spend", "Estimated_ROI", "Impact_Type", "Recommended_Action", 
        "Grounded_Source_Evidence", "Execution_Status"
    ])

    for a in actions:
        status = "Executed in ERP" if a["action_id"] in EXECUTED_ACTIONS else "Pending Approval"
        citations = " | ".join(a.get("grounded_citations", []))
        writer.writerow([
            a.get("action_id", ""),
            a.get("priority", ""),
            a.get("entity_name", ""),
            a.get("entity_id", ""),
            a.get("category", ""),
            f"${a.get('annual_spend', 0):,}",
            a.get("estimated_roi", ""),
            a.get("impact_type", ""),
            a.get("recommended_action", ""),
            citations,
            status
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=EntityPulse_Decision_Audit_Report.csv"}
    )

@app.route("/api/export/resolved-csv", methods=["GET"])
def export_resolved_csv():
    """
    Exports the last batch/uploaded resolved dataset with Golden_Entity_ID.
    """
    if batch_processor.last_resolved_df is None:
        return jsonify({"status": "error", "message": "No batch dataset processed yet"}), 400

    csv_data = batch_processor.last_resolved_df.to_csv(index=False)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=EntityPulse_Resolved_Dataset.csv"}
    )

if __name__ == "__main__":
    print("="*60)
    print("  EntityPulse AI - Decision Engine for Business Data")
    print("  Running on http://127.0.0.1:5000")
    print("="*60)
    app.run(host="127.0.0.1", port=5000, debug=False)
