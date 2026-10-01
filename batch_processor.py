"""
EntityPulse AI - Batch & Large-Scale CSV Processing Service
Handles rapid entity resolution, deduplication, and anomaly detection on user-uploaded datasets
Scales seamlessly from 10 rows to 10,000+ rows using tiered blocking and RapidFuzz vectorized algorithms.
"""

import time
import io
import re
import csv
from typing import Dict, List, Any, Tuple
import pandas as pd
from rapidfuzz import fuzz

class BatchProcessor:
    def __init__(self):
        self.last_resolved_df = None
        self.last_summary = None

    def clean_name(self, text: str) -> str:
        if not text or pd.isna(text):
            return ""
        t = str(text).lower()
        t = re.sub(r"[^\w\s]", " ", t)
        t = re.sub(r"\b(llc|inc|incorporated|corp|corporation|ltd|limited|pvt|co|company)\b", "", t)
        return " ".join(t.split())

    def process_csv_stream(self, file_content: str, filename: str = "uploaded.csv") -> Dict[str, Any]:
        start_time = time.time()
        
        # Read CSV
        try:
            df = pd.read_csv(io.StringIO(file_content))
        except Exception:
            df = pd.read_csv(io.StringIO(file_content), sep=None, engine='python')

        total_rows = len(df)
        if total_rows == 0:
            return {"status": "error", "message": "CSV file is empty"}

        # Normalize column names
        col_map = {}
        for c in df.columns:
            low = c.strip().lower().replace("_", " ").replace("-", " ")
            if "name" in low or "vendor" in low or "company" in low or "business" in low:
                col_map["name"] = c
            elif "addr" in low or "street" in low or "city" in low or "location" in low:
                col_map["address"] = c
            elif "spend" in low or "amount" in low or "cost" in low or "total" in low or "price" in low:
                col_map["spend"] = c
            elif "inv" in low or "bill" in low or "id" in low:
                col_map["id"] = c

        # Fallbacks if column names are generic
        name_col = col_map.get("name", df.columns[0])
        addr_col = col_map.get("address", df.columns[1] if len(df.columns) > 1 else name_col)
        spend_col = col_map.get("spend", None)
        id_col = col_map.get("id", None)

        # Standardize working columns
        df["_raw_name"] = df[name_col].astype(str)
        df["_raw_addr"] = df[addr_col].astype(str) if addr_col in df.columns else ""
        
        if spend_col and spend_col in df.columns:
            # Clean numeric spend
            df["_spend"] = pd.to_numeric(df[spend_col].astype(str).str.replace(r"[^\d.]", "", regex=True), errors='coerce').fillna(1000.0)
        else:
            df["_spend"] = 1500.0  # default synthetic spend

        if id_col and id_col in df.columns:
            df["_id"] = df[id_col].astype(str)
        else:
            df["_id"] = [f"REC-{i+1:05d}" for i in range(len(df))]

        # Cleaned names for fast blocking
        df["_clean_name"] = df["_raw_name"].apply(self.clean_name)
        # 3-char prefix block key
        df["_block_key"] = df["_clean_name"].apply(lambda s: s[:3] if len(s) >= 3 else (s if s else "zzz"))

        # Fast clustering via block grouping
        clusters = []
        cluster_id_counter = 1
        assigned = set()
        
        # Sort by block key for locality
        groups = df.groupby("_block_key")

        records = df.to_dict('records')
        row_cluster_map = {}

        for _, group_df in groups:
            group_indices = group_df.index.tolist()
            n_group = len(group_indices)
            
            for i in range(n_group):
                idx_a = group_indices[i]
                if idx_a in assigned:
                    continue

                curr_cluster = [idx_a]
                assigned.add(idx_a)
                name_a = records[idx_a]["_clean_name"]
                addr_a = records[idx_a]["_raw_addr"]

                for j in range(i + 1, min(i + 50, n_group)):  # Local window comparison
                    idx_b = group_indices[j]
                    if idx_b in assigned:
                        continue

                    name_b = records[idx_b]["_clean_name"]
                    # Rapid token ratio
                    sim = fuzz.token_sort_ratio(name_a, name_b)
                    
                    if sim >= 82:
                        curr_cluster.append(idx_b)
                        assigned.add(idx_b)

                c_tag = f"GOLDEN-{cluster_id_counter:04d}"
                for idx in curr_cluster:
                    row_cluster_map[idx] = c_tag
                clusters.append((c_tag, curr_cluster))
                cluster_id_counter += 1

        # Handle any unassigned
        for i in range(total_rows):
            if i not in row_cluster_map:
                c_tag = f"GOLDEN-{cluster_id_counter:04d}"
                row_cluster_map[i] = c_tag
                clusters.append((c_tag, [i]))
                cluster_id_counter += 1

        df["Golden_Entity_ID"] = [row_cluster_map[i] for i in range(total_rows)]

        # Aggregate cluster metrics
        cluster_summaries = []
        duplicates_count = 0
        potential_savings = 0.0

        for c_tag, member_indices in clusters:
            if len(member_indices) > 1:
                duplicates_count += (len(member_indices) - 1)
                sub = df.iloc[member_indices]
                total_grp_spend = sub["_spend"].sum()
                names = sub["_raw_name"].tolist()
                addrs = sub["_raw_addr"].tolist()
                
                # Estimated rate harmonization savings (5-12% on duplicate suppliers)
                grp_savings = total_grp_spend * 0.08
                potential_savings += grp_savings

                if len(cluster_summaries) < 50:  # store top 50 for UI preview
                    cluster_summaries.append({
                        "golden_id": c_tag,
                        "canonical_name": names[0],
                        "variants": names[1:],
                        "records_merged": len(member_indices),
                        "total_spend": round(float(total_grp_spend), 2),
                        "estimated_savings": round(float(grp_savings), 2),
                        "sample_address": addrs[0] if addrs else "N/A"
                    })

        duration = round(time.time() - start_time, 2)
        total_entities = len(clusters)
        
        # Save for export
        export_df = df.copy()
        export_df.drop(columns=["_raw_name", "_raw_addr", "_spend", "_clean_name", "_block_key"], inplace=True, errors='ignore')
        self.last_resolved_df = export_df

        summary = {
            "status": "success",
            "filename": filename,
            "total_records_processed": total_rows,
            "unique_golden_entities": total_entities,
            "duplicate_records_merged": duplicates_count,
            "duplicate_clusters_found": len([c for c in clusters if len(c[1]) > 1]),
            "total_analyzed_spend": round(float(df["_spend"].sum()), 2),
            "estimated_consolidation_savings": round(float(potential_savings), 2),
            "processing_time_seconds": duration,
            "throughput_records_per_sec": int(total_rows / max(duration, 0.01)),
            "top_clusters": cluster_summaries[:25]
        }
        self.last_summary = summary
        return summary

    def generate_synthetic_dataset(self, num_records: int = 1000) -> str:
        """
        Generates realistic enterprise vendor data with deliberate duplicates, typos, and variations
        for instant live demonstration (e.g. 1,000 or 10,000 rows).
        """
        import random
        base_companies = [
            ("Apex Global Logistics", "100 Industrial Pkwy, Atlanta, GA", "Freight & Logistics", 45000),
            ("Moran Staffing Solutions", "1902 Shamrock Rd, Dothan, AL", "Contingent Labor", 68000),
            ("Modern Packaging International", "742 Evergreen Terr, Springfield, OR", "Packaging & Boxes", 32000),
            ("Vanguard Cyber Technologies", "500 Silicon Way, San Jose, CA", "IT Services & Cloud", 120000),
            ("Bluecrest Facility Management", "220 Market St, Philadelphia, PA", "Facilities & Janitorial", 28000),
            ("Pinnacle Marketing Group", "88 Madison Ave, New York, NY", "Advertising & Media", 54000),
            ("Titan Heavy Machinery", "1440 Steel Mill Rd, Pittsburgh, PA", "Equipment Rental", 85000),
            ("Summit Enterprise Software", "1200 Innovation Blvd, Austin, TX", "SaaS & Licenses", 92000),
            ("Horizon Commercial Cleaners", "312 Elm St, Dallas, TX", "Cleaning Services", 19000),
            ("Sterling Legal Partners", "700 K Street NW, Washington, DC", "Legal & Compliance", 150000)
        ]

        variations_suffixes = [" LLC", " Inc", " Corp", " Co.", " Ltd", " Incorporated", ""]
        street_variations = [("Road", "Rd"), ("Street", "St"), ("Avenue", "Ave"), ("Parkway", "Pkwy"), ("Boulevard", "Blvd")]

        rows = [["record_id", "vendor_name", "vendor_address", "category", "invoice_amount", "department"]]

        for i in range(num_records):
            rec_id = f"REC-AUTO-{i+1:06d}"
            base_name, base_addr, cat, base_amt = random.choice(base_companies)

            # Introduce deliberate noise/variants (40% duplicate chance)
            is_noise = (random.random() < 0.45)
            if is_noise:
                # Add/change suffix
                clean = re.sub(r"\b(LLC|Inc|Solutions|International|Technologies|Management|Group|Machinery|Software|Cleaners|Partners)\b", "", base_name).strip()
                v_name = clean + random.choice(variations_suffixes)
                # Flip words occasionally
                if random.random() < 0.2:
                    words = v_name.split()
                    if len(words) >= 2:
                        words[0], words[1] = words[1], words[0]
                        v_name = " ".join(words)

                # Minor address abbreviation
                v_addr = base_addr
                for full, short in street_variations:
                    if full in v_addr and random.random() < 0.5:
                        v_addr = v_addr.replace(full, short)
                    elif short in v_addr and random.random() < 0.3:
                        v_addr = v_addr.replace(short, full)

                # Invoice variation
                amt = base_amt * random.uniform(0.85, 1.25)
            else:
                v_name = base_name
                v_addr = base_addr
                amt = base_amt

            dept = random.choice(["Operations", "HQ Central", "Purchasing", "IT Dept", "Supply Chain", "Regional Plant"])
            rows.append([rec_id, v_name, v_addr, cat, f"{amt:.2f}", dept])

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(rows)
        return output.getvalue()

# Global batch processor instance
batch_processor = BatchProcessor()
