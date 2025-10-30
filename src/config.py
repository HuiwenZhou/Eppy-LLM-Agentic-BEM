import os
from dotenv import load_dotenv

# === Load Environment Variables ===
load_dotenv()

# === Paths ===
ENERGYPLUS_DIR = os.getenv("ENERGYPLUS_DIR", r"C:\EnergyPlusV25-1-0")
ENERGYPLUS_IDD_PATH = os.getenv("ENERGYPLUS_IDD_PATH", os.path.join(ENERGYPLUS_DIR, "Energy+.idd"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
