from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from pycountry import countries

class CareCentreBase(BaseModel):
    name: str = Field(..., description="Name of the care centre")
    country_code: str = Field(..., description="Country code (ISO 3166-1 alpha-3) where the care centre is located")
    address: str = Field(..., description="Address of the care centre")
    postal_code: Optional[str] = Field(None, description="Postal code of the care centre")
    contact_no: Optional[str] = Field(None, description="Contact number of the care centre")
    email: Optional[str] = Field(None, description="Email address of the care centre")
    no_of_devices_avail: int = Field(..., description="Number of devices available at the care centre")

    # To be reconsider
    working_day: Optional[str] = Field(None, description="Working days of the care centre (e.g., 'Monday')")
    opening_hours: Optional[str] = Field(None, description="Opening hours of the care centre (e.g., '09:00 AM')")
    closing_hours: Optional[str] = Field(None, description="Closing hours of the care centre (e.g., '05:00 PM')")
    #===
    remarks: Optional[str] = Field(None, description="Additional remarks about the care centre")

    @model_validator(mode='after')
    def validate_country(self):
        if self.country not in [country.name for country in countries]:
            raise ValueError("Invalid country name provided.")
        return self
    
class CareCentreCreate(CareCentreBase):
    created_by_id: str = Field(..., description="ID of the user who created this care centre")

class CareCentreUpdate(CareCentreBase):
    modified_by_id: str = Field(..., description="ID of the user who last modified this care centre")
    id: int = Field(..., description="ID of the care centre to update")

class CareCentreResponse(CareCentreBase):
    id: int = Field(..., description="ID of the care centre")
    is_deleted: bool = Field(..., description="Is the care centre deleted")

    created_date: datetime = Field(..., description="Creation date of the care centre")
    modified_date: datetime = Field(..., description="Last modification date of the care centre")
    created_by_id: str = Field(..., description="ID of the user who created this care centre")
    modified_by_id: str = Field(..., description="ID of the user who last modified this care centre")
    class Config:
        from_attributes = True
        populate_by_name = True