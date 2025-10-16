"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from typing import List, Dict, Any

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

# Add a new in-memory structure for uploaded documents and verification status
activity_documents: Dict[str, List[Dict[str, Any]]] = {}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}


@app.post("/activities/{activity_name}/upload")
def upload_document(activity_name: str, email: str = Form(...), file: UploadFile = File(...), score: int = Form(...)):
    """Upload a certificate or score for an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
    # Store file metadata and score (not saving file contents for simplicity)
    doc = {
        "email": email,
        "filename": file.filename,
        "content_type": file.content_type,
        "score": score,
        "verified": False
    }
    activity_documents.setdefault(activity_name, []).append(doc)
    return {"message": f"Uploaded {file.filename} for {email} in {activity_name}"}


@app.get("/activities/{activity_name}/documents")
def get_activity_documents(activity_name: str):
    """Get all uploaded documents for an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity_documents.get(activity_name, [])


@app.post("/activities/{activity_name}/verify")
def verify_document(activity_name: str, email: str, filename: str):
    """Admin verifies a document for an activity"""
    docs = activity_documents.get(activity_name, [])
    for doc in docs:
        if doc["email"] == email and doc["filename"] == filename:
            doc["verified"] = True
            return {"message": f"Verified {filename} for {email} in {activity_name}"}
    raise HTTPException(status_code=404, detail="Document not found")


@app.get("/activities/sorted")
def get_sorted_activities(sort_by: str = Query("name", enum=["name", "participants", "score"]), descending: bool = Query(False)):
    """Get activities sorted by name, number of participants, or average score"""
    def avg_score(activity_name):
        docs = activity_documents.get(activity_name, [])
        scores = [doc["score"] for doc in docs if doc.get("verified")]
        return sum(scores) / len(scores) if scores else 0
    items = list(activities.items())
    if sort_by == "name":
        items.sort(key=lambda x: x[0], reverse=descending)
    elif sort_by == "participants":
        items.sort(key=lambda x: len(x[1]["participants"]), reverse=descending)
    elif sort_by == "score":
        items.sort(key=lambda x: avg_score(x[0]), reverse=descending)
    return [{"name": k, **v} for k, v in items]


@app.get("/activities/{activity_name}/participants/sorted")
def get_sorted_participants(activity_name: str, sort_by: str = Query("name", enum=["name", "score"]), descending: bool = Query(False)):
    """Get participants of an activity sorted by name or score"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")
    participants = activities[activity_name]["participants"]
    docs = activity_documents.get(activity_name, [])
    # Build participant info with scores
    info = []
    for email in participants:
        score = None
        for doc in docs:
            if doc["email"] == email and doc.get("verified"):
                score = doc["score"]
                break
        info.append({"email": email, "score": score})
    if sort_by == "name":
        info.sort(key=lambda x: x["email"], reverse=descending)
    elif sort_by == "score":
        info.sort(key=lambda x: (x["score"] if x["score"] is not None else 0), reverse=descending)
    return info
