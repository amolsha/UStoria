import os
import openai

ROUTER_API_KEY = os.getenv("REQUESTY_API_KEY") # Your key: sk-/N2/J...

if ROUTER_API_KEY is None:
    raise ValueError("ROUTER_API_KEY not found. Please check your .env file.")

try:
    # Initialize OpenAI client
    client = openai.OpenAI(
        api_key=ROUTER_API_KEY,
        base_url="https://router.requesty.ai/v1",
        default_headers={"Authorization": f"Bearer {ROUTER_API_KEY}"}
    )

    # Example request
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "user", "content": "Hello, who are you?"}]
    )

    # Check if the response is successful
    if not response.choices:
        raise Exception("No response choices found.")

    # Print the result
    print(response.choices[0].message.content)

except openai.OpenAIError as e:
    print(f"OpenAI API error: {e}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")