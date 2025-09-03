import os
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import google.generativeai as genai

# Google API clients
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --------- Load API Key ---------
load_dotenv()  # load .env into environment

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not set. Add it to .env or PyCharm env vars.")

genai.configure(api_key=api_key)

# --------- Config ---------
MODEL_NAME = "gemini-1.5-flash"
TRANSCRIPT_FILE = Path("assistant_history.jsonl")  # persisted memory
SYSTEM_PROMPT = (
    "You are Shivam’s AI assistant. "
    "You can chat naturally, but when useful, call tools like Calendar and Email. "
    "Always explain your reasoning briefly before/after tool use."
)

# Google API scopes
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Create model (global)
model = genai.GenerativeModel(MODEL_NAME)

# --------- Google Auth Helper ---------
def get_service(api: str, version: str, scopes: list):
    """Authenticate and return a Google API service client."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build(api, version, credentials=creds)

# --------- Real Tools ---------
def check_calendar():
    """Check upcoming 5 events from Google Calendar."""
    service = get_service("calendar", "v3", CALENDAR_SCOPES)
    now = datetime.utcnow().isoformat() + "Z"
    events_result = (
        service.events()
        .list(calendarId="primary", timeMin=now, maxResults=5, singleEvents=True, orderBy="startTime")
        .execute()
    )
    events = events_result.get("items", [])
    if not events:
        return "No upcoming events."
    return [f"{e['summary']} at {e['start'].get('dateTime', e['start'].get('date'))}" for e in events]

def create_meeting(summary="Meeting with Shivam", start_time=None, duration=60):
    """Create a Google Calendar event with Meet link."""
    service = get_service("calendar", "v3", CALENDAR_SCOPES)
    if not start_time:
        start_time = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    end_time = datetime.fromisoformat(start_time.replace("Z", "")) + timedelta(minutes=duration)

    event = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
        "conferenceData": {"createRequest": {"requestId": "meet-" + datetime.now().isoformat()}},
    }

    created_event = (
        service.events()
        .insert(calendarId="primary", body=event, conferenceDataVersion=1)
        .execute()
    )
    return created_event.get("hangoutLink", "❌ No Meet link generated.")

def send_email(to: str, subject: str, body: str):
    """Send an email using Gmail API."""
    from email.mime.text import MIMEText
    import base64

    service = get_service("gmail", "v1", GMAIL_SCOPES)
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"📧 Real email sent to {to} (ID: {sent['id']})"

# --------- Tool Handler ---------
def handle_tools(user_input: str):
    text = user_input.lower()

    if "calendar" in text:
        return f"📅 Upcoming events: {check_calendar()}"

    if "meeting" in text or "meet link" in text:
        link = create_meeting()
        return f"✅ Meeting created with Google Meet link: {link}"

    if "email" in text:
        if "shivam" in text:
            recipient = "raishivam313@gmail.com"
        else:
            recipient = "someone@example.com"
        subject = "Meeting Link"
        link = create_meeting()
        body = f"Here’s your meeting link: {link}"
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
    print(f"🤖 Gemini Assistant ({MODEL_NAME}) ready with real tools!")
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

        if user.lower() == "/exit":
            print("Bye! 👋")
            break
        if user.lower() == "/reset":
            reset_history()
            chat = start_chat(persist=True)
            print("🧹 Memory cleared.")
            continue

        tool_result = handle_tools(user)
        if tool_result:
            print("🔧 Tool:", tool_result)
            append_history("user", user)
            append_history("model", tool_result)
            continue

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
