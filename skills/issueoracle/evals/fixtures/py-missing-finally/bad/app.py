from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

app = FastAPI()
engine = create_engine("sqlite:///test.db")


@app.get("/users")
def get_users():
    session = Session(engine)
    result = session.query("SELECT * FROM users").all()
    return {"users": result}
