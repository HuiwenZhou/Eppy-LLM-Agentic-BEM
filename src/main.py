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

Author: Huiwen Zhou
Maintainer: @huiwenzhou
"""

import os
import subprocess
import time
import datetime

# === Global Settings ===
USER_GOAL = "reduce cooling load while maintaining comfort"
DEFAULT_MODEL = "gpt-5"  # You can change this if needed

# === Base Directories ===
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(PROJECT_ROOT, "agents")
OUTPUT_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), "outputs")
RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")


def run_step(step_name: str, module_name: str, user_goal: str):
    """Run each agent as a subprocess with unified goal parameter."""
    print(f"\n🚀 [START] {step_name}")
    start = time.time()

    command = f'python -m src.agents.{module_name} --goal "{user_goal}"'
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

    # === Step 1: Agent 1 – Parameter Schema Extraction ===
    if not run_step("Agent 1 – Parameter Schema Extraction", "agent1_parameter_schemal", USER_GOAL):
        return

    # === Step 2: Agent 2 – Parameter Modification ===
    if not run_step("Agent 2 – Parameter Modification / IDF Generation", "agent2_parameter_modifier", USER_GOAL):
        return

    # === Step 3a: Simulation Runner ===
    if not run_step("Agent 3a – Simulation Runner", "agent3a_simulation_runner", USER_GOAL):
        return

    # === Step 3b: Qualitative Analysis ===
    if not run_step("Agent 3b – LLM Qualitative Analysis", "agent3b_result_analyzer", USER_GOAL):
        return

    # === Step 3c: Quantitative Sensitivity ===
    if not run_step("Agent 3c – Quantitative Sensitivity Analyzer", "agent3c_sensitivity_analyzer", USER_GOAL):
        return

    # === Final Summary ===
    print("\n===================================")
    print("🎉 Full Agentic-BEM Workflow Completed Successfully!")
    print("===================================\n")

    print(f"🕒 Finished at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📂 Results saved to: {RESULTS_DIR}\n")


if __name__ == "__main__":
    main()
