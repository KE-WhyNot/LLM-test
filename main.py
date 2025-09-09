from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database.connection import get_db, engine
from app.database.models import Base
from app.api import bank_products, youth_policies, portfolio
import logging
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="금융 포트폴리오 추천 API",
    description="은행 상품과 청년 정책을 활용한 AI 기반 포트폴리오 추천 서비스",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 생성
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise

# API 라우터 등록
app.include_router(bank_products.router, prefix="/api/v1/bank-products", tags=["은행상품"])
app.include_router(youth_policies.router, prefix="/api/v1/youth-policies", tags=["청년정책"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["포트폴리오"])

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "금융 포트폴리오 추천 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    from app.services.msa_client import msa_client
    from app.services.portfolio_recommender import portfolio_recommender
    from app.services.ai_preprocessing import ai_preprocessing_service
    
    # MSA 서비스들 헬스 체크
    msa_health = await msa_client.health_check()
    
    return {
        "status": "healthy", 
        "message": "AI 서비스 정상 운영 중",
        "msa_services": msa_health,
        "ai": {
            "gemini": portfolio_recommender.get_status(),
            "vertex": ai_preprocessing_service.get_status()
        }
    }

@app.get("/sample-data")
async def get_sample_data():
    """샘플 데이터 조회 (테스트용)"""
    from app.services.mock_data_service import mock_data_service
    
    return {
        "bank_products": mock_data_service.get_bank_products(),
        "youth_policies": mock_data_service.get_youth_policies(),
        "user_profiles": mock_data_service.user_profiles
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
