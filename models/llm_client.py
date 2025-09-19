from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def complete(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or whichever you want
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()
