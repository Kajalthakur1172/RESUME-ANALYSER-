import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
        model="gemini-3.8-flash",
    contents="Hinglish me ek line me batao: Python kya hai?",
)

print(response.text)