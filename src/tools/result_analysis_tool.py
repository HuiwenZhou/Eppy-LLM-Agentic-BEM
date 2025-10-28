"""
Eppy-LLM: Natural-Language-Driven Building Energy Modeling
==========================================================

Module: result_analysis_tool.py  
Agent 3b – Simulation Result Analyzer & LLM Feedback
----------------------------------------------------
Compares EnergyPlus simulation results between baseline and modified models. 
Quantitatively computes percentage changes in key energy metrics (e.g., heating, cooling, site energy) 
and qualitatively interprets those differences using LLM reasoning.

This module bridges deterministic simulation outputs and semantic interpretation — 
producing human-readable insights for energy efficiency and comfort trade-offs.

Author: Huiwen Zhou  
Maintainer: @huiwenzhou  
"""


import os
import json
import re
import datetime
import pandas as pd
from dotenv import load_dotenv
from src.llm.eppy_openai_llm import EppyOpenAILLM


# ============================================================
# 🔧 Environment Setup
# ============================================================
dotenv_path = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(dotenv_path)


# ============================================================
# 🧠 LLM Comparison Function
# ============================================================
def compare_simulation_results_csv(baseline_csv: str, modified_csv: str, user_goal: str) -> dict:
    """Compare EnergyPlus simulation results (CSV-based) using LLM reasoning."""

    if not os.path.exists(baseline_csv):
        raise FileNotFoundError(f"❌ Baseline CSV not found: {baseline_csv}")
    if not os.path.exists(modified_csv):
        raise FileNotFoundError(f"❌ Modified CSV not found: {modified_csv}")

    # ✅ Safe CSV reader: handles UTF-8 / Latin1 / CP1252 encodings
    def safe_read_csv(path):
        """Read EnergyPlus CSV with tolerant parsing to handle inconsistent columns."""
        for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
            try:
                # engine='python' allows irregular rows
                return pd.read_csv(
                    path,
                    encoding=enc,
                    on_bad_lines="skip",   # skip problematic lines instead of failing
                    engine="python"        # more flexible parser
                )
            except Exception:
                continue
        raise UnicodeDecodeError(f"❌ Failed to decode CSV: {path}")


    baseline_df = safe_read_csv(baseline_csv)
    modified_df = safe_read_csv(modified_csv)

    baseline_text = baseline_df.head(400).to_csv(index=False)
    modified_text = modified_df.head(400).to_csv(index=False)

    llm = EppyOpenAILLM(model="gpt-4o-mini", temperature=0.3)
    prompt = f"""
    You are a Building Energy Modeling expert analyzing EnergyPlus simulation results.

    The user's goal is: **{user_goal}**

    Below are the tabular outputs (in CSV form) from two EnergyPlus simulations: baseline and modified.
    Compare quantitative differences and summarize trends.

    Return JSON:
    {{
      "summary": {{
          "major_differences": [
              {{
                  "parameter": "<parameter name>",
                  "baseline_value": "<value>",
                  "modified_value": "<value>",
                  "impact": "<increase/decrease/no change>",
                  "interpretation": "<implication or reasoning>"
              }}
          ],
          "overall_trend": "<concise conclusion>"
      }}
    }}

    --- BASELINE CSV (truncated to 400 rows) ---
    {baseline_text}

    --- MODIFIED CSV (truncated to 400 rows) ---
    {modified_text}
    """

    response = llm.call(prompt)
    raw_output = response if isinstance(response, str) else str(response.get("content", response))

    match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", raw_output)
    if not match:
        match = re.search(r"(\{[\s\S]*\})", raw_output)

    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return {"error": "JSON parse error", "raw_output": raw_output[:800]}
    return {"error": "No valid JSON detected", "raw_output": raw_output[:800]}


# ============================================================
# 📂 File Utility: Find eplustbl.csv
# ============================================================
def find_result_csv(folder: str) -> str:
    """Locate eplustbl.csv inside an EnergyPlus output directory."""
    for file in os.listdir(folder):
        if file.lower().endswith("eplustbl.csv"):
            return os.path.join(folder, file)
    raise FileNotFoundError(f"No eplustbl.csv found in {folder}")


# ============================================================
# 🧪 Main Batch Comparison
# ============================================================
if __name__ == "__main__":
    base_dir = r"outputs\simulations"
    results_dir = r"outputs\results"
    os.makedirs(results_dir, exist_ok=True)

    user_goal = "Reduce heat gain through windows while maximizing daylight availability without changing building orientation"

    print("🤖 Running EnergyPlus CSV-based comparison workflow...\n")

    # ✅ Baseline
    baseline_csv = find_result_csv(os.path.join(base_dir, "baseline_run_latest"))
    print(f"🧱 Baseline CSV: {baseline_csv}\n")

    # ✅ Find modified result folders
    subfolders = [
        os.path.join(base_dir, f)
        for f in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, f)) and f.startswith("modified_")
    ]

    if not subfolders:
        print("⚠️ No modified simulation results found. Please run Agent 3a first.")
    else:
        for folder in sorted(subfolders):
            try:
                modified_csv = find_result_csv(folder)
                mod_name = os.path.basename(folder)
                print(f"🔍 Comparing baseline ↔ {mod_name}")

                result = compare_simulation_results_csv(baseline_csv, modified_csv, user_goal)

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                out_path = os.path.join(results_dir, f"comparison_{mod_name}_{timestamp}.json")

                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                # ✅ Print summary feedback
                if "summary" in result:
                    summary = result["summary"]
                    n = len(summary.get("major_differences", []))
                    print(f"✅ {mod_name}: {n} differences identified.")
                    print(f"📈 Overall trend: {summary.get('overall_trend', 'N/A')}\n")
                else:
                    print(f"⚠️ {mod_name}: No structured summary found.\n")

            except Exception as e:
                print(f"❌ Error comparing {folder}: {e}\n")

    print(f"💾 All results saved to: {results_dir}")
