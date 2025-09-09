from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, DECIMAL, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class User(Base):
    """사용자 정보"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    income_level = Column(String(50), nullable=False)  # 소득분위
    total_assets = Column(DECIMAL(15, 2), nullable=False)  # 총 자산
    investment_preference = Column(String(50), nullable=False)  # 투자성향 (보수적, 중립, 공격적)
    interest_sectors = Column(JSON, nullable=True)  # 관심 종목 (IT, 조선, 금융 등)
    risk_tolerance = Column(Integer, nullable=False)  # 리스크 허용도 (1-10)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    portfolios = relationship("UserPortfolio", back_populates="user")
    recommendation_history = relationship("RecommendationHistory", back_populates="user")

class BankProduct(Base):
    """은행 상품 정보"""
    __tablename__ = "bank_products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(255), nullable=False)
    product_type = Column(String(50), nullable=False)  # 예금, 적금, 대출 등
    bank_name = Column(String(100), nullable=False)
    interest_rate = Column(DECIMAL(5, 2), nullable=False)  # 금리
    min_amount = Column(DECIMAL(15, 2), nullable=True)  # 최소 금액
    max_amount = Column(DECIMAL(15, 2), nullable=True)  # 최대 금액
    term_months = Column(Integer, nullable=True)  # 기간 (월)
    risk_level = Column(Integer, nullable=False)  # 리스크 레벨 (1-5)
    product_data = Column(JSON, nullable=True)  # 추가 상품 정보
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    portfolios = relationship("UserPortfolio", back_populates="bank_product")

class YouthPolicy(Base):
    """청년 정책 정보"""
    __tablename__ = "youth_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_code = Column(String(50), unique=True, nullable=False)
    policy_name = Column(String(255), nullable=False)
    target_age_min = Column(Integer, nullable=False)  # 대상 연령 최소
    target_age_max = Column(Integer, nullable=False)  # 대상 연령 최대
    benefit_amount = Column(DECIMAL(15, 2), nullable=True)  # 혜택 금액
    requirements = Column(Text, nullable=True)  # 신청 요건
    application_period = Column(String(100), nullable=True)  # 신청 기간
    policy_data = Column(JSON, nullable=True)  # 추가 정책 정보
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserPortfolio(Base):
    """사용자 포트폴리오"""
    __tablename__ = "user_portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bank_product_id = Column(Integer, ForeignKey("bank_products.id"), nullable=False)
    allocation_percentage = Column(DECIMAL(5, 2), nullable=False)  # 배분 비율
    investment_amount = Column(DECIMAL(15, 2), nullable=False)  # 투자 금액
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    user = relationship("User", back_populates="portfolios")
    bank_product = relationship("BankProduct", back_populates="portfolios")

class RecommendationHistory(Base):
    """추천 히스토리"""
    __tablename__ = "recommendation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recommendation_type = Column(String(50), nullable=False)  # portfolio, policy 등
    recommendation_data = Column(JSON, nullable=False)  # 추천 데이터
    ai_model_version = Column(String(50), nullable=True)  # AI 모델 버전
    confidence_score = Column(DECIMAL(3, 2), nullable=True)  # 신뢰도 점수
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    user = relationship("User", back_populates="recommendation_history")
