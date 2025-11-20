import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Site, Asset, JobRequest, Job, Invoice, Feedback

app = FastAPI(title="Cueron Client API", version="0.1.0")

# CORS
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class Message(BaseModel):
    message: str


def _collection(name: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    return db[name]


# Root and health
@app.get("/", response_model=Message)
async def read_root():
    return {"message": "Hello from Cueron Backend!"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/echo")
async def echo(payload: dict):
    return {"received": payload, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Set"
            try:
                response["collections"] = db.list_collection_names()
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "❌ Not Initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"
    return response


# ---- Sites ----
@app.post("/sites")
async def create_site(site: Site):
    inserted_id = create_document("site", site)
    return {"_id": inserted_id}


@app.get("/sites")
async def list_sites(limit: Optional[int] = 100):
    docs = get_documents("site", {}, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs


# ---- Assets ----
@app.post("/assets")
async def create_asset(asset: Asset):
    # Ensure site exists
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    site = db["site"].find_one({"_id": __import__("bson").ObjectId(asset.site_id)}) if asset.site_id else None
    # Optional: skip strict validation to keep simple; if site missing, still allow with given id string
    inserted_id = create_document("asset", asset)
    return {"_id": inserted_id}


@app.get("/assets")
async def list_assets(limit: Optional[int] = 200, site_id: Optional[str] = None):
    filt = {"site_id": site_id} if site_id else {}
    docs = get_documents("asset", filt, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs


# ---- Jobs ----
@app.post("/jobs")
async def create_job(req: JobRequest):
    job = Job(
        customer_id=None,
        service_type=req.service_type,
        site_id=req.site_id,
        asset_ids=req.asset_ids,
        description=req.description,
        scheduled_for=req.schedule,
        assigned_technician_id=None,
        timeline=[{"status": "New", "at": datetime.now(timezone.utc).isoformat()}],
    )
    inserted_id = create_document("job", job)
    return {"job_id": inserted_id, "status": "New"}


@app.get("/jobs")
async def list_jobs(limit: Optional[int] = 200, status: Optional[str] = None):
    filt = {"status": status} if status else {}
    docs = get_documents("job", filt, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs


# ---- Invoices ----
@app.post("/invoices")
async def create_invoice(invoice: Invoice):
    inserted_id = create_document("invoice", invoice)
    return {"_id": inserted_id}


@app.get("/invoices")
async def list_invoices(limit: Optional[int] = 200, status: Optional[str] = None):
    filt = {"status": status} if status else {}
    docs = get_documents("invoice", filt, limit)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs


# ---- Feedback ----
@app.post("/feedback")
async def submit_feedback(feedback: Feedback):
    inserted_id = create_document("feedback", feedback)
    return {"_id": inserted_id}


# Schema exposure for tooling (optional)
@app.get("/schema")
async def schema_info():
    return {
        "collections": [
            "site",
            "asset",
            "job",
            "invoice",
            "feedback",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
