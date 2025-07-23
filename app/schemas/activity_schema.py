from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ActivityBase(BaseModel):
    title: str = Field(..., example="Morning Walk")
    description: Optional[str] = Field(
        None, example="Gentle stroll around the garden"
    )

    class Config:
        populate_by_name = True

class ActivityCreate(ActivityBase):
    pass

class ActivityRead(ActivityBase):
    id: int
    is_deleted: bool = Field(False, description="Is the Activity deleted")
    created_date: datetime = Field(..., description="Creation date of the Activity")
    modified_date: datetime = Field(..., description="Last modification date of the Activity")
    created_by_id: Optional[str] = Field(None, description="ID of the user who created this activity")
    modified_by_id: Optional[str] = Field(None, description="ID of the user who last modified this activity")

    class Config:
        from_attributes = True    
        populate_by_name = True

class ActivityUpdate(ActivityBase):
    id: int = Field(..., description="ID of the Activity to update")
    is_deleted: bool = Field(..., description="Is the Activity deleted")
    modified_by_id: Optional[str] = Field(None, description="ID of the user who last modified this activity")