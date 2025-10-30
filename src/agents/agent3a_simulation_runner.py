"""
Eppy-LLM: Natural-Language-Driven Building Energy Modeling
===========================================================

Module: simulation_runner_tool.py
Agent 3a – Simulation Runner
-----------------------------
Executes EnergyPlus simulations for baseline and modified IDF files.  
Supports automatic baseline caching (via hash comparison) to avoid redundant runs,
and provides timestamped directories with structured logs.

It is designed to integrate seamlessly with Agents 1–2 outputs and produce
EnergyPlus-compatible simulation folders for further analysis by Agents 3b–3c.

Author: Huiwen Zhou  
Maintainer: @huiwenzhou  
"""

import os
import subprocess
import datetime
import hashlib
import json
import shutil
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_files")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
SIM_DIR = os.path.join(OUTPUTS_DIR, "simulations")
RESULTS_DIR = os.path.join(OUTPUTS_DIR, "results")

# ✅ Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(dotenv_path)


def file_hash(path: str) -> str:
    """Generate MD5 hash of file content."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def run_energyplus_simulation(idf_path: str, weather_path: str, output_root: str, label: str = None) -> str:
    """
    Runs an EnergyPlus simulation and saves results in a timestamped directory.

    Args:
        idf_path: Path to IDF file.
        weather_path: Path to EPW weather file.
        output_root: Root folder for simulation outputs.
        label: Optional tag (e.g., 'baseline', 'modified').

    Returns:
        output_dir (str): Directory containing simulation outputs.
    """
    energyplus_exe = os.getenv("ENERGYPLUS_EXE")
    if not energyplus_exe or not os.path.exists(energyplus_exe):
        ep_dir = os.getenv("ENERGYPLUS_DIR")
        if ep_dir and os.path.exists(ep_dir):
            energyplus_exe = os.path.join(ep_dir, "energyplus.exe")
        else:
            raise FileNotFoundError("❌ Cannot find EnergyPlus executable. Please set ENERGYPLUS_EXE or ENERGYPLUS_DIR.")

    # === 1️⃣ Prepare output directory ===
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    idf_name = os.path.splitext(os.path.basename(idf_path))[0]
    run_label = label or idf_name
    output_dir = os.path.join(output_root, f"{run_label}_run_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"🚀 Running EnergyPlus for: {idf_path}")
    print(f"🌦️ather file: {weather_path}")
    print(f"📂 Output directory: {output_dir}")

    cmd = [
        energyplus_exe,
        "-w", weather_path,
        "-d", output_dir,
        "-r",
        idf_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)

        log_path = os.path.join(output_dir, "run.log")
        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write(result.stdout)
            log_file.write(result.stderr)

        if result.returncode == 0:
            print("✅ Simulation completed successfully.")
        else:
            print("⚠️ Simulation finished with warnings/errors.")
            print(result.stderr[:500])

    except subprocess.TimeoutExpired:
        raise TimeoutError("⏰ EnergyPlus simulation timed out (15 min limit).")
    except Exception as e:
        raise RuntimeError(f"❌ Simulation failed: {e}")

    return output_dir


def run_baseline_if_needed(idf_path: str, weather_path: str, output_root: str) -> str:
    """
    Check for cached baseline; only re-run if missing or IDF changed.
    """
    baseline_dir = os.path.join(output_root, "baseline_run_latest")
    metadata_path = os.path.join(baseline_dir, "metadata.json")

    os.makedirs(output_root, exist_ok=True)

    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        cached_hash = meta.get("idf_hash")
        current_hash = file_hash(idf_path)

        if cached_hash == current_hash:
            print(f"🧠 Using cached baseline results from: {baseline_dir}")
            return baseline_dir
        else:
            print("⚙️ Baseline IDF has changed — re-running baseline simulation.")

    # Run new baseline simulation
    print("🚀 Running new baseline simulation...")
    new_dir = run_energyplus_simulation(idf_path, weather_path, output_root, label="baseline")

    # === 🧩 Copy key results (HTML, CSV, etc.) into baseline_run_latest ===
    os.makedirs(baseline_dir, exist_ok=True)
    for file in os.listdir(new_dir):
        if file.lower().endswith((".htm", ".html", ".csv", ".eso", ".rdd", ".mtr")):
            src = os.path.join(new_dir, file)
            dst = os.path.join(baseline_dir, file)
            shutil.copy2(src, dst)

    # Save metadata
    new_hash = file_hash(idf_path)
    meta = {
        "idf_path": idf_path,
        "idf_hash": new_hash,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "output_dir": new_dir
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"💾 Baseline metadata saved → {metadata_path}")
    return baseline_dir


if __name__ == "__main__":
    idf_path = os.path.join(SAMPLE_DIR, "iUnit_Golden.idf")
    weather_path = os.path.join(SAMPLE_DIR, "USA_CO_Golden-NREL.724666_TMY3.epw")
    output_root = SIM_DIR

    print("🚀 Starting EnergyPlus Simulation Test...\n")

    try:
        # ✅ Run baseline only once
        baseline_dir = run_baseline_if_needed(idf_path, weather_path, output_root)

        # ✅ Run multiple modified idfs
        modified_root = r"outputs\modified_idfs"
        modified_files = [
            f for f in os.listdir(modified_root)
            if f.lower().endswith(".idf")
        ]

        for file in modified_files:
            modified_path = os.path.join(modified_root, file)
            label = os.path.splitext(file)[0]  # eg. modified_Window_U-factor
            modified_dir = run_energyplus_simulation(
                modified_path, weather_path, output_root, label=label
            )
            print(f"✅ Modified simulation complete: {modified_dir}")

        print(f"\n🏁 Baseline results: {baseline_dir}")
        print("🔗 Open 'eplustbl.htm' inside these folders for details.")

    except Exception as e:
        print("❌ Error:", e)

