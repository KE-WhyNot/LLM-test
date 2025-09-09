from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.models import BankProduct
from app.schemas.bank_product import BankProductResponse, BankProductFilter, BankProductCreate, BankProductUpdate
from app.services.msa_client import msa_client
from app.services.ai_preprocessing import ai_preprocessing_service
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[BankProductResponse])
async def get_bank_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_type: Optional[str] = None,
    bank_name: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """은행 상품 목록 조회"""
    try:
        query = db.query(BankProduct)
        
        if product_type:
            query = query.filter(BankProduct.product_type == product_type)
        if bank_name:
            query = query.filter(BankProduct.bank_name == bank_name)
        if is_active is not None:
            query = query.filter(BankProduct.is_active == is_active)
        
        products = query.offset(skip).limit(limit).all()
        return products
        
    except Exception as e:
        logger.error(f"은행 상품 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="은행 상품 조회 중 오류가 발생했습니다")

@router.get("/{product_id}", response_model=BankProductResponse)
async def get_bank_product(product_id: int, db: Session = Depends(get_db)):
    """특정 은행 상품 조회"""
    try:
        product = db.query(BankProduct).filter(BankProduct.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"은행 상품 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="은행 상품 조회 중 오류가 발생했습니다")

@router.post("/preprocess", response_model=dict)
async def preprocess_bank_products(
    background_tasks: BackgroundTasks,
    product_type: Optional[str] = None
):
    """은행 상품 전처리 (MSA 통신)"""
    try:
        # 백그라운드에서 상품 전처리 실행
        background_tasks.add_task(preprocess_products_task, product_type)
        
        return {
            "message": "은행 상품 전처리가 시작되었습니다",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"은행 상품 전처리 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="전처리 시작 중 오류가 발생했습니다")

async def preprocess_products_task(product_type: Optional[str]):
    """은행 상품 전처리 백그라운드 작업"""
    try:
        # 1. 정책/상품 MSA에서 원본 데이터 가져오기
        raw_products = await msa_client.get_bank_products({"product_type": product_type} if product_type else None)
        
        if not raw_products:
            logger.warning("전처리할 은행 상품이 없습니다")
            return
        
        # 2. AI 전처리 수행
        processed_products = await ai_preprocessing_service.preprocess_bank_products(raw_products)
        
        # 3. 전처리된 데이터를 정책/상품 MSA로 전송
        success = await msa_client.send_processed_products(processed_products)
        
        if success:
            logger.info(f"은행 상품 전처리 완료: {len(processed_products)}개 상품")
        else:
            logger.error("전처리된 은행 상품 전송 실패")
        
    except Exception as e:
        logger.error(f"은행 상품 전처리 실패: {e}")

@router.post("/", response_model=BankProductResponse)
async def create_bank_product(
    product: BankProductCreate,
    db: Session = Depends(get_db)
):
    """새 은행 상품 생성"""
    try:
        # 중복 상품 코드 확인
        existing_product = db.query(BankProduct).filter(
            BankProduct.product_code == product.product_code
        ).first()
        
        if existing_product:
            raise HTTPException(status_code=400, detail="이미 존재하는 상품 코드입니다")
        
        # 새 상품 생성
        new_product = BankProduct(**product.dict())
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        return new_product
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"은행 상품 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="은행 상품 생성 중 오류가 발생했습니다")

@router.put("/{product_id}", response_model=BankProductResponse)
async def update_bank_product(
    product_id: int,
    product_update: BankProductUpdate,
    db: Session = Depends(get_db)
):
    """은행 상품 수정"""
    try:
        product = db.query(BankProduct).filter(BankProduct.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
        
        # 업데이트할 필드만 적용
        update_data = product_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"은행 상품 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="은행 상품 수정 중 오류가 발생했습니다")

@router.delete("/{product_id}")
async def delete_bank_product(product_id: int, db: Session = Depends(get_db)):
    """은행 상품 삭제 (소프트 삭제)"""
    try:
        product = db.query(BankProduct).filter(BankProduct.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다")
        
        # 소프트 삭제 (is_active = False)
        product.is_active = False
        db.commit()
        
        return {"message": "상품이 비활성화되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"은행 상품 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="은행 상품 삭제 중 오류가 발생했습니다")
