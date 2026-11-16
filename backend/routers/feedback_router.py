from fastapi import APIRouter, Depends, status
from backend.schemas import FeedbackCreate
from backend.database import db
from backend.auth import get_current_user, require_student

router = APIRouter(prefix="/api/feedback", tags=["Food Feedback & Ratings"])

FEEDBACK_TAG_KEYWORDS = {
    "taste": ["bland", "tasteless", "spicy", "salty", "sweet", "taste"],
    "quantity": ["less", "small portion", "not enough", "quantity", "more food"],
    "quality": ["stale", "cold", "raw", "undercooked", "quality", "oily", "oil"],
    "repetition": ["repeat", "same", "again", "every day", "repetitive", "monotonous"]
}

def analyze_feedback_tags(text: str, stars: int) -> list:
    """Auto-detect tags based on feedback content and star rating."""
    t = (text or "").lower()
    tags = []
    for tag, keywords in FEEDBACK_TAG_KEYWORDS.items():
        if any(k in t for k in keywords):
            tags.append(tag)
    if not tags and stars >= 4:
        tags.append("positive")
    if not tags:
        tags.append("general")
    return tags

@router.get("")
async def get_feedback(current_user: dict = Depends(get_current_user)):
    """Retrieve recent student food feedback."""
    return db.get_feedback()

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feedback(req: FeedbackCreate, student: dict = Depends(require_student)):
    """Student only: submit rating and comment for today's meal."""
    tags = analyze_feedback_tags(req.comment, req.stars)
    feedback_item = db.add_feedback(
        user_id=student["id"],
        meal=req.meal,
        stars=req.stars,
        comment=req.comment,
        tags=tags
    )
    return feedback_item
