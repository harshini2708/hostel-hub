from fastapi import APIRouter, Depends, HTTPException, status
from backend.schemas import PollCreate, PollVoteRequest
from backend.database import db
from backend.auth import get_current_user, require_warden, require_student

router = APIRouter(prefix="/api/polls", tags=["Hostel Polls & Voting"])

@router.get("")
async def get_polls(current_user: dict = Depends(get_current_user)):
    """Retrieve all active polls with options, vote counts, and user's voted status."""
    return db.get_polls(user_id=current_user["id"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_poll(req: PollCreate, warden: dict = Depends(require_warden)):
    """Warden only: create a new hostel poll."""
    clean_options = [opt.strip() for opt in req.options if opt.strip()]
    if len(clean_options) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A poll must have at least two non-empty options."
        )

    poll = db.create_poll(
        question=req.question,
        options=clean_options,
        created_by=warden["id"]
    )
    return poll

@router.post("/{poll_id}/vote")
async def vote_poll(poll_id: int, req: PollVoteRequest, student: dict = Depends(require_student)):
    """
    Student only: cast vote in a poll.
    Strictly prevents duplicate voting using unique database constraints.
    """
    try:
        res = db.vote_poll(
            poll_id=poll_id,
            option_id=req.option_id,
            user_id=student["id"]
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
