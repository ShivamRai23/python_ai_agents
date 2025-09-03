import os
import json
from openpyxl import Workbook
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd

# ------------------ Load API Key ------------------
load_dotenv()  # load .env into environment

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not set. Add it to .env or PyCharm env vars.")

genai.configure(api_key=api_key)

# ------------------ Config ------------------
MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# ------------------ Test Case Generator ------------------
def generate_test_cases(requirement: str):
    """Send requirement to Gemini and get test cases back in JSON."""
    prompt = f"""
    You are a QA Test Case Generator.
    Based on the requirement below, generate detailed test cases.

    Requirement:
    {requirement}

    Output ONLY valid JSON.
    Format: a list of objects with keys:
    - id (string, e.g. "TC001")
    - title (string)
    - preconditions (string)
    - steps (list of steps)
    - expected_result (string)
    - priority (High/Medium/Low)
    """

    response = model.generate_content(prompt)
    text = response.text.strip()

    # ✅ Handle code fences like ```json ... ```
    if text.startswith("```"):
        text = text.strip("`")
        if "json" in text[:10].lower():
            text = text.split("\n", 1)[1]

    return text

# ------------------ Save to Excel ------------------
def save_to_excel(test_cases, filename="test_cases.xlsx"):
    """Save test cases JSON into Excel."""
    try:
        cases = json.loads(test_cases)
    except Exception as e:
        raise ValueError(f"❌ Failed to parse Gemini response as JSON: {e}\n\nResponse:\n{test_cases}")

    wb = Workbook()
    ws = wb.active
    ws.title = "TestCases"

    # Header
    ws.append(["ID", "Title", "Preconditions", "Steps", "Expected Result", "Priority"])

    for idx, case in enumerate(cases, start=1):
        case_id = case.get("id") or f"TC{idx:03d}"  # Auto-generate if missing
        steps = case.get("steps", "")

        # Convert list of steps to a single string
        if isinstance(steps, list):
            steps = "\n".join(steps)

        ws.append([
            case_id,
            case.get("title", ""),
            case.get("preconditions", ""),
            steps,
            case.get("expected_result", ""),
            case.get("priority", "")
        ])

    wb.save(filename)
    print(f"✅ Test cases saved to {filename}")

# ------------------ Main ------------------
if __name__ == "__main__":
    print("🧪 Test Case Generator Agent")
    requirement = input("Enter requirement/user story: ").strip()

    print("⏳ Generating test cases...")
    test_cases_json = generate_test_cases(requirement)

    save_to_excel(test_cases_json, "test_cases.xlsx")

df = pd.read_excel("test_cases.xlsx")   # works with .xls and .xlsx
print(df.head())