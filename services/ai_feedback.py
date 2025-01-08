import openai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

def generate_feedback(swing_issue):
    # Using the ChatCompletion endpoint
    response = openai.ChatCompletion.create(
        # Using gpt-4o model
        model="gpt-4o",  
        messages=[
            {"role": "system", "content": "You are a helpful golf swing coach."},
            {"role": "user", "content": f"Provide actionable golf swing advice for the issue: {swing_issue}"}
        ],
        max_tokens=150,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()