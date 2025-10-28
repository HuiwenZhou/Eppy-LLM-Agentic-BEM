# Eppy-LLM-Agentic-BEM
Code demo and examples for "Eppy-LLM: An Agentic Workflow for Natural-Language-Driven Building Energy Modeling"

This repository provides the source code, example files, and documentation accompanying the paper  
**"Eppy-LLM: An Agentic Workflow for Natural-Language-Driven Building Energy Modeling"**,  
submitted to *SimBuild 2026 – The Tenth National Conference of IBPSA-USA*.

The framework integrates **Large Language Model (LLM)**-based semantic reasoning with deterministic **EnergyPlus** simulation workflows through an agentic multi-stage architecture.  
It enables natural-language-driven exploration, modification, and evaluation of building energy models (BEMs) in a transparent and reproducible manner.

---

## 🧭 Overview

Eppy-LLM introduces a **three-agent system** that connects design semantics to building energy simulation and analysis:

| Agent | Function | Core Tasks |
|:------|:----------|:-----------|
| **Agent 1 – Semantic Interpreter** | Bridges user intent and simulation schema | Parses user goals and identifies relevant editable parameters in IDF |
| **Agent 2 – Deterministic Modifier** | Ensures syntactic validity and physical consistency | Applies rule-based edits via Eppy and produces validated IDF variants |
| **Agent 3 – Analytical Feedback** | Automates simulation and interprets results | Executes EnergyPlus runs, performs quantitative & qualitative analysis, and ranks parameter sensitivities |

<p align="center">
  <img src="docs/fig_framework_overview.png" width="650" alt="Framework Overview Diagram">
</p>

Each agent communicates through standardized JSON data and time-stamped directories, ensuring **traceability, reproducibility, and interpretability** throughout the simulation workflow.

---

## 📁 Repository Structure

```plaintext
Eppy-LLM-Agentic-BEM/
│
├── README.md
├── LICENSE
├── requirements.txt
│
├── sample_files/
│ ├── iUnit_Golden.idf
│ ├── USA_CO_Golden-NREL.724666_TMY3.epw
│
├── src/
│ ├── tools/
│ │ ├── parameter_schema_tool.py # Agent 1: Semantic Interpreter
│ │ ├── parameter_modifier_tool.py # Agent 2: Deterministic Modifier
│ │ ├── simulation_runner_tool.py # Agent 3a: Simulation Runner
│ │ ├── result_analysis_tool.py # Agent 3b: Result Analyzer
│ │ ├── quant_sensitivity_tool.py # Agent 3c: Sensitivity Analyzer
│ │ └── init.py
│ └── main.py # Example entry point
│
├── outputs/
│ └── demo_results/ # Example results for demonstration
│
└── docs/
└── fig_framework_overview.png
```

---

## ⚙️ Installation

1️⃣ **Clone this repository**
   ```bash
   git clone https://github.com/<your-username>/Eppy-LLM-Agentic-BEM.git
   cd Eppy-LLM-Agentic-BEM
   ```
2️⃣ **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
**Main dependencies**

eppy — EnergyPlus IDF/IDD parser

pandas — data handling and result analysis

plotly — visualization (optional)

openai — LLM interface (local/remote; optional)

3️⃣ **Configure EnergyPlus path**
Windows example:
```bash
   setx ENERGYPLUS_DIR "C:\EnergyPlusV25-1-0"
   ```
## 🚀 Quick Start

Run the **full workflow** (semantic → modification → simulation → feedback):
```bash
   python -m src.tools.simulation_runner_tool
   ```
Or run individual agents for testing:
```bash
   python -m src.tools.parameter_schema_tool
   python -m src.tools.parameter_modifier_tool
   python -m src.tools.result_analysis_tool
   python -m src.tools.quant_sensitivity_tool
   ```
**Example natural-language input**
```lua
   reduce cooling load while maintaining comfort
   ```
## 🧾 Case Study Example

The demonstration case uses the NREL iUnit, a modular residential prototype located in Golden, Colorado
(weather file USA_CO_Golden-NREL.724666_TMY3.epw).

The workflow autonomously identifies envelope-related parameters — such as insulation thickness, glazing ratio, and orientation — and quantifies their impacts on annual cooling and heating loads.

<p align="center"> <img src="docs/fig_iunit_overview.png" width="600" alt="iUnit Case Study Illustration"> </p>

| Parameter                 | Δ Cooling (%) | Δ Heating (%) | Sensitivity Score |
| :------------------------ | :------------ | :------------ | :---------------- |
| Orientation               | −5.8          | +1.2          | 5.8               |
| WWR                       | −3.2          | +0.6          | 3.2               |
| Roof Insulation Thickness | −2.7          | −0.4          | 2.7               |

**LLM-based interpretive output example**

“Reduced solar absorptance decreases afternoon cooling peaks while maintaining comfort.”

## 🔗 Related Resources

[EnergyPlus Official Documentation](https://energyplus.net/documentation).

[Eppy Python Library](https://energyplus.net/documentation).

[IBPSA-USA SimBuild Conference](https://energyplus.net/documentation).
