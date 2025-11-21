import os
import random
from datetime import datetime, timezone, date
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Routine, Task

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Quotes logic ---
QUOTES = [
    "Small steps every morning lead to big changes.",
    "Discipline is choosing what you want most over what you want now.",
    "Today is a new chance to become who you want to be.",
    "Rise with purpose. Act with intention.",
    "Your future is built in the morning.",
    "Win the morning, win the day.",
    "Consistency beats intensity.",
    "You don’t have to be extreme, just consistent.",
    "One good habit can change everything.",
    "Start where you are. Use what you have. Do what you can.",
]


def quote_of_the_day() -> str:
    # Deterministic daily quote based on date
    today = date.today().toordinal()
    return QUOTES[today % len(QUOTES)]


# --- Models for updating ---
class RoutineCreate(BaseModel):
    client_id: str
    title: str
    wake_time: Optional[str] = None
    reminders_enabled: bool = True
    days: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    tasks: List[Task] = []


class RoutineUpdate(BaseModel):
    title: Optional[str] = None
    wake_time: Optional[str] = None
    reminders_enabled: Optional[bool] = None
    days: Optional[List[str]] = None
    tasks: Optional[List[Task]] = None


@app.get("/")
def root():
    return {"message": "Morning Routine API running", "quote": quote_of_the_day()}


@app.get("/api/quote")
def get_quote():
    return {"quote": quote_of_the_day()}


@app.post("/api/routines")
def create_routine(payload: RoutineCreate):
    try:
        rid = create_document("routine", payload)
        return {"id": rid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/routines")
def list_routines(client_id: str):
    try:
        docs = get_documents("routine", {"client_id": client_id})
        # Convert ObjectId and datetime fields to strings
        for d in docs:
            d["_id"] = str(d.get("_id"))
            for k in ["created_at", "updated_at"]:
                if k in d and isinstance(d[k], datetime):
                    d[k] = d[k].isoformat()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/routines/{routine_id}")
def update_routine(routine_id: str, payload: RoutineUpdate):
    try:
        if db is None:
            raise Exception("Database not available")
        update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
        update_data["updated_at"] = datetime.now(timezone.utc)
        res = db["routine"].update_one({"_id": __import__("bson").ObjectId(routine_id)}, {"$set": update_data})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Routine not found")
        return {"updated": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/routines/{routine_id}")
def delete_routine(routine_id: str):
    try:
        if db is None:
            raise Exception("Database not available")
        res = db["routine"].delete_one({"_id": __import__("bson").ObjectId(routine_id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Routine not found")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
