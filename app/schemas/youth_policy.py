from pydantic import BaseModel
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

class YouthPolicyBase(BaseModel):
    policy_code: str
    policy_name: str
    target_age_min: int
    target_age_max: int
    benefit_amount: Optional[Decimal] = None
    requirements: Optional[str] = None
    application_period: Optional[str] = None
    policy_data: Optional[Dict[str, Any]] = None

class YouthPolicyCreate(YouthPolicyBase):
    pass

class YouthPolicyUpdate(BaseModel):
    policy_name: Optional[str] = None
    target_age_min: Optional[int] = None
    target_age_max: Optional[int] = None
    benefit_amount: Optional[Decimal] = None
    requirements: Optional[str] = None
    application_period: Optional[str] = None
    policy_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class YouthPolicyResponse(YouthPolicyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
