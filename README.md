# 🧠 Eppy-LLM-Agentic-BEM  
**An Agentic Workflow for LLM-Assisted Building Energy Modeling Using EnergyPlus**

This repository implements the core workflow described in the paper:  
> *Eppy-LLM: An Agentic Workflow for Natural-Language-Driven Building Energy Modeling (2025)*  
> University of Arizona, Civil & Architectural Engineering and Mechanics Department  

It integrates **EnergyPlus v25.1**, **Eppy**, and **LLM agents** (GPT-5 / OpenAI API) into a modular pipeline that enables natural-language goals to be translated into simulation-ready building energy models.

---

## 📂 Repository Structure

Eppy-LLM-Agentic-BEM/
│
├── LICENSE
├── README.md
├── requirements.txt
│
├── sample_files/
│ ├── iUnit_Golden.idf
│ └── USA_CO_Golden-NREL.724666_TMY3.epw
│
├── outputs/
│ ├── modified_idfs/
│ ├── results/
│ └── simulations/
│
└── src/
├── config.py
├── main.py
│
├── agents/
│ ├── agent1_parameter_schema.py
│ ├── agent2_parameter_modifier.py
│ ├── agent3a_simulation_runner.py
│ ├── agent3b_result_analyzer.py
│ ├── agent3c_sensitivity_analyzer.py
│ └── init.py
│
└── llm/
├── eppy_openai_llm.py
└── init.py


---

## ⚙️ 1. Environment Setup

### 🧩 Prerequisites

| Tool | Version | Purpose |
|------|----------|----------|
| **Python** | ≥ 3.11 | Core runtime |
| **EnergyPlus** | v25.1 | Building simulation engine |
| **Eppy** | ≥ 0.5.64 | Python API for IDF editing |
| **OpenAI Python SDK** | ≥ 1.40 | For LLM agent inference |
| **Pandas / Matplotlib** | ≥ 2.2 | Data analysis and visualization |

---

### 🧱 Installation Steps

#### 1️⃣ Install **EnergyPlus v25.1**

- Download from the [official DOE website](https://energyplus.net/downloads).
- During installation, note the directory (e.g. `C:\EnergyPlusV25-1-0`).
- Add the following environment variable (Windows PowerShell):

```powershell
setx ENERGYPLUS_DIR "C:\EnergyPlusV25-1-0"
```
You can test it with:
```powershell
echo $Env:ENERGYPLUS_DIR
```
#### 2️⃣ Clone this repository
```bash
git clone https://github.com/HuiwenZhou/Eppy-LLM-Agentic-BEM.git
cd Eppy-LLM-Agentic-BEM
```
#### 3️⃣ Create and activate a Python virtual environment
```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
```
#### 4️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
#### 5️⃣ (Optional) Set your OpenAI API key
```powershell
setx OPENAI_API_KEY "sk-xxxxxx..."
```
## 🚀 2. Running the Workflow
The workflow consists of **three core Agents** (1 → 3c) that together perform semantic interpretation, deterministic modification, and simulation analysis.

Each Agent can be run **individually** or **automatically** through main.py.

### 🧠 Full Pipeline Execution
```bash
python src/main.py
```
This runs:

```r
Agent 1 → Agent 2 → Agent 3a → Agent 3b → Agent 3c
```
The workflow will:

1. Parse the baseline IDF and extract editable parameters.
2. Generate modification schemas and variant IDFs.
3. Run EnergyPlus simulations automatically.
4. Compare simulation outputs.
5. Perform sensitivity and impact analysis.

All results are saved in outputs:

📁 outputs/modified_idfs/ — generated variant models

📁 outputs/simulations/ — EnergyPlus results for baseline and variants

📁 outputs/results/ — LLM comparison reports & sensitivity summaries

> ⚠️ **Note:**  
> The `outputs/` folder currently contains example results from a demonstration run.  
> These files illustrate the expected directory structure and output format of the workflow.  
> If you want to re-run your own case from scratch, you can safely delete all files and folders inside `outputs/` before execution.  
> The workflow will automatically regenerate them during runtime.

## 🧩 3. Running Individual Agents
### 🧱 Agent 1 — Semantic Interpreter
**File**: src/agents/agent1_parameter_schema.py
**Purpose**: Parse user goals into structured JSON parameter schemas.

```bash
python src/agents/agent1_parameter_schema.py
```
**Output**:
outputs/parameter_schema_latest.json

### 🔧 Agent 2 — Deterministic Modifier
**File**: src/agents/agent2_parameter_modifier.py
**Purpose**: Automatically generate modified IDF variants based on the JSON schema.

```bash
python src/agents/agent2_parameter_modifier.py
```
**Output**:
outputs/modified_idfs/*.idf

### 🔆 Agent 3a — Simulation Runner
**File**: src/agents/agent3a_simulation_runner.py
**Purpose**: Batch-run EnergyPlus simulations for all variants.

```bash
python src/agents/agent3a_simulation_runner.py
```
**Output**:
EnergyPlus .csv, .htm, .eso files in outputs/simulations/

### 📊 Agent 3b — Qualitative Result Analyzer
**File**: src/agents/agent3b_result_analyzer.py
**Purpose**: Use LLM reasoning to compare baseline vs. modified results (CSV tables).

```bash
python src/agents/agent3b_result_analyzer.py
```
**Output**:
outputs/results/comparison_*.json

### 📈 Agent 3c — Quantitative Sensitivity Analyzer
**File**: src/agents/agent3c_sensitivity_analyzer.py
**Purpose**: Compute numeric sensitivities and parameter impacts.

```bash
python src/agents/agent3c_sensitivity_analyzer.py
```
**Output**:
outputs/results/quant_summary_*.csv
outputs/results/quant_summary_*.md

### 🔍 4. Typical Workflow Example
```text
1️⃣ User provides goal: “Reduce cooling load while maintaining comfort.”
2️⃣ Agent 1 parses editable parameters (walls, roof, windows).
3️⃣ Agent 2 generates modified IDFs with controlled perturbations.
4️⃣ Agent 3a runs EnergyPlus simulations on all variants.
5️⃣ Agent 3b analyzes differences in comfort & load.
6️⃣ Agent 3c ranks top impactful parameters quantitatively.
```
Output summaries are logged in terminal and saved as .json, .csv, and .md.

### 📊 5. Example Output Snapshot
Rank	Parameter	ΔCooling (%)	ΔHeating (%)	Impact Score
1	Building_Orientation_v3	−51.9	−0.1	51.99
2	Roof_Material_Conductivity	−30.3	+2.6	30.37
3	Building_Orientation_v2	−18.0	+0.1	18.06
4	Window_to_Wall_Ratio_v1	+0.4	−3.6	3.64
5	Window_to_Wall_Ratio_v2	+0.3	−2.6	2.57

### 🧩 6. Reproducibility Notes
The workflow is designed to work offline once the OpenAI schema files are generated.

All modified models and results include timestamps for traceability.

Paths are automatically resolved via src/config.py, so you can run any script from any directory.

Default EnergyPlus weather and IDF files are provided in sample_files/.

### 🧰 7. Key Dependencies (requirements.txt)
```text
eppy>=0.5.64
pandas>=2.2.2
matplotlib>=3.9.0
openai>=1.40.0
python-dotenv>=1.0.1
tqdm>=4.66.5
```

### 🧑‍💻 8. Contact
Author: Huiwen Zhou
Affiliation: University of Arizona, Civil & Architectural Engineering & Mechanics
Email: huiwenzhou@arizona.edu
GitHub: HuiwenZhou

Last Updated: October 2025