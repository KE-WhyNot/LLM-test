import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.schemas.youth_policy import YouthPolicyCreate
from app.database.models import YouthPolicy
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class YouthPolicyAPIService:
    """온통청년 정책 API 서비스"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def fetch_policies(self, age: Optional[int] = None) -> List[Dict[str, Any]]:
        """청년 정책 정보 조회"""
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if age:
                    params["age"] = age
                
                response = await client.get(
                    f"{self.base_url}/policies",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("data", [])
                
        except httpx.HTTPError as e:
            logger.error(f"청년 정책 API 요청 실패: {e}")
            raise Exception(f"청년 정책 조회 실패: {str(e)}")
        except Exception as e:
            logger.error(f"청년 정책 API 처리 중 오류: {e}")
            raise
    
    async def fetch_policy_detail(self, policy_code: str) -> Dict[str, Any]:
        """특정 정책 상세 정보 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/policies/{policy_code}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("data", {})
                
        except httpx.HTTPError as e:
            logger.error(f"청년 정책 상세 조회 실패: {e}")
            raise Exception(f"정책 상세 조회 실패: {str(e)}")
    
    def sync_policies_to_db(self, policies: List[Dict[str, Any]], db: Session) -> int:
        """API에서 받은 정책 정보를 DB에 동기화"""
        synced_count = 0
        
        for policy_data in policies:
            try:
                # 기존 정책 확인
                existing_policy = db.query(YouthPolicy).filter(
                    YouthPolicy.policy_code == policy_data.get("policy_code")
                ).first()
                
                if existing_policy:
                    # 기존 정책 업데이트
                    existing_policy.policy_name = policy_data.get("policy_name", existing_policy.policy_name)
                    existing_policy.target_age_min = policy_data.get("target_age_min", existing_policy.target_age_min)
                    existing_policy.target_age_max = policy_data.get("target_age_max", existing_policy.target_age_max)
                    existing_policy.benefit_amount = policy_data.get("benefit_amount", existing_policy.benefit_amount)
                    existing_policy.requirements = policy_data.get("requirements", existing_policy.requirements)
                    existing_policy.application_period = policy_data.get("application_period", existing_policy.application_period)
                    existing_policy.policy_data = policy_data.get("policy_data", existing_policy.policy_data)
                    existing_policy.is_active = policy_data.get("is_active", True)
                else:
                    # 새 정책 생성
                    new_policy = YouthPolicy(
                        policy_code=policy_data.get("policy_code"),
                        policy_name=policy_data.get("policy_name"),
                        target_age_min=policy_data.get("target_age_min"),
                        target_age_max=policy_data.get("target_age_max"),
                        benefit_amount=policy_data.get("benefit_amount"),
                        requirements=policy_data.get("requirements"),
                        application_period=policy_data.get("application_period"),
                        policy_data=policy_data.get("policy_data"),
                        is_active=policy_data.get("is_active", True)
                    )
                    db.add(new_policy)
                
                synced_count += 1
                
            except Exception as e:
                logger.error(f"정책 동기화 실패: {policy_data.get('policy_code', 'Unknown')} - {e}")
                continue
        
        try:
            db.commit()
            logger.info(f"{synced_count}개 정책 동기화 완료")
        except Exception as e:
            db.rollback()
            logger.error(f"DB 커밋 실패: {e}")
            raise
        
        return synced_count
