from pydantic import BaseModel, EmailStr
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    age: int
    income_level: str
    total_assets: Decimal
    investment_preference: str
    interest_sectors: Optional[List[str]] = None
    risk_tolerance: int

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    income_level: Optional[str] = None
    total_assets: Optional[Decimal] = None
    investment_preference: Optional[str] = None
    interest_sectors: Optional[List[str]] = None
    risk_tolerance: Optional[int] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    """사용자 프로필 분석용"""
    age: int
    income_level: str
    total_assets: Decimal
    investment_preference: str
    interest_sectors: List[str]
    risk_tolerance: int
    investment_goal: Optional[str] = None  # 투자 목표
    investment_horizon: Optional[str] = None  # 투자 기간
