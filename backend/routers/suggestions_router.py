from fastapi import APIRouter, Depends, status
from backend.schemas import SuggestionCreate
from backend.database import db
from backend.auth import get_current_user, require_student

router = APIRouter(prefix="/api/suggestions", tags=["Student Suggestions"])

SUGGESTION_KEYWORDS = [
    'wifi', 'water', 'laundry', 'gym', 'library', 'cleaning',
    'food', 'mess', 'parking', 'ac', 'fan', 'security', 'lift', 'elevator', 'cooler'
]

def guess_suggestion_group(text: str) -> str:
    t = text.lower()
    for kw in SUGGESTION_KEYWORDS:
        if kw in t:
            return kw.capitalize()
    return "General"

@router.get("")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    """Retrieve all student suggestions."""
    return db.get_suggestions()

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_suggestion(req: SuggestionCreate, student: dict = Depends(require_student)):
    """Student only: submit an improvement suggestion."""
    group_tag = guess_suggestion_group(req.text)
    item = db.add_suggestion(
        user_id=student["id"],
        text=req.text,
        group_tag=group_tag
    )
    return item
