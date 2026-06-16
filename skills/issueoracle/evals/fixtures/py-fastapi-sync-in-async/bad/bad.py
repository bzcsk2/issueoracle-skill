import time
from fastapi import FastAPI

app = FastAPI()


@app.get("/users")
async def get_users():
    time.sleep(2)
    return {"users": []}
