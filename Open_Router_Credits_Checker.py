import requests
import json
import os

OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER_KEY")

response = requests.get(
  url="https://openrouter.ai/api/v1/key",
  headers={
    "Authorization": f"Bearer {OPEN_ROUTER_KEY}"
  }
)
print(json.dumps(response.json(), indent=2))