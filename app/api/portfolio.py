from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.models import User, BankProduct, YouthPolicy, UserPortfolio, RecommendationHistory
from app.schemas.user import UserProfile, UserCreate, UserResponse
from app.schemas.portfolio import (
    PortfolioRecommendation, 
    UserPortfolioCreate, 
    UserPortfolioResponse,
    PortfolioAnalysis
)
from app.services.msa_client import msa_client
from app.services.portfolio_recommender import portfolio_recommender
import os
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/recommend/{user_id}", response_model=dict)
async def recommend_portfolio(
    user_id: int,
    background_tasks: BackgroundTasks
):
    """AI 기반 포트폴리오 추천 (MSA 통신)"""
    try:
        # 1. 사용자 프로필 조회
        user_profile = await msa_client.get_user_profile(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 2. 사용 가능한 은행 상품 조회
        available_products = await msa_client.get_bank_products()
        
        if not available_products:
            raise HTTPException(
                status_code=404,
                detail="사용 가능한 은행 상품이 없습니다"
            )
        
        # 3. 사용자 연령에 맞는 청년 정책 조회
        youth_policies = await msa_client.get_youth_policies(user_profile.get('age', 25))
        
        # 4. AI 포트폴리오 추천 생성
        recommendation = await portfolio_recommender.generate_portfolio_recommendation(
            user_profile, available_products, youth_policies
        )
        
        # 5. 추천 결과를 사용자/포트폴리오 MSA로 전송 (백그라운드)
        background_tasks.add_task(
            send_recommendation_to_user_service,
            user_id,
            recommendation
        )
        
        return {
            "user_id": user_id,
            "recommendation": recommendation,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트폴리오 추천 실패: {e}")
        raise HTTPException(status_code=500, detail="포트폴리오 추천 중 오류가 발생했습니다")

async def send_recommendation_to_user_service(user_id: int, recommendation: dict):
    """추천 결과를 사용자/포트폴리오 MSA로 전송"""
    try:
        success = await msa_client.send_portfolio_recommendation(user_id, recommendation)
        
        if success:
            logger.info(f"포트폴리오 추천 전송 완료: 사용자 {user_id}")
        else:
            logger.error(f"포트폴리오 추천 전송 실패: 사용자 {user_id}")
            
    except Exception as e:
        logger.error(f"포트폴리오 추천 전송 중 오류: {e}")

async def save_recommendation_history(user_id: int, recommendation: PortfolioRecommendation, db: Session):
    """추천 히스토리 저장"""
    try:
        history = RecommendationHistory(
            user_id=user_id,
            recommendation_type="portfolio",
            recommendation_data=recommendation.dict(),
            ai_model_version="gemini-1.5-pro",
            confidence_score=recommendation.confidence_score
        )
        db.add(history)
        db.commit()
        logger.info(f"추천 히스토리 저장 완료: 사용자 {user_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"추천 히스토리 저장 실패: {e}")

@router.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """사용자 생성"""
    try:
        # 이메일 중복 확인
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")
        
        # 새 사용자 생성
        new_user = User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 생성 중 오류가 발생했습니다")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 정보 조회"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="사용자 조회 중 오류가 발생했습니다")

@router.post("/users/{user_id}/portfolio", response_model=UserPortfolioResponse)
async def create_user_portfolio(
    user_id: int,
    portfolio_item: UserPortfolioCreate,
    db: Session = Depends(get_db)
):
    """사용자 포트폴리오 아이템 생성"""
    try:
        # 사용자 존재 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # 상품 존재 확인
        product = db.query(BankProduct).filter(
            BankProduct.id == portfolio_item.bank_product_id
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="은행 상품을 찾을 수 없습니다")
        
        # 포트폴리오 아이템 생성
        new_portfolio_item = UserPortfolio(
            user_id=user_id,
            **portfolio_item.dict()
        )
        db.add(new_portfolio_item)
        db.commit()
        db.refresh(new_portfolio_item)
        
        return new_portfolio_item
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"포트폴리오 아이템 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="포트폴리오 아이템 생성 중 오류가 발생했습니다")

@router.get("/users/{user_id}/portfolio", response_model=List[UserPortfolioResponse])
async def get_user_portfolio(user_id: int, db: Session = Depends(get_db)):
    """사용자 포트폴리오 조회"""
    try:
        # 사용자 존재 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        portfolio_items = db.query(UserPortfolio).filter(
            UserPortfolio.user_id == user_id
        ).all()
        
        return portfolio_items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 포트폴리오 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="포트폴리오 조회 중 오류가 발생했습니다")

@router.get("/users/{user_id}/analysis", response_model=PortfolioAnalysis)
async def analyze_user_portfolio(user_id: int, db: Session = Depends(get_db)):
    """사용자 포트폴리오 분석"""
    try:
        # 사용자 포트폴리오 조회
        portfolio_items = db.query(UserPortfolio).filter(
            UserPortfolio.user_id == user_id
        ).all()
        
        if not portfolio_items:
            raise HTTPException(status_code=404, detail="포트폴리오가 없습니다")
        
        # 포트폴리오 분석 로직
        total_value = sum(float(item.investment_amount) for item in portfolio_items)
        total_return = 0.0
        risk_score = 0.0
        sector_allocation = {}
        
        for item in portfolio_items:
            # 상품 정보 조회
            product = db.query(BankProduct).filter(
                BankProduct.id == item.bank_product_id
            ).first()
            
            if product:
                # 예상 수익률 계산 (간단한 예시)
                expected_return = float(product.interest_rate) / 100 * float(item.investment_amount)
                total_return += expected_return
                
                # 리스크 점수 계산
                risk_score += float(product.risk_level) * float(item.allocation_percentage) / 100
                
                # 섹터별 배분 계산
                sector = product.product_type
                if sector in sector_allocation:
                    sector_allocation[sector] += float(item.allocation_percentage)
                else:
                    sector_allocation[sector] = float(item.allocation_percentage)
        
        # 분산투자 점수 계산
        diversification_score = min(100, len(sector_allocation) * 20)
        
        analysis = PortfolioAnalysis(
            total_value=Decimal(str(total_value)),
            total_return=Decimal(str(total_return)),
            risk_score=Decimal(str(risk_score)),
            diversification_score=Decimal(str(diversification_score)),
            sector_allocation=sector_allocation,
            risk_analysis={
                "overall_risk": "낮음" if risk_score < 2 else "보통" if risk_score < 4 else "높음",
                "diversification": "양호" if diversification_score > 60 else "개선 필요"
            },
            recommendations=[
                "포트폴리오가 잘 분산되어 있습니다" if diversification_score > 60 else "더 많은 상품으로 분산투자를 고려해보세요",
                "리스크 관리가 잘 되고 있습니다" if risk_score < 3 else "리스크를 줄이는 상품을 고려해보세요"
            ]
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"포트폴리오 분석 실패: {e}")
        raise HTTPException(status_code=500, detail="포트폴리오 분석 중 오류가 발생했습니다")
