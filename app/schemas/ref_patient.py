from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class RefPatientBase(BaseModel):
    """Base schema for ref patient with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Patient name")
    preferred_name: Optional[str] = Field(None, max_length=255, description="Patient's preferred name")
    update_bit: str = Field(default="1", pattern="^[01]$", description="Update flag: 0 or 1")
    start_date: datetime = Field(..., description="Patient start date")
    end_date: Optional[datetime] = Field(None, description="Patient end date")
    is_active: str = Field(default="1", pattern="^[01]$", description="Active status: 0 or 1")


class RefPatientCreate(RefPatientBase):
    """Schema for creating a new ref patient - includes id for message queue operations"""
    id: int = Field(..., description="Patient ID from source system")
    is_deleted: str = Field(default="0", pattern="^[01]$", description="Deletion status: 0 or 1")
    created_date: datetime = Field(..., description="Creation timestamp")
    modified_date: datetime = Field(..., description="Last modification timestamp")
    created_by_id: str = Field(..., max_length=50, description="Creator user/service ID")
    modified_by_id: str = Field(..., max_length=50, description="Last modifier user/service ID")


class RefPatientUpdate(BaseModel):
    """Schema for updating an existing ref patient"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    preferred_name: Optional[str] = Field(None, max_length=255)
    update_bit: Optional[str] = Field(None, pattern="^[01]$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[str] = Field(None, pattern="^[01]$")
    is_deleted: Optional[str] = Field(None, pattern="^[01]$")
    modified_date: datetime = Field(..., description="Last modification timestamp")
    modified_by_id: str = Field(..., max_length=50, description="Modifier user/service ID")


class RefPatientDelete(BaseModel):
    """Schema for soft-deleting a ref patient"""
    modified_date: datetime = Field(..., description="Deletion timestamp")
    modified_by_id: str = Field(..., max_length=50, description="Deleter user/service ID")


class RefPatient(RefPatientBase):
    """Schema for ref patient response"""
    id: int
    is_deleted: str = Field(default="0", pattern="^[01]$")
    created_date: datetime
    modified_date: datetime
    created_by_id: str
    modified_by_id: str
    
    model_config = ConfigDict(from_attributes=True)
