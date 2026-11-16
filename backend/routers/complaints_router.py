from fastapi import APIRouter, Depends, HTTPException, status
from backend.schemas import ComplaintCreate
from backend.database import db
from backend.auth import get_current_user, require_warden, require_student

router = APIRouter(prefix="/api/complaints", tags=["Complaints & Status Tracking"])

COMPLAINT_KEYWORDS = {
    "Food": ["food", "mess", "meal", "rice", "curry", "dal", "veg", "sabzi", "taste"],
    "Water": ["water", "tap", "leak", "supply", "cooler"],
    "Electricity": ["electricity", "power", "light", "fan", "socket", "wire", "spark"],
    "WiFi": ["wifi", "wi-fi", "internet", "network", "router"],
    "Cleanliness": ["clean", "dirty", "trash", "garbage", "washroom", "toilet", "bathroom"],
    "Maintenance": ["door", "window", "furniture", "bed", "repair", "broken", "cupboard", "lock"]
}
URGENT_WORDS = ["urgent", "emergency", "no water", "no power", "not working", "spark", "fire", "safety", "broken lock"]
MINOR_WORDS = ["minor", "small", "sometimes", "occasionally"]

def guess_complaint_category(text: str) -> str:
    t = text.lower()
    for cat, words in COMPLAINT_KEYWORDS.items():
        if any(w in t for w in words):
            return cat
    return "Maintenance"

def guess_complaint_priority(text: str) -> str:
    t = text.lower()
    if any(w in t for w in URGENT_WORDS):
        return "High"
    if any(w in t for w in MINOR_WORDS):
        return "Low"
    return "Medium"

@router.get("")
async def get_complaints(current_user: dict = Depends(get_current_user)):
    """
    STRICT PRIVACY ENFORCEMENT:
    - If user is a student: returns ONLY complaints submitted by this student.
    - If user is warden: returns all complaints across the entire hostel with student names & rooms.
    """
    return db.get_complaints(current_user=current_user)

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_complaint(req: ComplaintCreate, student: dict = Depends(require_student)):
    """Student only: submit a new private complaint."""
    category = req.category or guess_complaint_category(req.description)
    priority = req.priority or guess_complaint_priority(req.description)

    complaint = db.add_complaint(
        user_id=student["id"],
        category=category,
        description=req.description,
        priority=priority
    )
    return complaint

@router.patch("/{complaint_id}/view")
async def mark_viewed(complaint_id: int, warden: dict = Depends(require_warden)):
    """Warden only: mark a complaint as viewed/acknowledged."""
    res = db.mark_complaint_viewed(complaint_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")
    return res

@router.patch("/{complaint_id}/resolve")
async def mark_resolved(complaint_id: int, warden: dict = Depends(require_warden)):
    """Warden only: mark a complaint as resolved."""
    res = db.mark_complaint_resolved(complaint_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")
    return res
