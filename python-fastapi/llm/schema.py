from pydantic import BaseModel,ValidationError,Field
from enum import StrEnum,Enum

class Input(BaseModel):
    id : str
    content: str = Field(...,min_length=1,max_length=2000)
    received_at: str

class Category(StrEnum):
    BILLING = "billing"
    BUG = "bug"
    FEATURE = "feature"
    OTHER = "other"

class Urgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Suggested_team(StrEnum):
    FINANCE = "finance"
    ENGINEERING = "engineering"
    PRODUCT = "product"
    SUPPORT_TRIAGE = "support_triage"

class Output(BaseModel):
    category : Category
    urgency : Urgency
    difficulty : Difficulty
    suggested_team : Suggested_team
    confidence : float = Field(ge=0.0,le=1.0)
    reason : str = Field(...,max_length=200)


