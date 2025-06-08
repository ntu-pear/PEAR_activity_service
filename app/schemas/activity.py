from datetime import datetime
from typing   import Optional
from pydantic import BaseModel, Field

class ActivityBase(BaseModel):
    title: str = Field(..., example="Morning Walk")
    description: Optional[str] = Field(None, example="Gentle stroll around the park")
    start_date: datetime
    end_date: Optional[datetime] = None
    is_fixed: bool = False
    is_compulsory: bool = False
    is_group: bool = False
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    min_people_required: Optional[int] = None

    class Config:
        orm_mode = True

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(ActivityBase):
    id: str

class Activity(ActivityBase):
    id: str
    created_date: datetime
    modified_date: datetime