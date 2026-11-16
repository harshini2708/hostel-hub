from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# ==================== AUTH SCHEMAS ====================
class UserRegister(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    room_number: Optional[str] = None
    role: str = "student" # 'student' or 'warden'

class UserLogin(BaseModel):
    email: str = Field(..., min_length=3)
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    room_number: Optional[str] = None
    role: str

# ==================== MENU SCHEMAS ====================
class MenuItemCreate(BaseModel):
    day: str = Field(..., pattern="^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)$")
    dish: str = Field(..., min_length=2)

class MenuLockRequest(BaseModel):
    locked: bool

# ==================== FEEDBACK SCHEMAS ====================
class FeedbackCreate(BaseModel):
    meal: str = Field(..., pattern="^(Breakfast|Lunch|Dinner)$")
    stars: int = Field(..., ge=1, le=5)
    comment: Optional[str] = ""

# ==================== COMPLAINTS SCHEMAS ====================
class ComplaintCreate(BaseModel):
    category: str
    description: str = Field(..., min_length=4)
    priority: str = Field(default="Medium", pattern="^(High|Medium|Low)$")

# ==================== POLLS SCHEMAS ====================
class PollCreate(BaseModel):
    question: str = Field(..., min_length=5)
    options: List[str] = Field(..., min_items=2, max_items=4)

class PollVoteRequest(BaseModel):
    option_id: int

# ==================== SUGGESTIONS SCHEMAS ====================
class SuggestionCreate(BaseModel):
    text: str = Field(..., min_length=4)
