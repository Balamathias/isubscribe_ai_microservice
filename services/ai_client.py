import os
from dotenv import load_dotenv

load_dotenv()

from google import genai
from openai import OpenAI

google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

openai_client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
