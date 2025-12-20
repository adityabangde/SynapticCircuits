import os
from google import genai
from google.genai import types # Required for safety settings
from PySpice.Spice.Netlist import Circuit

# 1. API Configuration
# Replace with your actual key or ensure it is set as an environment variable
GEMINI_API_KEY = "your_api_key_here" 
client = genai.Client(api_key=GEMINI_API_KEY)

def get_circuit_json(prompt):
    # 1. Lower safety thresholds to prevent "False Positives" on circuit designs
    safety_settings = [
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_ONLY_HIGH", # Allow more complex technical designs
        ),
    ]

    system_instr = (
        "You are an electrical engineering assistant. Convert requests into JSON. "
        "Schema: {'circuit_name': str, 'components': [{'type': str, 'id': str, "
        "'nodes': [str, str], 'value': str}], 'simulation': str}. "
        "Output ONLY valid JSON."
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "system_instruction": system_instr,
                "response_mime_type": "application/json",
                "safety_settings": safety_settings
            }
        )

        # CHECK 1: If safety filters blocked it
        if response.candidates[0].finish_reason == "SAFETY":
            print("Error: The design was blocked by safety filters. Try a simpler prompt.")
            return None

        # CHECK 2: Fallback to manual parsing if .parsed is None
        if response.parsed:
            return response.parsed
        
        if response.text:
            import json
            # Clean possible markdown code blocks from text
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)

        return None
        
    except Exception as e:
        print(f"API Error: {e}")
        return None

# build_and_save_netlist function remains the same as previous version

def build_and_save_netlist(data, target_folder="generated_circuits"):
    if not data:
        return None

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    circuit_name = data.get("circuit_name", "Design").replace(" ", "_")
    circuit = Circuit(circuit_name)
    
    for comp in data.get("components", []):
        ctype = comp["type"].upper()
        cid = str(comp["id"])
        n = comp["nodes"]
        val = comp["value"]
        
        try:
            if ctype == 'R': circuit.R(cid, n[0], n[1], val)
            elif ctype == 'C': circuit.C(cid, n[0], n[1], val)
            elif ctype == 'L': circuit.L(cid, n[0], n[1], val)
            elif ctype == 'V': circuit.V(cid, n[0], n[1], val)
            elif ctype == 'I': circuit.I(cid, n[0], n[1], val)
        except Exception as e:
            print(f"Warning: Could not add component {ctype}{cid}: {e}")

    # Append simulation directives
    sim_cmd = data.get("simulation", ".op")
    circuit.raw_spice += f"\n{sim_cmd}\n.end"
    
    # --- ADDED PRINT STATEMENT HERE ---
    netlist_content = str(circuit)
    print("\n--- GENERATED SPICE NETLIST ---")
    print(netlist_content)
    print("-------------------------------\n")
    
    file_path = os.path.join(target_folder, f"{circuit_name}.cir")
    with open(file_path, "w") as f:
        f.write(netlist_content)
    
    return os.path.abspath(file_path)

if __name__ == "__main__":
    user_prompt = input("Describe the circuit: ")
    circuit_data = get_circuit_json(user_prompt)
    print(circuit_data)
    
    if circuit_data:
        saved_path = build_and_save_netlist(circuit_data)
        if saved_path:
            print("-" * 40)
            print(f"Netlist saved to: {saved_path}")
            print("-" * 40)