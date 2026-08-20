import json
import os

def record_human_feedback(raw_email_text: str, correct_category: str, human_approved_response: str):
    """Saves human-corrected resolutions back into the golden dataset for continuous learning."""
    golden_path = "tests/golden_dataset.json"
    
    new_entry = {
        "raw_email_text": raw_email_text,
        "expected_category": correct_category,
        "approved_response": human_approved_response
    }
    
    dataset = []
    if os.path.exists(golden_path):
        try:
            with open(golden_path, "r") as f:
                dataset = json.load(f)
        except Exception:
            dataset = []
            
    dataset.append(new_entry)
    
    with open(golden_path, "w") as f:
        json.dump(dataset, f, indent=4)
        
    print(f"✅ HITL Feedback captured! Added corrected ticket to {golden_path}")