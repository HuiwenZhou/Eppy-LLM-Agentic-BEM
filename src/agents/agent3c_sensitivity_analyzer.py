"""
Eppy-LLM: Natural-Language-Driven Building Energy Modeling
===========================================================

Module: quant_sensitivity_tool.py
Agent 3c – Quantitative Sensitivity Analyzer
--------------------------------------------
Performs quantitative sensitivity analysis on EnergyPlus simulation results
generated from multiple modified IDF runs (by Agent 2). It computes
metric-wise relative change (%) with respect to the baseline simulation.

Outputs:
    • sensitivity_table.csv — normalized Δ% per metric
    • sensitivity_summary.json — top-N ranked sensitivity metrics

Author: Huiwen Zhou  
Maintainer: @huiwenzhou  
"""

import os
import json
import datetime
from io import StringIO
from typing import Optional, List, Dict
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_files")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
SIM_DIR = os.path.join(OUTPUTS_DIR, "simulations")
RESULTS_DIR = os.path.join(OUTPUTS_DIR, "results")

# ------------------------------------------------------------
# Environment setup
# ------------------------------------------------------------
dotenv_path = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(dotenv_path)

COOLING_KEYWORD = "Zone Sensible Cooling"
HEATING_KEYWORD = "Zone Sensible Heating"


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------
def read_text_safely(path: str) -> str:
    for enc in ["utf-8-sig", "cp1252", "latin1"]:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception:
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def to_number(x) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(",", "")
    for bad in ["°", "Â", "\u00b0"]:
        s = s.replace(bad, "")
    try:
        return float(s)
    except Exception:
        return None


# ------------------------------------------------------------
# CSV parsing: tolerant version
# ------------------------------------------------------------
def extract_table_total(csv_path: str, keyword: str) -> Optional[float]:
    text = read_text_safely(csv_path)
    lines = text.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower():
            start_idx = i
            break
    if start_idx is None:
        return None

    data_lines: List[str] = []
    header_found = False
    for j in range(start_idx + 1, len(lines)):
        line = lines[j]
        if not header_found:
            if len(line.strip()) == 0:
                continue
            if "calculated" in line.lower() and "design" in line.lower():
                header_found = True
                data_lines.append(line)
            continue
        if line.strip() == "" or line.lower().startswith("zone "):
            break
        data_lines.append(line)

    if not data_lines:
        return None

    try:
        df = pd.read_csv(StringIO("\n".join(data_lines)), header=0, engine="python", on_bad_lines="skip")
    except Exception:
        return None

    candidates = [c for c in df.columns if "calculated" in str(c).lower() and "design" in str(c).lower()]
    if not candidates:
        return None

    col = candidates[0]
    values = df[col].apply(to_number).dropna()
    if values.empty:
        return None

    return float(values.sum())


def get_zone_totals(folder: str) -> Dict[str, Optional[float]]:
    csv_path = os.path.join(folder, "eplustbl.csv")
    if not os.path.exists(csv_path):
        return {"cooling": None, "heating": None}
    cooling = extract_table_total(csv_path, COOLING_KEYWORD)
    heating = extract_table_total(csv_path, HEATING_KEYWORD)
    return {"cooling": cooling, "heating": heating}


# ------------------------------------------------------------
# Main analysis
# ------------------------------------------------------------
def analyze_all(base_dir: str, results_dir: str) -> Dict:
    os.makedirs(results_dir, exist_ok=True)
    baseline_folder = os.path.join(base_dir, "baseline_run_latest")
    if not os.path.isdir(baseline_folder):
        raise FileNotFoundError("Cannot find baseline_run_latest folder.")

    baseline = get_zone_totals(baseline_folder)
    base_cool = baseline["cooling"]
    base_heat = baseline["heating"]

    if base_cool is None and base_heat is None:
        raise RuntimeError("Cannot extract baseline cooling/heating totals from eplustbl.csv.")

    print(f"🧱 Baseline totals → Cooling: {base_cool or 0:.2f} W, Heating: {base_heat or 0:.2f} W\n")

    modified_folders = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("modified_")
    ]
    modified_folders.sort()

    results = []
    for folder in modified_folders:
        mod_name = os.path.basename(folder)
        print(f"🔍 Analyzing {mod_name} ...")
        totals = get_zone_totals(folder)
        m_cool, m_heat = totals["cooling"], totals["heating"]

        row = {
            "run_name": mod_name,
            "cooling_baseline_W": base_cool,
            "cooling_modified_W": m_cool,
            "heating_baseline_W": base_heat,
            "heating_modified_W": m_heat,
            "cooling_delta_W": None,
            "heating_delta_W": None,
            "cooling_delta_%": None,
            "heating_delta_%": None,
        }

        if base_cool and m_cool:
            row["cooling_delta_W"] = m_cool - base_cool
            row["cooling_delta_%"] = (m_cool - base_cool) / base_cool * 100
        if base_heat and m_heat:
            row["heating_delta_W"] = m_heat - base_heat
            row["heating_delta_%"] = (m_heat - base_heat) / base_heat * 100

        results.append(row)

    df = pd.DataFrame(results)
    df["sensitivity_score"] = df.apply(
        lambda r: max(abs(r.get("cooling_delta_%") or 0), abs(r.get("heating_delta_%") or 0)),
        axis=1,
    )
    df_sorted = df.sort_values(by="sensitivity_score", ascending=False).reset_index(drop=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    csv_out = os.path.join(results_dir, f"quant_summary_{timestamp}.csv")
    json_out = os.path.join(results_dir, f"quant_summary_{timestamp}.json")
    md_out = os.path.join(results_dir, f"quant_summary_{timestamp}.md")

    df_sorted.to_csv(csv_out, index=False, encoding="utf-8-sig")

    # Identify most sensitive parameter
    top_run = df_sorted.iloc[0]
    top_name = top_run["run_name"]
    top_param = top_name.replace("modified_", "").split("_run_")[0]
    top_score = top_run["sensitivity_score"]

    print(f"\n🔥 Most sensitive parameter: {top_param} (impact score = {top_score:.2f}%)")

    # Create natural language summary
    summary_text = (
        f"**Quantitative Sensitivity Analysis Summary**\n\n"
        f"- Baseline total cooling load: **{base_cool:.2f} W**\n"
        f"- Baseline total heating load: **{base_heat:.2f} W**\n\n"
        f"Among all modified simulations, **{top_param}** showed the highest sensitivity "
        f"with an overall change of **{top_score:.2f}%**. "
        f"This indicates that the parameter has the strongest quantitative impact "
        f"on the user's optimization goal.\n\n"
        f"The complete ranked sensitivity list is available in the attached CSV/JSON files."
    )

    # Save JSON
    summary = {
        "baseline": {"cooling_total_W": base_cool, "heating_total_W": base_heat},
        "runs": df_sorted.to_dict(orient="records"),
        "most_sensitive_parameter": {"name": top_param, "score_%": top_score},
        "summary_text": summary_text,
        "note": "sensitivity_score = max(|ΔCooling%|, |ΔHeating%|)",
    }

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Save Markdown
    with open(md_out, "w", encoding="utf-8") as f:
        f.write(summary_text)

    # Print console summary
    print("\n📊 Top 5 sensitivity results:")
    top5 = df_sorted.head(5).to_dict(orient="records")
    for i, r in enumerate(top5, 1):
        print(
            f"  {i}. {r['run_name']}: ΔCooling%={r.get('cooling_delta_%','NA')}, "
            f"ΔHeating%={r.get('heating_delta_%','NA')} (score={r['sensitivity_score']})"
        )

    print(f"\n💾 Saved CSV → {csv_out}")
    print(f"💾 Saved JSON → {json_out}")
    print(f"📝 Saved Markdown summary → {md_out}")

    return summary


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    base_dir = SIM_DIR
    results_dir = RESULTS_DIR

    print("📐 Agent 3c – Quantitative & Sensitivity Analyzer (v0.95 Final)\n")
    try:
        analyze_all(base_dir, results_dir)
    except Exception as e:
        print("❌ Error:", e)
