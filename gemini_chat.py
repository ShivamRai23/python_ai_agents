import os
import json
import google.generativeai as genai
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# --------- Setup ---------
load_dotenv()  # load .env into environment

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set. Add it to .env or PyCharm env vars.")

genai.configure(api_key=api_key)

# Create model (make this global so it's accessible everywhere)
MODEL_NAME = "gemini-1.5-flash"   # or "gemini-1.5-pro"
model = genai.GenerativeModel(MODEL_NAME)

TRANSCRIPT_FILE = Path("chat_history.jsonl")  # persisted memory (optional)
SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. "
    "Always answer clearly and ask a brief follow-up question when useful."
)

# --------- Persistence helpers ---------
def load_history():
    """Load prior chat from a JSONL transcript into Gemini's expected format."""
    if not TRANSCRIPT_FILE.exists():
        return []
    history = []
    with TRANSCRIPT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            role = rec["role"]
            content = rec["content"]
            # Gemini expects {'role': 'user'|'model', 'parts': [text]}
            if role in ["user", "model"]:  # no system
                history.append({"role": role, "parts": [content]})
    return history

def append_history(role: str, content: str):
    """Append a message to transcript."""
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
    """
    Start a chat that remembers history.
    If persist=True, it loads/saves to chat_history.jsonl.
    """
    base_history = []

    # Put "system prompt" as a *user message* instead (Gemini has no system role)
    base_history.append({"role": "user", "parts": [f"(Instruction) {SYSTEM_PROMPT}"]})

    if persist:
        base_history.extend(load_history())

    chat = model.start_chat(history=base_history)
    return chat

def interactive_chat():
    print(f"Gemini multi-turn chat on {MODEL_NAME}")
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

        # Persist user message
        append_history("user", user)

        # Send message (streaming chunk-by-chunk)
        try:
            stream = chat.send_message(user, stream=True)
            print("Gemini:", end=" ", flush=True)
            full_text = ""
            for chunk in stream:
                if chunk.candidates and chunk.candidates[0].content.parts:
                    piece = chunk.candidates[0].content.parts[0].text or ""
                    full_text += piece
                    print(piece, end="", flush=True)
            print()  # newline
        except Exception as e:
            print(f"\n[Error] {e}")
            continue

        # Persist model reply
        append_history("model", full_text)

if __name__ == "__main__":
    interactive_chat()

