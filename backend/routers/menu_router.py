from fastapi import APIRouter, Depends, HTTPException, status
from backend.schemas import MenuItemCreate, MenuLockRequest
from backend.database import db
from backend.auth import get_current_user, require_warden, require_student

router = APIRouter(prefix="/api/menu", tags=["Weekly Mess Menu"])

@router.get("")
async def get_menu(current_user: dict = Depends(get_current_user)):
    """Retrieve weekly menu items, total votes, lock state, and user's voted status."""
    return db.get_menu_items(user_id=current_user["id"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def add_menu_item(req: MenuItemCreate, warden: dict = Depends(require_warden)):
    """Warden only: add a new dish to the weekly menu."""
    item = db.add_menu_item(day=req.day, dish=req.dish)
    return item

@router.post("/{item_id}/vote")
async def vote_menu_item(item_id: int, student: dict = Depends(require_student)):
    """
    Student only: toggle vote on a menu dish.
    Guarantees no duplicate votes via database unique constraint.
    """
    menu_data = db.get_menu_items(user_id=student["id"])
    if menu_data.get("menuLocked"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The menu has been locked by the warden. Voting is closed."
        )

    res = db.toggle_menu_vote(menu_item_id=item_id, user_id=student["id"])
    return res

@router.post("/lock")
async def lock_menu(warden: dict = Depends(require_warden)):
    """Warden only: lock and publish the menu."""
    db.set_menu_locked(True)
    return {"message": "Menu locked and published successfully.", "menuLocked": True}

@router.post("/unlock")
async def unlock_menu(warden: dict = Depends(require_warden)):
    """Warden only: reopen menu for voting/editing."""
    db.set_menu_locked(False)
    return {"message": "Menu reopened for editing.", "menuLocked": False}
