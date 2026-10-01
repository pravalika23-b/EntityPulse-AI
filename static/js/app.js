/**
 * EntityPulse AI — Frontend Application Logic
 * Problem Statement 4: AI Decision Engine for Business Data
 * Team: Hustle Squad
 */

// State tracking
let allEntities = [];
let samplePlaygroundPairs = [
    {
        s1_name: "Moran Staffing LLC",
        s1_addr: "1902 Shamrock Road, Dothan, AL",
        s2_name: "LLC Moran Staffing",
        s2_addr: "1902 Shamrock Rd, Alabama, Dothan"
    },
    {
        s1_name: "Modern Packaging Inc",
        s1_addr: "742 Evergreen Terrace, Springfield, OR",
        s2_name: "Modern Packaging Incorporated",
        s2_addr: "742 Evergreen Terr, Springfield, Oregon"
    },
    {
        s1_name: "QH Vendome Logistics",
        s1_addr: "88 Industrial Way, Newark, NJ",
        s2_name: "Vendome Q.H. Logistics LLC",
        s2_addr: "88 Ind. Way, Newark, New Jersey"
    }
];

// Switch active tabs
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
    if (activeBtn) activeBtn.classList.add('active');

    const targetContent = document.getElementById(`tab-${tabId}`);
    if (targetContent) targetContent.classList.add('active');
}

// -------------------------------------------------------------
// 1. KPI LOADING
// -------------------------------------------------------------
async function loadKpis() {
    try {
        const res = await fetch('/api/kpis');
        const json = await res.json();
        if (json.status === 'success') {
            const data = json.data;
            document.getElementById('kpi-spend').innerText = `$${Number(data.total_business_spend).toLocaleString()}`;
            document.getElementById('kpi-entities').innerText = Number(data.total_entities).toLocaleString();
            document.getElementById('kpi-savings').innerText = `$${Number(data.total_rate_savings).toLocaleString()} / yr`;
            document.getElementById('kpi-fraud').innerText = `$${Number(data.duplicate_invoice_amount).toLocaleString()}`;
            document.getElementById('kpi-precision').innerText = `${data.model_precision}%`;
        }
    } catch (err) {
        console.error("Error loading KPIs:", err);
    }
}

// -------------------------------------------------------------
// 2. ACTION BOARD LOADING
// -------------------------------------------------------------
async function loadActions() {
    try {
        const res = await fetch('/api/actions');
        const json = await res.json();
        if (json.status === 'success') {
            renderActions(json.data);
        }
    } catch (err) {
        console.error("Error loading actions:", err);
    }
}

function renderActions(actions) {
    const container = document.getElementById('actions-container');
    if (!container) return;

    if (!actions || actions.length === 0) {
        container.innerHTML = '<div class="placeholder-msg">No pending actions. All vendor optimizations executed.</div>';
        return;
    }

    container.innerHTML = actions.map(act => {
        const priorityClass = act.priority.toLowerCase();
        const citationsHtml = act.grounded_citations.map(c => `<span class="citation-pill">${c}</span>`).join('');
        const isExecuted = act.executed;

        return `
            <div class="action-card ${priorityClass}">
                <div class="action-card-header">
                    <span class="action-priority priority-${priorityClass}">${act.priority} PRIORITY</span>
                    <span class="action-savings">${act.estimated_roi}</span>
                </div>
                <h3>${act.title}</h3>
                <div class="action-entity-tag">Entity: <strong>${act.entity_name}</strong> (${act.category})</div>
                <div class="action-rationale">${act.rationale}</div>
                
                <div class="action-citations-box">
                    <div class="citations-title">📌 Underlying Grounded Citations (Source Row IDs)</div>
                    <div>${citationsHtml}</div>
                </div>

                <div class="action-btn-row">
                    <span style="font-size:0.75rem; color:var(--text-muted);">Annual Spend: $${Number(act.annual_spend).toLocaleString()}</span>
                    ${isExecuted ? 
                        `<button class="btn btn-secondary" disabled>✓ Executed in ERP</button>` : 
                        `<button class="btn btn-primary" onclick="executeAction('${act.action_id}')">⚡ Approve & Execute Action</button>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

async function executeAction(actionId) {
    try {
        const res = await fetch(`/api/actions/${actionId}/execute`, { method: 'POST' });
        const json = await res.json();
        if (json.status === 'success') {
            alert(json.message);
            loadActions(); // refresh list
        }
    } catch (err) {
        alert("Error executing action: " + err);
    }
}

// -------------------------------------------------------------
// 3. ENTITY EXPLORER
// -------------------------------------------------------------
async function loadEntities() {
    try {
        const res = await fetch('/api/entities');
        const json = await res.json();
        if (json.status === 'success') {
            allEntities = json.data;
            renderEntityList(allEntities);
            if (allEntities.length > 0) {
                showEntityDetail(allEntities[0].golden_id);
            }
        }
    } catch (err) {
        console.error("Error loading entities:", err);
    }
}

function renderEntityList(entities) {
    const container = document.getElementById('entity-list-container');
    if (!container) return;

    if (!entities || entities.length === 0) {
        container.innerHTML = '<div class="placeholder-msg">No matching entities found.</div>';
        return;
    }

    container.innerHTML = entities.map(e => `
        <div class="entity-list-item" id="item-${e.golden_id}" onclick="showEntityDetail('${e.golden_id}')">
            <div class="item-top">
                <span class="item-name">${e.canonical_name}</span>
                <span class="item-spend">$${Number(e.total_spend).toLocaleString()}</span>
            </div>
            <div class="item-bottom">
                <span>${e.category} · ${e.country}</span>
                <span>${e.linked_source_records.length} Sources Linked</span>
            </div>
        </div>
    `).join('');
}

function filterEntities() {
    const query = document.getElementById('entity-search-input').value.toLowerCase();
    const filtered = allEntities.filter(e => 
        e.canonical_name.toLowerCase().includes(query) ||
        e.category.toLowerCase().includes(query) ||
        e.country.toLowerCase().includes(query) ||
        e.golden_id.toLowerCase().includes(query)
    );
    renderEntityList(filtered);
}

async function showEntityDetail(goldenId) {
    document.querySelectorAll('.entity-list-item').forEach(el => el.classList.remove('selected'));
    const selectedEl = document.getElementById(`item-${goldenId}`);
    if (selectedEl) selectedEl.classList.add('selected');

    const detailContainer = document.getElementById('entity-detail-container');
    try {
        const res = await fetch(`/api/entities/${goldenId}`);
        const json = await res.json();
        if (json.status === 'success') {
            const e = json.data;
            const recordsRows = e.linked_source_records.map(r => `
                <tr>
                    <td><strong style="color:#60A5FA;">${r.source}</strong></td>
                    <td><code>${r.source_id}</code></td>
                    <td>${r.raw_name}</td>
                    <td>${r.raw_address}</td>
                    <td style="color:#34D399; font-weight:600;">$${Number(r.spend).toLocaleString()}</td>
                    <td>$${r.contract_rate.toFixed(2)}/hr</td>
                </tr>
            `).join('');

            const citationsHtml = e.grounded_sources.map(s => `<span class="citation-pill">${s}</span>`).join('');

            detailContainer.innerHTML = `
                <div class="entity-detail-card">
                    <div class="golden-summary-box">
                        <div class="golden-header">
                            <div>
                                <h3 style="font-size:1.3rem; font-weight:800; color:#FFFFFF;">${e.canonical_name}</h3>
                                <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.2rem;">
                                    Authoritative Address: <strong>${e.canonical_address}</strong>
                                </div>
                            </div>
                            <span class="golden-badge">Golden ID: ${e.golden_id}</span>
                        </div>

                        <div class="golden-stats-grid">
                            <div class="stat-box">
                                <div class="stat-label">Total Spend (Consolidated)</div>
                                <div class="stat-value" style="color:#34D399;">$${Number(e.total_spend).toLocaleString()}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Category & Jurisdiction</div>
                                <div class="stat-value">${e.category} (${e.country})</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Multi-Source Lineage</div>
                                <div class="stat-value" style="color:#60A5FA;">${e.linked_source_records.length} Systems Unified</div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <h4 style="font-size:1rem; font-weight:700; margin-bottom:0.75rem;">Source Record Lineage (CRM S1, ERP S2, Procurement S3)</h4>
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Source System</th>
                                    <th>Source Row ID</th>
                                    <th>Ingested Raw Name</th>
                                    <th>Ingested Raw Address</th>
                                    <th>Recorded Spend</th>
                                    <th>Contract Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${recordsRows}
                            </tbody>
                        </table>
                    </div>

                    ${e.anomalies && e.anomalies.length > 0 ? `
                        <div style="background:rgba(244,63,94,0.1); border:1px solid rgba(244,63,94,0.3); border-radius:var(--radius-md); padding:1rem;">
                            <h4 style="font-size:0.95rem; color:#FB7185; margin-bottom:0.4rem;">🚨 Active Anomalies Detected</h4>
                            <ul style="padding-left:1.2rem; font-size:0.85rem; color:#FCA5A5;">
                                ${e.anomalies.map(a => `<li>${a.description} (${a.type})</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}

                    <div class="action-citations-box">
                        <div class="citations-title">🔒 Ground Truth Source Row Provenance</div>
                        <div>${citationsHtml}</div>
                    </div>
                </div>
            `;
        }
    } catch (err) {
        detailContainer.innerHTML = `<div class="placeholder-msg">Error loading entity detail: ${err}</div>`;
    }
}

// -------------------------------------------------------------
// 4. LIVE ML MODEL PLAYGROUND
// -------------------------------------------------------------
function loadPlaygroundSample(index) {
    const pair = samplePlaygroundPairs[index];
    if (!pair) return;
    document.getElementById('pg-s1-name').value = pair.s1_name;
    document.getElementById('pg-s1-addr').value = pair.s1_addr;
    document.getElementById('pg-s2-name').value = pair.s2_name;
    document.getElementById('pg-s2-addr').value = pair.s2_addr;
    scorePlaygroundPair();
}

async function scorePlaygroundPair() {
    const s1_name = document.getElementById('pg-s1-name').value.trim();
    const s1_addr = document.getElementById('pg-s1-addr').value.trim();
    const s2_name = document.getElementById('pg-s2-name').value.trim();
    const s2_addr = document.getElementById('pg-s2-addr').value.trim();
    const container = document.getElementById('playground-results-container');

    container.innerHTML = '<div class="placeholder-msg">Running feature extraction & LightGBM inference...</div>';

    try {
        const res = await fetch('/api/ml/score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ s1_name, s1_addr, s2_name, s2_addr })
        });
        const json = await res.json();
        if (json.status === 'success') {
            const d = json.data;
            const probPct = (d.probability * 100).toFixed(1);
            const isMatch = d.is_match;

            const featuresHtml = Object.entries(d.features).map(([name, val]) => {
                const normVal = Math.min(Math.max(val, 0), 1);
                const pct = (normVal * 100).toFixed(0);
                return `
                    <div class="feature-bar-box">
                        <div class="feature-bar-top">
                            <span>${name}</span>
                            <span>${val.toFixed(3)}</span>
                        </div>
                        <div class="progress-track">
                            <div class="progress-fill" style="width: ${pct}%;"></div>
                        </div>
                    </div>
                `;
            }).join('');

            container.innerHTML = `
                <div class="score-banner">
                    <div>
                        <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">LightGBM Model Confidence</div>
                        <div class="score-num ${isMatch ? 'match' : 'nomatch'}">${probPct}%</div>
                    </div>
                    <div>
                        <span class="decision-badge ${isMatch ? 'priority-high' : 'priority-critical'}" style="background:${isMatch ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}; color:${isMatch ? '#34D399' : '#FB7185'}; border:1px solid ${isMatch ? 'rgba(16,185,129,0.4)' : 'rgba(244,63,94,0.4)'};">
                            ${isMatch ? '✓ AUTHORITATIVE MATCH' : '✕ NON-MATCHING PAIR'}
                        </span>
                        <div style="font-size:0.72rem; color:var(--text-muted); margin-top:0.3rem; text-align:right;">Threshold: τ = ${d.threshold}</div>
                    </div>
                </div>

                <div style="font-size:0.85rem; font-weight:700; color:#FFFFFF; margin-bottom:0.75rem;">
                    Extracted RapidFuzz Linguistic & Spatial Features (13 Dimensions):
                </div>
                <div class="features-grid">
                    ${featuresHtml}
                </div>
            `;
        } else {
            container.innerHTML = `<div class="placeholder-msg">Error: ${json.message}</div>`;
        }
    } catch (err) {
        container.innerHTML = `<div class="placeholder-msg">Error running ML scoring: ${err}</div>`;
    }
}

// -------------------------------------------------------------
// 5. TRACEABLE AI ASSISTANT
// -------------------------------------------------------------
function sendQuickQuery(text) {
    document.getElementById('chat-input').value = text;
    sendChatQuery();
}

async function sendChatQuery() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;

    const chatMessages = document.getElementById('chat-messages');

    // Add user bubble
    chatMessages.innerHTML += `
        <div class="chat-bubble user">
            ${escapeHtml(query)}
        </div>
    `;
    input.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Loading indicator
    const tempId = `temp-${Date.now()}`;
    chatMessages.innerHTML += `
        <div class="chat-bubble ai" id="${tempId}">
            <em>Querying Golden Knowledge Graph and verifying row citations...</em>
        </div>
    `;
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const res = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const json = await res.json();
        const tempBubble = document.getElementById(tempId);

        if (json.status === 'success') {
            const data = json.data;
            const citationsTags = (data.grounded_citations || []).map(c => `<span class="chat-citation-tag">${c}</span>`).join('');
            
            // Format answer with bolding
            const formattedAnswer = data.answer.replace(/\n/g, '<br>');

            tempBubble.innerHTML = `
                <div>${formattedAnswer}</div>
                ${citationsTags ? `
                    <div style="margin-top:0.75rem; padding-top:0.5rem; border-top:1px solid rgba(255,255,255,0.08);">
                        <span style="font-size:0.72rem; color:var(--text-muted); font-weight:700;">VERIFIED CITATIONS:</span>
                        <div>${citationsTags}</div>
                    </div>
                ` : ''}
            `;
        } else {
            tempBubble.innerHTML = `<strong>Error:</strong> ${json.message}`;
        }
    } catch (err) {
        const tempBubble = document.getElementById(tempId);
        if (tempBubble) tempBubble.innerHTML = `<strong>Network Error:</strong> ${err}`;
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// -------------------------------------------------------------
// 6. HUMAN-IN-THE-LOOP (HITL) QUEUE
// -------------------------------------------------------------
async function loadHitl() {
    try {
        const res = await fetch('/api/hitl');
        const json = await res.json();
        if (json.status === 'success') {
            renderHitl(json.data);
        }
    } catch (err) {
        console.error("Error loading HITL queue:", err);
    }
}

function renderHitl(queue) {
    const container = document.getElementById('hitl-container');
    if (!container) return;

    if (!queue || queue.length === 0) {
        container.innerHTML = '<div class="placeholder-msg">HITL queue is empty. All boundary matches reviewed.</div>';
        return;
    }

    container.innerHTML = queue.map(item => {
        const isDecided = item.user_decision !== 'Pending';
        return `
            <div class="hitl-card" id="hitl-${item.review_id}">
                <div class="hitl-top">
                    <div>
                        <strong style="color:#FFFFFF; font-size:1rem;">Case ${item.review_id}</strong>
                        <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.15rem;">Reason: ${item.variance_reason}</div>
                    </div>
                    <span class="hitl-score-badge">Model Conf: ${(item.model_probability * 100).toFixed(1)}%</span>
                </div>

                <div class="hitl-comparison">
                    <div class="hitl-item">
                        <h5>Record A (${item.entity_candidate_1.source})</h5>
                        <div class="hitl-item-name">${item.entity_candidate_1.name}</div>
                        <div class="hitl-item-addr">${item.entity_candidate_1.address}</div>
                        <div class="hitl-item-spend">Spend: $${Number(item.entity_candidate_1.spend).toLocaleString()}</div>
                    </div>
                    <div class="hitl-item">
                        <h5>Record B (${item.entity_candidate_2.source})</h5>
                        <div class="hitl-item-name">${item.entity_candidate_2.name}</div>
                        <div class="hitl-item-addr">${item.entity_candidate_2.address}</div>
                        <div class="hitl-item-spend">Spend: $${Number(item.entity_candidate_2.spend).toLocaleString()}</div>
                    </div>
                </div>

                <div class="hitl-actions-row">
                    ${isDecided ? `
                        <span style="font-size:0.85rem; font-weight:700; color:${item.user_decision === 'Approved' ? '#34D399' : '#FB7185'};">
                            Decision Recorded: ${item.user_decision}
                        </span>
                    ` : `
                        <button class="btn btn-secondary" onclick="submitHitlDecision('${item.review_id}', 'Rejected')">✕ Reject Link</button>
                        <button class="btn btn-success" onclick="submitHitlDecision('${item.review_id}', 'Approved')">✓ Confirm Match</button>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

async function submitHitlDecision(reviewId, decision) {
    try {
        const res = await fetch(`/api/hitl/${reviewId}/decision`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision })
        });
        const json = await res.json();
        if (json.status === 'success') {
            alert(json.message);
            loadHitl();
        }
    } catch (err) {
        alert("Error submitting decision: " + err);
    }
}

// Utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}

// -------------------------------------------------------------
// 7. BATCH UPLOAD & SCALE BENCHMARK (UP TO 10,000+ ROWS)
// -------------------------------------------------------------
async function runBenchmark(numRecords) {
    const pane = document.getElementById('upload-results-pane');
    const btn1k = document.getElementById('btn-bench-1k');
    const btn10k = document.getElementById('btn-bench-10k');

    if (btn1k) btn1k.disabled = true;
    if (btn10k) btn10k.disabled = true;

    pane.innerHTML = `
        <div class="placeholder-msg">
            <div>
                <div style="font-size:1.8rem; margin-bottom:0.75rem;">⚡</div>
                <strong>Processing ${numRecords.toLocaleString()} Enterprise Records...</strong>
                <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.3rem;">
                    Executing Tiered Blocking + RapidFuzz Token Clustering...
                </div>
            </div>
        </div>
    `;

    try {
        const res = await fetch('/api/upload/benchmark', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ num_records: numRecords })
        });
        const json = await res.json();
        if (json.status === 'success') {
            renderUploadResults(json.data);
        } else {
            pane.innerHTML = `<div class="placeholder-msg">Error: ${json.message}</div>`;
        }
    } catch (err) {
        pane.innerHTML = `<div class="placeholder-msg">Network error: ${err}</div>`;
    } finally {
        if (btn1k) btn1k.disabled = false;
        if (btn10k) btn10k.disabled = false;
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const pane = document.getElementById('upload-results-pane');
    pane.innerHTML = `
        <div class="placeholder-msg">
            <div>
                <div style="font-size:1.8rem; margin-bottom:0.75rem;">📂</div>
                <strong>Ingesting & Resolving "${file.name}"...</strong>
                <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.3rem;">
                    Parsing columns and clustering entities...
                </div>
            </div>
        </div>
    `;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const json = await res.json();
        if (json.status === 'success') {
            renderUploadResults(json.data);
        } else {
            pane.innerHTML = `<div class="placeholder-msg">Error: ${json.message}</div>`;
        }
    } catch (err) {
        pane.innerHTML = `<div class="placeholder-msg">Error uploading file: ${err}</div>`;
    }
}

function renderUploadResults(data) {
    const pane = document.getElementById('upload-results-pane');
    if (!pane) return;

    const rowsHtml = (data.top_clusters || []).map(c => `
        <tr>
            <td><strong style="color:#60A5FA;">${c.golden_id}</strong></td>
            <td><strong>${c.canonical_name}</strong></td>
            <td style="color:var(--text-secondary); font-size:0.78rem;">${(c.variants || []).slice(0, 2).join(' · ') || 'Exact Matches'}</td>
            <td><span class="badge badge-model">${c.records_merged} records</span></td>
            <td style="color:#34D399; font-weight:700;">$${Number(c.estimated_savings).toLocaleString()}</td>
        </tr>
    `).join('');

    pane.innerHTML = `
        <div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
                <div>
                    <h3 style="font-size:1.15rem; color:#FFFFFF;">Resolution Complete: ${data.filename}</h3>
                    <div style="font-size:0.8rem; color:var(--text-secondary);">
                        Processed in <strong>${data.processing_time_seconds}s</strong> (${data.throughput_records_per_sec.toLocaleString()} rows/sec throughput)
                    </div>
                </div>
                <a href="/api/export/resolved-csv" class="btn btn-primary" download style="font-size:0.8rem;">
                    📥 Download Cleaned & Resolved CSV
                </a>
            </div>

            <div class="bench-stats-grid">
                <div class="bench-stat-card">
                    <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Records Processed</div>
                    <div class="bench-stat-val">${data.total_records_processed.toLocaleString()}</div>
                </div>
                <div class="bench-stat-card">
                    <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Golden Entities Created</div>
                    <div class="bench-stat-val" style="color:#60A5FA;">${data.unique_golden_entities.toLocaleString()}</div>
                </div>
                <div class="bench-stat-card">
                    <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Identified Savings</div>
                    <div class="bench-stat-val" style="color:#34D399;">$${Number(data.estimated_consolidation_savings).toLocaleString()}</div>
                </div>
            </div>

            <h4 style="font-size:0.9rem; font-weight:700; margin-bottom:0.6rem; color:#FFFFFF;">
                Top Resolved Vendor Duplicate Clusters (Found ${data.duplicate_clusters_found} clusters):
            </h4>
            <div style="max-height:280px; overflow-y:auto; border:1px solid var(--border-color); border-radius:var(--radius-sm);">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Golden ID</th>
                            <th>Canonical Name</th>
                            <th>Resolved Alias Variants</th>
                            <th>Cluster Size</th>
                            <th>Estimated Savings</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml || '<tr><td colspan="5" style="text-align:center;">All unique singletons. No duplicates found.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// -------------------------------------------------------------
// INITIALIZATION ON PAGE LOAD
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    loadKpis();
    loadActions();
    loadEntities();
    loadHitl();
    scorePlaygroundPair(); // run initial scoring for default sample
});
