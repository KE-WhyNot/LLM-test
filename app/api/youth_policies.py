from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.models import YouthPolicy
from app.schemas.youth_policy import YouthPolicyResponse, YouthPolicyCreate, YouthPolicyUpdate
from app.services.msa_client import msa_client
from app.services.ai_preprocessing import ai_preprocessing_service
from app.services.file_preprocessor import file_preprocessor
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[YouthPolicyResponse])
async def get_youth_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    age: Optional[int] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db)
):
    """청년 정책 목록 조회"""
    try:
        query = db.query(YouthPolicy)
        
        if age:
            query = query.filter(
                YouthPolicy.target_age_min <= age,
                YouthPolicy.target_age_max >= age
            )
        if is_active is not None:
            query = query.filter(YouthPolicy.is_active == is_active)
        
        policies = query.offset(skip).limit(limit).all()
        return policies
        
    except Exception as e:
        logger.error(f"청년 정책 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="청년 정책 조회 중 오류가 발생했습니다")

@router.get("/{policy_id}", response_model=YouthPolicyResponse)
async def get_youth_policy(policy_id: int, db: Session = Depends(get_db)):
    """특정 청년 정책 조회"""
    try:
        policy = db.query(YouthPolicy).filter(YouthPolicy.id == policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다")
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"청년 정책 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="청년 정책 조회 중 오류가 발생했습니다")

@router.post("/preprocess", response_model=dict)
async def preprocess_youth_policies(
    background_tasks: BackgroundTasks,
    age: Optional[int] = None
):
    """청년 정책 전처리 (MSA 통신)"""
    try:
        # 백그라운드에서 정책 전처리 실행
        background_tasks.add_task(preprocess_policies_task, age)
        
        return {
            "message": "청년 정책 전처리가 시작되었습니다",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"청년 정책 전처리 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="전처리 시작 중 오류가 발생했습니다")

async def preprocess_policies_task(age: Optional[int]):
    """청년 정책 전처리 백그라운드 작업"""
    try:
        # 1-a. 파일 기반 원본 데이터 전처리 (data/policy.json)
        file_processed = await file_preprocessor.preprocess_policy()
        
        # 1-b. 정책/상품 MSA에서 원본 데이터 가져오기
        raw_policies = await msa_client.get_youth_policies(age)
        
        # 2. AI 전처리 수행 (MSA 원본)
        processed_policies = []
        if raw_policies:
            processed_policies = await ai_preprocessing_service.preprocess_youth_policies(raw_policies)
        
        combined = (file_processed or []) + (processed_policies or [])
        if not combined:
            logger.warning("전처리할 청년 정책이 없습니다")
            return
        
        # 3. 전처리된 데이터를 정책/상품 MSA로 전송
        success = await msa_client.send_processed_policies(combined)
        
        if success:
            logger.info(f"청년 정책 전처리 완료: {len(combined)}개 정책")
        else:
            logger.error("전처리된 청년 정책 전송 실패")
        
    except Exception as e:
        logger.error(f"청년 정책 전처리 실패: {e}")

@router.post("/", response_model=YouthPolicyResponse)
async def create_youth_policy(
    policy: YouthPolicyCreate,
    db: Session = Depends(get_db)
):
    """새 청년 정책 생성"""
    try:
        # 중복 정책 코드 확인
        existing_policy = db.query(YouthPolicy).filter(
            YouthPolicy.policy_code == policy.policy_code
        ).first()
        
        if existing_policy:
            raise HTTPException(status_code=400, detail="이미 존재하는 정책 코드입니다")
        
        # 새 정책 생성
        new_policy = YouthPolicy(**policy.dict())
        db.add(new_policy)
        db.commit()
        db.refresh(new_policy)
        
        return new_policy
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"청년 정책 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="청년 정책 생성 중 오류가 발생했습니다")

@router.put("/{policy_id}", response_model=YouthPolicyResponse)
async def update_youth_policy(
    policy_id: int,
    policy_update: YouthPolicyUpdate,
    db: Session = Depends(get_db)
):
    """청년 정책 수정"""
    try:
        policy = db.query(YouthPolicy).filter(YouthPolicy.id == policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다")
        
        # 업데이트할 필드만 적용
        update_data = policy_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(policy, field, value)
        
        db.commit()
        db.refresh(policy)
        
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"청년 정책 수정 실패: {e}")
        raise HTTPException(status_code=500, detail="청년 정책 수정 중 오류가 발생했습니다")

@router.delete("/{policy_id}")
async def delete_youth_policy(policy_id: int, db: Session = Depends(get_db)):
    """청년 정책 삭제 (소프트 삭제)"""
    try:
        policy = db.query(YouthPolicy).filter(YouthPolicy.id == policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다")
        
        # 소프트 삭제 (is_active = False)
        policy.is_active = False
        db.commit()
        
        return {"message": "정책이 비활성화되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"청년 정책 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="청년 정책 삭제 중 오류가 발생했습니다")
