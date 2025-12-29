from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict

class Company(BaseModel):
    ico: str = Field(..., description="IČO (company registration number or equivalent)")
    name: str = Field(..., description="Company name")
    address: str = Field(..., description="Registered address")
    status: str = Field(..., description="Company status (e.g., ACTIVE, DISSOLVED)")
    raw_data: Optional[Dict] = Field(default=None, description="Additional raw data for visualization")

    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)
