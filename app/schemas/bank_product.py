from pydantic import BaseModel
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

class BankProductBase(BaseModel):
    product_code: str
    product_name: str
    product_type: str
    bank_name: str
    interest_rate: Decimal
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    term_months: Optional[int] = None
    risk_level: int
    product_data: Optional[Dict[str, Any]] = None

class BankProductCreate(BankProductBase):
    pass

class BankProductUpdate(BaseModel):
    product_name: Optional[str] = None
    interest_rate: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    term_months: Optional[int] = None
    risk_level: Optional[int] = None
    product_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class BankProductResponse(BankProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class BankProductFilter(BaseModel):
    """은행 상품 필터링용"""
    product_type: Optional[str] = None
    bank_name: Optional[str] = None
    min_interest_rate: Optional[Decimal] = None
    max_interest_rate: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    risk_level: Optional[int] = None
    is_active: Optional[bool] = True
