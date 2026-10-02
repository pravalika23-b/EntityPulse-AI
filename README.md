# ⚡ EntityPulse AI — Decision Engine for Business Data
> **BFWAI / HACK 26 Hackathon • Problem Statement 04 (AI Decision Engine for Business Data)**  
> **Team:** Hustle Squad  
> **Live Demo:** [https://entitypulse-ai.onrender.com/](https://entitypulse-ai.onrender.com/)

---

## 🏢 1. The Real-World Problem We Are Solving

In enterprise organizations, business data is trapped in separate software systems:
* **System 1 (CRM)**: used by sales and management.
* **System 2 (ERP)**: used by accounting and operations.
* **System 3 (Procurement)**: used by purchasing and warehouses.

Because humans enter company names with typos, abbreviations, or different legal forms (e.g., `Moran Staffing LLC` vs `LLC Moran Staffing` vs `Moran Staffing Incorporated`), standard databases treat them as **completely different vendors**.

### 💸 Why This Costs Companies Millions:
1. **Duplicate Invoices:** A vendor bills Department A for $42,000 and bills Department B for the exact same $42,000. Both departments pay it because neither realizes it is the same vendor.
2. **Conflicting Contract Rates:** Department A negotiates a master rate of **$65/hr**, while Department B pays **$82.50/hr** to the same vendor. The company overpays hundreds of thousands of dollars annually.
3. **LLM Hallucinations:** Feeding millions of messy, duplicate rows directly into ChatGPT or general LLMs results in made-up numbers and ungrounded answers.

---

## 🚀 2. How EntityPulse AI Works (The 4-Step Architecture)

```
[1. INPUT] ──▶ [2. PROCESS] ──▶ [3. PROCESS & KG] ──▶ [4. DECISION ENGINE]
Multi-Source      Tiered Blocking       Golden Knowledge       Quantified Actions,
Messy Ingestion   + 13-Dim LightGBM     Graph with Lineage     Audit CSV & Chat
```

1. **INPUT (Multi-Source Data)**: Ingests messy, fragmented vendor data from CRM (`S1`), Legacy ERP (`S2`), and Field Procurement (`S3`).
2. **PROCESS (Machine Learning)**: Uses our trained **LightGBM Classifier** + **RapidFuzz** (13 spatial & linguistic features) with smart **tiered blocking** to match duplicate companies with **89.65% precision** in milliseconds.
3. **OUTPUT (Traceable Golden Graph)**: Merges records into a clean master directory with **zero hallucinations**—every single metric cites the exact raw database row IDs (`[S1-...]`, `[S2-...]`, `[S3-...]`).
4. **PROBLEM SOLVED (Actionable Decisions)**: Autonomously flags duplicate billing fraud and contract rate disparities, unlocking **over $725,000 in direct savings**.

---

## 🌟 3. Detailed Feature Breakdown: What Each Feature Does & How It Helps

### 💡 1. Actionable Decision Board & 1-Click Execution
* **What it does:** Scans the unified data and generates prioritized **Action Cards** (Critical, High, Medium) with quantified dollar ROI.
* **How it is helpful:** Executives don't have to read through spreadsheets. They see clear financial actions (e.g., *"Halt duplicate payment of $42,000 for Invoice INV-9988"* or *"Harmonize Moran Staffing rates to save $69,125/yr"*) and can click **"Approve & Execute"** to immediately queue the change.

### 📥 2. High-Scale Batch Processing & CSV Ingestion
* **What it does:** Drag-and-drop any CSV file with messy business records up to 10,000+ rows, or click the **1,000 / 10,000 row live benchmark** button.
* **How it is helpful:** Processes over **13,700 records per second** in memory using tiered blocking and RapidFuzz C++ vectorization. Instantly returns processing throughput and lets users download the deduplicated dataset with new `Golden_Entity_ID` columns.

### 📋 3. Executive Decision Audit Report Export
* **What it does:** Generates a complete, compliance-ready CSV report containing every recommended decision, financial priority, estimated ROI, and raw database row citations.
* **How it is helpful:** Provides financial auditors and executives with transparent, verifiable proof before enacting major procurement changes or halting payments.

### 🌐 4. Unified Golden Knowledge Graph Directory
* **What it does:** Displays the authoritative Master Entity profile for each company, showing which records from CRM, ERP, and Procurement were unified together.
* **How it is helpful:** Eliminates guesswork. Clicking any vendor shows their consolidated spend, all historical addresses, and exact source system provenance.

### 🧪 5. Live Machine Learning Model Playground
* **What it does:** Provides an interactive sandbox where users can type any two messy company names and addresses to test the ML model in real time.
* **How it is helpful:** Instantly displays the match probability (e.g., 99.9% Match) and visualizes the breakdown of all **13 RapidFuzz linguistic and spatial feature scores** (token ratio, address match, word inversion, etc.).

### 🤖 6. Traceable AI Assistant (Zero Hallucination)
* **What it does:** A natural language assistant that answers business questions such as: *"Where are we paying duplicate bills?"* or *"Which vendors have contract pricing discrepancies?"*.
* **How it is helpful:** Unlike generic LLMs that guess, every answer is strictly grounded in the Golden Graph with clickable citations linking back to the exact source row ID.

### 🛡️ 7. Human-in-the-Loop (HITL) Governance Queue
* **What it does:** Routes borderline match predictions (confidence between **65% and 85%**) to a dedicated review screen for human sign-off with **Confirm Match** and **Reject Link** buttons.
* **How it is helpful:** Protects the company from making mistakes. High-confidence pairs merge automatically, while ambiguous cases are reviewed safely by a human.

---

## 📊 4. Performance & ML Metrics

| Metric | Result | Meaning / Impact |
| :--- | :---: | :--- |
| **Model Match Precision** | **89.65%** | Minimizes false merges, ensuring distinct companies aren't wrongly combined. |
| **Singleton Accuracy** | **93.5%** | Correctly identifies unique standalone companies without hallucinating links. |
| **Optimal Threshold** | **$\tau = 0.85$** | Statistically validated decision boundary on 346,000 ground truth pairs. |
| **10,000-Row Throughput** | **0.61 seconds** | Over **16,000 rows/second** processed via RapidFuzz and C++ vectorization. |
| **Automated Test Coverage** | **13 / 13 (100%)** | Every API endpoint, ML model scoring, and export function verified. |

---

## 🛠️ 5. Technology Stack

* **Machine Learning & Core:** LightGBM (Gradient Boosted Trees), RapidFuzz, Pandas, NumPy, Scikit-Learn.
* **Backend:** Python 3.13, Flask (RESTful Architecture), Gunicorn WSGI server.
* **Frontend:** Modern HTML5, Responsive CSS3 (Custom Dark Theme), Vanilla JavaScript (Zero external heavy frameworks).
* **Cloud & Deployment:** Render.com / Gunicorn container ready with `Procfile` and `requirements.txt`.

---

## 💻 6. Quickstart: How to Run Locally

### 1. Clone the Repository
```bash
git clone https://github.com/<YOUR_USERNAME>/entitypulse-ai.git
cd entitypulse-ai/entitypulse_app
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Verification Tests
```bash
python test_app.py
```
*(Confirms that all 13 backend, ML scoring, and benchmark tests pass 100%).*

### 4. Start the Application
```bash
python run_app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🤖 7. Disclosure of AI Tools Used

In accordance with hackathon submission guidelines:
* **Machine Learning Algorithms**: LightGBM GBDT (MIT License, parameter budget $<100\text{k} \ll 8\text{B}$ parameter limit), RapidFuzz (MIT License).
* **Development & Pair-Programming Assistance**: Google Antigravity / Gemini 2.5 Coding Assistant was used for boilerplate scaffolding, CSS refinement, and test suite design.
* **All models, training datasets, and inference logic are 100% original, open-source, and verifiable.**

---

## 👥 Team: Hustle Squad
* **Track:** AI Decision Engine for Business Data (Problem Statement 04)  
* **Event:** BFWAI / HACK 26 Hackathon  