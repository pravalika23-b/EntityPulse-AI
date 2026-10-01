# ⚡ EntityPulse AI: Zero-Hallucination Enterprise Decision Engine
**Track 04:** AI Decision Engine for Business Data  
**Team Name:** Hustle Squad  

---

## 📌 Problem Overview & Solution
Modern enterprises lose millions annually due to fragmented vendor records across CRM, ERP, and procurement systems. Because names and addresses contain spelling errors, abbreviations, and DBAs, organizations inadvertently issue **duplicate invoice payments** and negotiate **conflicting contract rates** with the same suppliers.

**EntityPulse AI** solves this through an end-to-end 4-step architecture:
1. **INPUT**: Ingestion of multi-source messy records (Reference CRM, Legacy ERP, Field Procurement).
2. **PROCESS**: High-precision machine learning entity resolution using tiered blocking, 13 RapidFuzz spatial/linguistic features, and a competition-trained **LightGBM Classifier** ($\tau = 0.85$, $89.65\%$ precision, $93.5\%$ singleton accuracy).
3. **OUTPUT**: Unified Golden Knowledge Graph with **100% row-level provenance** and zero hallucinations.
4. **PROBLEM SOLVED**: Autonomous anomaly detection identifying over **$725,000 in rate savings** and **$42,000 in duplicate invoices**, with one-click ERP execution.

---

## 🚀 Quickstart & Local Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/entitypulse-ai.git
cd entitypulse-ai/entitypulse_app
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests (13/13 Passing)
```bash
python test_app.py
```

### 4. Launch the Web Application
```bash
python run_app.py
```
Open your browser to: **`http://127.0.0.1:5000`**

---

## ⚡ High-Scale Batch Benchmark Performance
* **1,000 Records**: Resolved in **0.21 seconds** (4,760 records/sec).
* **10,000 Records**: Resolved in **0.73 seconds** (13,690 records/sec).
* Capable of live CSV upload with instant downloadable resolved clusters.

---

## 🤖 Mandatory Disclosure of AI Tools Used
In accordance with hackathon submission guidelines:
* **Machine Learning Algorithms**: LightGBM GBDT (MIT License, parameter budget $<100\text{k} \ll 8\text{B}$), RapidFuzz (MIT License).
* **Development & Pair-Programming Assistance**: Google Antigravity / Gemini 2.5 Coding Assistant used for code scaffolding, refactoring, and test suite design.
* **All models, training datasets, and inference logic are 100% original, open-source, and verifiable.**
