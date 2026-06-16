import asyncio
from fastapi import FastAPI

app = FastAPI()


@app.get("/users")
async def get_users():
    await asyncio.sleep(2)
    return {"users": []}
