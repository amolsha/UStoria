import os
import httpx

API_KEY = os.getenv("OPENAI_API_KEY")

async def list_models():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.openai.com/v1/models", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        models = [m["id"] for m in data["data"]]
        for model in sorted(models):
            print(model)

import asyncio
asyncio.run(list_models())