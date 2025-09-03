import os
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import google.generativeai as genai

# --------- Load API Key ---------
load_dotenv()  # load .env into environment

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set. Add it to .env or PyCharm env vars.")

genai.configure(api_key=api_key)

# --------- Config ---------
MODEL_NAME = "gemini-1.5-flash"
TRANSCRIPT_FILE = Path("assistant_history.jsonl")  # persisted memory
SYSTEM_PROMPT = (
    "You are Shivam’s AI assistant. "
    "You can chat naturally, but when useful, call tools like Calendar and Email. "
    "Always explain your reasoning briefly before/after tool use."
)

# Create model (global)
model = genai.GenerativeModel(MODEL_NAME)

# --------- Tools ---------
def check_calendar(user: str):
    """Fake calendar API"""
    return {
        "shivam": ["Wed 10AM", "Thu 11AM"],
        "priya": ["Thu 11AM", "Fri 2PM"]
    }.get(user.lower(), ["No availability found."])

def send_email(to: str, subject: str, body: str):
    """Fake email API"""
    return f"Email sent to {to} with subject '{subject}' and body '{body}'"

def handle_tools(user_input: str):
    """Detect tool commands and call fake APIs with simple parsing."""
    text = user_input.lower()

    # --- Calendar ---
    if "calendar" in text:
        if "priya" in text:
            return f"Priya’s availability: {check_calendar('priya')}"
        elif "shivam" in text:
            return f"Shivam’s availability: {check_calendar('shivam')}"
        else:
            return "Whose calendar do you want to check?"

    # --- Email ---
    if "email" in text:
        # Extract recipient name
        if "priya" in text:
            recipient = "priya@example.com"
        elif "shivam" in text:
            recipient = "raishivam313@gmail.com"
        else:
            recipient = "someone@example.com"

        subject = "Meeting"
        body = "Let’s connect at Thu 11AM."
        return send_email(recipient, subject, body)

    return None

# --------- Persistence helpers ---------
def load_history():
    if not TRANSCRIPT_FILE.exists():
        return []
    history = []
    with TRANSCRIPT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            history.append({"role": rec["role"], "parts": [rec["content"]]})
    return history

def append_history(role: str, content: str):
    with TRANSCRIPT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "content": content
        }) + "\n")

def reset_history():
    if TRANSCRIPT_FILE.exists():
        TRANSCRIPT_FILE.unlink()

# --------- Chat session ---------
def start_chat(persist: bool = True):
    base_history = []
    base_history.append({"role": "user", "parts": [SYSTEM_PROMPT]})
    if persist:
        base_history.extend(load_history())
    chat = model.start_chat(history=base_history)
    return chat

def interactive_chat():
    print(f"🤖 Gemini Assistant ({MODEL_NAME}) ready!")
    print("Commands: /reset (clear memory), /exit (quit)\n")

    chat = start_chat(persist=True)

    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye! 👋")
            break

        if not user:
            continue

        # Commands
        if user.lower() == "/exit":
            print("Bye! 👋")
            break
        if user.lower() == "/reset":
            reset_history()
            chat = start_chat(persist=True)
            print("🧹 Memory cleared.")
            continue

        # Step 1: Try tool handling
        tool_result = handle_tools(user)
        if tool_result:
            print("🔧 Tool:", tool_result)
            append_history("user", user)
            append_history("model", tool_result)
            continue

        # Step 2: Normal Gemini response
        append_history("user", user)
        try:
            stream = chat.send_message(user, stream=True)
            print("Gemini:", end=" ", flush=True)
            full_text = ""
            for chunk in stream:
                if chunk.candidates and chunk.candidates[0].content.parts:
                    piece = chunk.candidates[0].content.parts[0].text or ""
                    full_text += piece
                    print(piece, end="", flush=True)
            print()
        except Exception as e:
            print(f"\n[Error] {e}")
            continue

        append_history("model", full_text)

if __name__ == "__main__":
    interactive_chat()
