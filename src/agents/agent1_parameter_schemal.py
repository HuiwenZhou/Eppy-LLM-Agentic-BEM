"""
Eppy-LLM: Natural-Language-Driven Building Energy Modeling
===========================================================

Module: parameter_schema_tool.py
Agent 1 – Semantic Interpreter
------------------------------
Automatically analyzes an EnergyPlus IDF model, categorizes editable parameters
by surface type, and leverages a local LLM (CrewAI-compatible) to identify the
most relevant parameters for a given user goal.

It outputs a structured JSON schema mapping user intent → physical parameters,
enabling deterministic modification by Agent 2.

Author: Huiwen Zhou
Maintainer: @huiwenzhou
"""

import json
import os
import re
from eppy.modeleditor import IDF
from src.llm.eppy_openai_llm import EppyOpenAILLM
from dotenv import load_dotenv

# ✅ 1. Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), "../../.env")
load_dotenv(dotenv_path)

# ✅ White list
WHITELIST = {
    "BUILDING",
    "MATERIAL",
    "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM",
    "CONSTRUCTION",
    "FENESTRATIONSURFACE:DETAILED", 
    "BUILDINGSURFACE:DETAILED",
    "SHADING:ZONE:DETAILED",
    "SHADING:BUILDING:DETAILED",
}


def categorize_surface(obj, obj_type: str) -> str:
    """
    Determine surface category based on object type and attributes
    return: ExteriorWall, InteriorWall, Roof, Floor, Window, Door, Shading, Building
    """
    obj_type_upper = obj_type.upper()
    
    # Building
    if obj_type_upper == "BUILDING":
        return "Building"
    
    # Window and doors
    if obj_type_upper == "FENESTRATIONSURFACE:DETAILED":
        surface_type = str(obj.get("Surface_Type", "")).lower()
        if "window" in surface_type:
            return "Window"
        elif "door" in surface_type:
            return "Door"
        return "Fenestration"
    
    # Shadings
    if "SHADING" in obj_type_upper:
        return "Shading"
    
    # Building surface
    if obj_type_upper == "BUILDINGSURFACE:DETAILED":
        surface_type = str(obj.get("Surface_Type", "")).lower()
        outside_boundary = str(obj.get("Outside_Boundary_Condition", "")).lower()
        
        # Determine whether it is an outer surface
        is_exterior = "outdoors" in outside_boundary or "ground" in outside_boundary
        
        if "wall" in surface_type:
            return "ExteriorWall" if is_exterior else "InteriorWall"
        elif "roof" in surface_type or "ceiling" in surface_type:
            return "Roof" if is_exterior else "InteriorCeiling"
        elif "floor" in surface_type:
            return "Floor" if is_exterior else "InteriorFloor"
    
    # Material and Construction
    if obj_type_upper == "MATERIAL" or obj_type_upper == "WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM":
        return "Material"
    
    if obj_type_upper == "CONSTRUCTION":
        return "Construction"
    
    return "Other"


def get_dynamic_schema(idf_path: str) -> dict:
    """Scans IDF files and organizes editable parameters by category"""
    IDD_PATH = os.getenv("ENERGYPLUS_IDD_PATH", "")
    if not IDD_PATH:
        raise ValueError("ENERGYPLUS_IDD_PATH not set. Please export the path to Energy+.idd.")

    IDF.setiddname(IDD_PATH)
    idf = IDF(idf_path)

    editable = {}
    
    for obj_type, objs in idf.idfobjects.items():
        if not objs:
            continue
        if obj_type.upper() not in WHITELIST:
            continue

        # Group objects by category
        categorized_samples = {}
        
        for obj in objs:
            category = categorize_surface(obj, obj_type)
            
            if category not in categorized_samples:
                categorized_samples[category] = []
            
            # Get the object name (if it exists)
            obj_name = obj.get("Name", f"Unnamed_{len(categorized_samples[category])}")
            
            # Collect all fields and values
            sample_data = {
                "object_name": obj_name,
                "fields": {}
            }
            
            for field in obj.fieldnames:
                try:
                    value = obj[field]
                    # Only record fields that have actual values
                    if value is not None and str(value).strip() != "":
                        sample_data["fields"][field] = value
                except:
                    continue
            
            categorized_samples[category].append(sample_data)
        
        # Stored in the editable dictionary
        editable[obj_type] = {
            "categories": categorized_samples,
            "available_fields": objs[0].fieldnames if objs else []
        }
    
    return editable


def generate_semantic_schema(idf_path: str, user_goal: str) -> dict:
    """Run an LLM analysis, selecting the relevant enclosure parameters (with exact object names)"""
    editable = get_dynamic_schema(idf_path)
    obj_list = list(editable.keys())
    
    # Create a cleaner prompt data structure
    prompt_data = {}
    for obj_type, data in editable.items():
        prompt_data[obj_type] = {}
        for category, samples in data["categories"].items():
            # Show the first 3 samples to reduce token consumption
            prompt_data[obj_type][category] = samples[:3]
    
    editable_json = json.dumps(prompt_data, indent=2, ensure_ascii=False)

    prompt = f"""
You are a Building Energy Modeling (BEM) expert. The user goal is: "{user_goal}"

You are given an IDF editability map organized by surface categories (ExteriorWall, InteriorWall, Roof, Window, Building, etc.).

**CRITICAL RULES:**
1) `idf_object` MUST be one of this exact list (no new names allowed):
   {json.dumps(obj_list, indent=2)}

2) `category` MUST be one of: ExteriorWall, InteriorWall, Roof, Floor, Window, Door, Shading, Building, Material, Construction

3) `object_name` MUST be copied EXACTLY from the "object_name" field in the samples. This identifies the specific wall, window, or building object.

4) `field` MUST be chosen from the available fields for that object type.

5) `original_value` MUST be copied from the provided samples for that object_name + field combination.
   If the value is not in samples, set "original_value": "unknown".

6) For Building orientation: use idf_object="BUILDING", field="North_Axis"
   For window-to-wall ratio adjustment: use idf_object="FENESTRATIONSURFACE:DETAILED", field="Multiplier"

7) DO NOT invent new object types, categories, or field names. If not available, skip it.

8) Return ONLY valid JSON, no commentary or markdown.

**Available IDF Objects with Categorized Samples:**
{editable_json}

**Task:** Select the top 1-8 most impactful parameters for the user goal and return:

{{
  "goal": "{user_goal}",
  "parameters_to_modify": {{
    "<descriptive_parameter_name>": {{
      "idf_object": "<one of the allowed objects>",
      "category": "<ExteriorWall|InteriorWall|Roof|Window|Building|etc>",
      "object_name": "<exact name from samples, e.g., 'Perimeter_ZN_1_wall_south_Window_1'>",
      "field": "<field name, e.g., 'Thermal_Absorptance' or 'Multiplier'>",
      "original_value": "<copied from samples or 'unknown'>",
      "expected_effect": "increase|decrease|adjust",
      "suggested_range": [min_value, max_value],
      "unit": "<unit if known, e.g., 'deg', 'W/m2-K', or empty string>"
    }}
  }}
}}

**Example output structure:**
{{
  "goal": "reduce cooling load",
  "parameters_to_modify": {{
    "South_Window_Size": {{
      "idf_object": "FENESTRATIONSURFACE:DETAILED",
      "category": "Window",
      "object_name": "Perimeter_ZN_1_wall_south_Window_1",
      "field": "Multiplier",
      "original_value": 1.0,
      "expected_effect": "decrease",
      "suggested_range": [0.5, 0.9],
      "unit": ""
    }},
    "Building_Orientation": {{
      "idf_object": "BUILDING",
      "category": "Building",
      "object_name": "Ref Bldg Small Office New2004_v1.3_5.0",
      "field": "North_Axis",
      "original_value": 0.0,
      "expected_effect": "adjust",
      "suggested_range": [0, 180],
      "unit": "deg"
    }},
    "Exterior_Wall_Thermal_Absorptance": {{
      "idf_object": "MATERIAL",
      "category": "Material",
      "object_name": "1IN Stucco",
      "field": "Thermal_Absorptance",
      "original_value": 0.9,
      "expected_effect": "decrease",
      "suggested_range": [0.2, 0.5],
      "unit": ""
    }}
  }}
}}
"""
   
    # ✅ 2. Create a local CrewAI LLM instance
    llm = EppyOpenAILLM(model="gpt-5", temperature=0.2)

    # ✅ 3. Run the LLM
    response = llm.call(prompt)
    raw_output = response["content"] if isinstance(response, dict) else str(response)

    # ✅ 4. Parse JSON response
    try:
        result = json.loads(raw_output)
    except Exception:
        # Try to extract JSON from code block
        match = re.search(r"```json\s*(.*?)```", raw_output, re.S)
        if match:
            try:
                json_str = match.group(1).strip()
                result = json.loads(json_str)
            except Exception as e:
                result = {
                    "error": "JSON inside code block failed to parse",
                    "raw": json_str,
                    "exception": str(e)
                }
        else:
            result = {
                "error": "Failed to parse LLM output",
                "raw": raw_output
            }

    # ✅ 5. Validation: Check if parameters have required fields
    if isinstance(result, dict) and "parameters_to_modify" in result:
        validated_params = {}
        for param_name, param_data in result["parameters_to_modify"].items():
            if all(key in param_data for key in ["idf_object", "field", "object_name"]):
                validated_params[param_name] = param_data
            else:
                print(f"⚠️ Warning: Parameter '{param_name}' missing required fields, skipped.")
        
        result["parameters_to_modify"] = validated_params
        result["total_parameters"] = len(validated_params)

    return result


if __name__ == "__main__":
    idf_path = r"sample_files\iUnit_Golden.idf"
    user_goal = "reduce cooling load while maintaining comfort"

    print("🚀 Running parameter schema generator...\n")
    try:
        schema = generate_semantic_schema(idf_path, user_goal)

        print("✅ Generated Dynamic Schema:")
        print(json.dumps(schema, indent=2, ensure_ascii=False))

        import datetime
        # ✅ 6. Save to JSON file for Agent 2
        output_dir = r"outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        output_path = os.path.join(output_dir, f"parameter_schema_{timestamp}.json")
        latest_path = os.path.join(output_dir, "parameter_schema_latest.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Timestamped schema saved to: {output_path}")
        print(f"📄 Latest version also saved to: {latest_path}")
        
        # 打印参数统计
        if "parameters_to_modify" in schema:
            print(f"\n📊 Total parameters identified: {len(schema['parameters_to_modify'])}")
            print("\n📋 Parameter Summary:")
            for param_name, param_data in schema["parameters_to_modify"].items():
                category = param_data.get("category", "Unknown")
                obj_name = param_data.get("object_name", "Unknown")
                field = param_data.get("field", "Unknown")
                print(f"  • {param_name}: [{category}] {obj_name} → {field}")

    except Exception as e:
        print("❌ Error:", e)
        import traceback
        traceback.print_exc()