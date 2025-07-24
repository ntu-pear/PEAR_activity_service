from pydantic import BaseModel, Field, model_validator, ValidationInfo
from typing import Optional, Dict, Literal, get_args
from datetime import datetime
from pycountry import countries

# Set of valid country codes for quick lookup
VALID_COUNTRY_CODES = {country.alpha_3 for country in countries}
Day = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

class CareCentreBase(BaseModel):
    name: str = Field(..., description="Name of the care centre")
    country_code: str = Field(..., description="ISO 3166-1 alpha-3 country code", example="SGP")
    address: str = Field(..., description="Address of the care centre")
    postal_code: str = Field(..., description="Postal code of the care centre")
    contact_no: str = Field(..., description="Contact number")
    email: str = Field(..., description="Email address")
    no_of_devices_avail: int = Field(..., description="Number of devices available")

    working_hours: Dict[Day, Dict[str, Optional[str]]] = Field(
        ...,
        description="Working hours per day (both open and close must be specified or null)",
        example={
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": None, "close": None},
            "sunday": {"open": None, "close": None}
        }
    )
    remarks: Optional[str] = Field(None, description="Optional remarks")

    def _is_valid_time_format(self, time_str: str) -> bool:
            import re
            return bool(re.fullmatch(r"^([01][0-9]|2[0-3]):[0-5][0-9]$", time_str))
    
    @model_validator(mode="after")
    def validate_centre(self):
        country_code = self.country_code
        working_hours = self.working_hours

        if country_code not in VALID_COUNTRY_CODES:
            raise ValueError(f"Invalid country code: {country_code}. Must be 3 uppercase letters (ISO 3166-1 alpha-3)")

        missing_days = set(get_args(Day)) - set(working_hours)

        if missing_days:
            raise ValueError(f"Missing working hours for: {sorted(missing_days)}")

        errors = []
        for day, times in working_hours.items():
            open_time = times.get("open")
            close_time = times.get("close")

            if (open_time is None) != (close_time is None):
                errors.append(f"Both open and close must be specified or null for {day}")

            # Validate format if present
            open_valid = open_time is not None
            close_valid = close_time is not None
            if open_time and not self._is_valid_time_format(open_time):
                errors.append(f"Invalid time format for open on {day}: {open_time}")
                open_valid = False
            if close_time and not self._is_valid_time_format(close_time):
                errors.append(f"Invalid time format for close on {day}: {close_time}")
                close_valid = False
            if open_valid and close_valid and close_time <= open_time:         # Assuming close time does not pass midnight
                errors.append(f"Close time must be after open time for {day} ({open_time} >= {close_time})")

        if errors:
            raise ValueError("working_hours errors:\n" + "\n".join(errors))
        return self

class CareCentreCreate(CareCentreBase):
    created_by_id: str = Field(..., description="User ID who created the centre")

class CareCentreUpdate(CareCentreBase):
    id: int = Field(..., description="ID of the care centre to update")
    is_deleted: bool = Field(False, description="Is the care centre deleted")
    modified_by_id: str = Field(..., description="User ID who last modified the centre")
    modified_date: datetime = Field(None, description="Last modification timestamp")

class CareCentreResponse(CareCentreBase):
    id: int = Field(..., description="Care centre ID")
    is_deleted: bool = Field(..., description="Deletion status")
    created_date: datetime = Field(..., description="Timestamp of creation")
    modified_date: Optional[datetime] = Field(..., description="Last modification timestamp")
    created_by_id: str = Field(..., description="User ID who created it")
    modified_by_id: Optional[str] = Field(..., description="User ID who modified it")

    class Config:
        from_attributes = True
        populate_by_name = True
