from dotenv import load_dotenv
import os, google.generativeai as genai

load_dotenv()  # load .env into environment

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not set. Add it to .env or PyCharm env vars.")

genai.configure(api_key=api_key)

class GeminiClient:
    def __init__(self, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client.
        model: "gemini-1.5-flash" (fast/free) or "gemini-1.5-pro" (better reasoning)
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY not set. Run: export GEMINI_API_KEY='your_key_here'")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        print(f"✅ Using Gemini model: {model}")

    def chat(self, prompt: str, temperature: float = 0.3) -> str:
        """
        Send a prompt to Gemini and return the reply.
        """
        response = self.model.generate_content(
            prompt,
            generation_config={"temperature": temperature}
        )
        return response.text.strip()


# -------------------------------
# Example Usage
# -------------------------------
if __name__ == "__main__":
    client = GeminiClient(model="gemini-1.5-flash")  # or "gemini-1.5-pro"
    reply = client.chat("Write a funny haiku about debugging code.")
    print("\n🤖 Gemini Reply:\n", reply)
