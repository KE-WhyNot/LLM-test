from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

class PortfolioItem(BaseModel):
    """포트폴리오 아이템"""
    bank_product_id: int
    product_name: str
    bank_name: str
    product_type: str
    allocation_percentage: Decimal
    investment_amount: Decimal
    expected_return: Optional[Decimal] = None
    risk_level: int

class PortfolioRecommendation(BaseModel):
    """포트폴리오 추천"""
    user_id: int
    total_investment_amount: Decimal
    portfolio_items: List[PortfolioItem]
    expected_total_return: Decimal
    total_risk_score: Decimal
    recommendation_reason: str
    confidence_score: Optional[Decimal] = None
    created_at: datetime

class UserPortfolioCreate(BaseModel):
    """사용자 포트폴리오 생성"""
    user_id: int
    bank_product_id: int
    allocation_percentage: Decimal
    investment_amount: Decimal

class UserPortfolioUpdate(BaseModel):
    """사용자 포트폴리오 수정"""
    allocation_percentage: Optional[Decimal] = None
    investment_amount: Optional[Decimal] = None

class UserPortfolioResponse(BaseModel):
    """사용자 포트폴리오 응답"""
    id: int
    user_id: int
    bank_product_id: int
    allocation_percentage: Decimal
    investment_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PortfolioAnalysis(BaseModel):
    """포트폴리오 분석"""
    total_value: Decimal
    total_return: Decimal
    risk_score: Decimal
    diversification_score: Decimal
    sector_allocation: Dict[str, Decimal]
    risk_analysis: Dict[str, Any]
    recommendations: List[str]
