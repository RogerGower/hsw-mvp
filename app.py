from fastapi import FastAPI

app = FastAPI(title="Observation Service", version="0.0.1")

@app.get("/")
def root():
    return {"message": "Hello, Observation Service"}

@app.get("/health")
def health():
    return {"ok": True, "service": "observation", "version": "0.0.1"}
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional
import json, os

# your existing app = FastAPI(...) and routes stay above

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "prestart.schema.json")

class Check(BaseModel):
    area: str
    item: str
    status: str              # "Compliant" | "Non-compliant" | "N/A"
    note: Optional[str] = None
    photoUrl: Optional[str] = None

class Tyre(BaseModel):
    position: str            # e.g., "Front Left"
    treadDepthMm: Optional[float] = None
    condition: Optional[str] = None      # "OK" | "Damage" | "Needs Attention"
    pressureCheck: Optional[str] = None  # "Pass" | "Fail"

class Defect(BaseModel):
    natureOfFault: str
    workCarriedOutBy: Optional[str] = None
    dateWorkCompleted: Optional[str] = None  # ISO date
    comments: Optional[str] = None

class GeneralInfo(BaseModel):
    plantNumber: str
    date: str               # ISO date
    completedBy: str
    registrationDue: Optional[str] = None
    cofWofDue: Optional[str] = None
    hubKmReading: Optional[float] = None
    speedoReading: Optional[float] = None

class Prestart(BaseModel):
    generalInfo: GeneralInfo
    checks: List[Check]
    tyres: List[Tyre]
    defects: Optional[List[Defect]] = []

    @field_validator("checks")
    @classmethod
    def at_least_one_check(cls, v):
        if not v or len(v) < 1:
            raise ValueError("At least one check item is required")
        return v

PRESTART_STORE: List[Prestart] = []  # temp memory store (swap to DB later)

@app.get("/prestart/schema")
def get_prestart_schema():
    if not os.path.exists(SCHEMA_PATH):
        raise HTTPException(status_code=500, detail="Schema not found on server")
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

@app.get("/prestart/example")
def prestart_example():
    return {
        "generalInfo": {
            "plantNumber": "TRK-4502",
            "date": "2025-08-29",
            "completedBy": "K. James",
            "registrationDue": "2025-12-01",
            "cofWofDue": "2025-10-15",
            "speedoReading": 65723
        },
        "checks": [
            {"area":"In cab","item":"Seat Belts","status":"Compliant"},
            {"area":"Vehicle exterior","item":"Lights/Indicators","status":"Non-compliant","note":"LH indicator cracked"}
        ],
        "tyres": [
            {"position":"Front Left","treadDepthMm":6.0,"condition":"OK","pressureCheck":"Pass"},
            {"position":"Front Right","treadDepthMm":2.5,"condition":"Needs Attention","pressureCheck":"Fail"}
        ],
        "defects": [
            {"natureOfFault":"Cracked LH indicator lens","comments":"Replace ASAP"}
        ]
    }

@app.post("/prestart")
def submit_prestart(payload: Prestart):
    PRESTART_STORE.append(payload)
    return {"status": "stored", "count": len(PRESTART_STORE)}
