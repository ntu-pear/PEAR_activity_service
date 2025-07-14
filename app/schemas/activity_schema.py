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
    is_deleted: bool = Field(False, alias="isDeleted")
    created_date: datetime = Field(..., alias="createdDate")
    modified_date: datetime = Field(..., alias="modifiedDate")
    created_by_id: Optional[str] = Field(None, alias="createdById")
    modified_by_id: Optional[str] = Field(None, alias="modifiedById")

    class Config:
        from_attributes = True    
        populate_by_name = True