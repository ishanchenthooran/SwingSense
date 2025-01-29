import openai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)  

def generate_feedback(swing_issue):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", 
                "content": (
                    "You are an experienced golf swing coach specializing in helping amateur golfers improve their swing. "
                    "Provide clear, step-by-step, and easy-to-follow advice tailored to the user's issue. "
                    "Your response should focus on simple adjustments, practical drills, and common mistakes to avoid. "
                    "Explain concepts in a way that is easy to understand, avoiding overly technical jargon unless necessary. "
                    "Whenever possible, include real-world analogies or visual cues to help the golfer grasp the adjustment."
                )   
            },
            {"role": "user", 
                "content": f"My golf swing issue is: {swing_issue}. "
                   "Please break down the cause of this issue in simple terms and provide specific, actionable steps, "
                   "effective drills, and key focus points to improve my swing."
            }
        ],
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].message.content.strip() 