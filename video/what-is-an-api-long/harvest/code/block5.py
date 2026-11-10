# main.py
from fastapi import FastAPI, HTTPException

app = FastAPI()

# In real systems this would be a database call — see Part 4.
FAKE_USERS_DB = {
    42: {"id": 42, "name": "Priya Sharma", "email": "priya@example.com"}
}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    """The API contract: given a user_id, return that user's public profile."""
    user = FAKE_USERS_DB.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
