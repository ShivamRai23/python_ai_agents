import os
import google.generativeai as genai

# Works if you set GOOGLE_API_KEY in environment
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Hello Gemini, are you working?")
print(response.text)



