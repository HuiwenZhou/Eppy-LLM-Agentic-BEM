"""
Eppy-LLM: Natural-Language-Driven Building Energy Modeling
===========================================================

Module: main.py
Agentic-BEM Workflow Orchestrator
---------------------------------
Coordinates the full five-agent workflow:

    1. Agent 1 – Semantic Interpreter
    2. Agent 2 – Deterministic Modifier
    3. Agent 3a – EnergyPlus Simulation Runner
    4. Agent 3b – Result Analyzer & LLM Feedback
    5. Agent 3c – Quantitative Sensitivity Analyzer

This script is the central entry point for the Eppy-LLM framework.
It allows researchers to reproduce experiments end-to-end or to
execute individual agents for debugging and ablation studies.

Author: Huiwen Zhou  
Maintainer: @huiwenzhou  
"""

import os
import subprocess
import time
import datetime

# === Global Settings ===
USER_GOAL = "reduce heat gain through windows while maximizing daylight availability"
DEFAULT_MODEL = "gpt-5"  # You can change to other model if needed

# === Base Directories ===
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
OUTPUT_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), "outputs")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")

# === Helper Function ===
def run_step(step_name: str, module_name: str, user_goal: str):
    """Run each agent as a subprocess with unified goal parameter."""
    print(f"\n🚀 [START] {step_name}")
    start = time.time()

    # Pass goal as CLI argument
    command = f'python -m src.tools.{module_name} --goal "{user_goal}"'
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ [FAILED] {step_name}: {e}")
        return False

    duration = time.time() - start
    print(f"✅ [DONE] {step_name} — ({duration:.2f} sec)")
    return True


def main():
    print("\n===================================")
    print("🏗️  Agentic-BEM Workflow Runner")
    print("===================================\n")

    print(f"🎯 USER GOAL: {USER_GOAL}")
    print(f"🧠 LLM MODEL: {DEFAULT_MODEL}")
    print("===================================\n")

    # === Step 1: Schema Extraction ===
    if not run_step("Agent 1 – Parameter Schema Extraction", "parameter_schema_tool", USER_GOAL):
        return

    # === Step 2: Parameter Modification ===
    if not run_step("Agent 2 – Parameter Modification / IDF Generation", "parameter_modifier_tool", USER_GOAL):
        return

    # === Step 3: Simulation Runner ===
    if not run_step("Agent 3a – Simulation Runner", "simulation_runner_tool", USER_GOAL):
        return

    # === Step 4: Qualitative Analysis ===
    if not run_step("Agent 3b – LLM Qualitative Analysis", "result_analysis_tool", USER_GOAL):
        return

    # === Step 5: Quantitative Sensitivity ===
    if not run_step("Agent 3c – Quantitative Sensitivity Analyzer", "quant_sensitivity_tool", USER_GOAL):
        return

    # === Final Summary ===
    print("\n===================================")
    print("🎉 Full Agentic-BEM Workflow Completed Successfully!")
    print("===================================\n")

    print(f"🕒 Finished at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📂 Results saved to: {RESULTS_DIR}\n")


if __name__ == "__main__":
    main()
