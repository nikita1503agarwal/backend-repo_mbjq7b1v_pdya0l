"""
Database Schemas for Cueron Client App

Each Pydantic model below represents a MongoDB collection. The collection name
is the lowercase of the class name. For example: class Job -> collection "job".

These schemas are used for validation and to keep a consistent shape for data
stored in MongoDB.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Core entities
class Site(BaseModel):
    name: str = Field(..., description="Site/Location name")
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class Asset(BaseModel):
    site_id: str = Field(..., description="Reference to site _id (string)")
    name: str
    type: str
    status: Literal["active", "inactive", "maintenance"] = "active"
    serial_number: Optional[str] = None
    model: Optional[str] = None

class JobRequest(BaseModel):
    service_type: Literal["AMC", "Repair", "Installation", "Emergency"]
    site_id: str
    asset_ids: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    schedule: Optional[datetime] = Field(None, description="Requested datetime, optional")
    media_urls: List[str] = Field(default_factory=list)

class Job(BaseModel):
    customer_id: Optional[str] = None
    service_type: Literal["AMC", "Repair", "Installation", "Emergency"]
    status: Literal["New", "Assigned", "Travelling", "In Progress", "Closed"] = "New"
    site_id: str
    asset_ids: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    assigned_technician_id: Optional[str] = None
    timeline: List[dict] = Field(default_factory=list, description="Status updates with timestamps")

class Invoice(BaseModel):
    job_id: str
    amount: float
    due_date: Optional[datetime] = None
    status: Literal["unpaid", "paid", "overdue"] = "unpaid"
    line_items: List[dict] = Field(default_factory=list)

class Feedback(BaseModel):
    job_id: str
    rating_overall: int = Field(..., ge=1, le=5)
    rating_engineer: Optional[int] = Field(None, ge=1, le=5)
    comments: Optional[str] = None
    request_follow_up: bool = False

class User(BaseModel):
    org_name: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Literal["admin", "manager", "viewer", "technician", "customer"] = "customer"

# Optional: basic analytic snapshot document
class AnalyticsSnapshot(BaseModel):
    month: str  # YYYY-MM
    jobs_count: int
    downtime_hours: float
    engineer_performance: List[dict] = Field(default_factory=list)
