"""
MSA 통신을 위한 API 클라이언트
다른 MSA 서비스들과 통신하는 공통 클라이언트
"""
import httpx
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from app.services.mock_data_service import mock_data_service

load_dotenv()

logger = logging.getLogger(__name__)

class MSAClient:
    """MSA 통신 클라이언트"""
    
    def __init__(self):
        self.policy_service_url = os.getenv("POLICY_SERVICE_URL", "http://localhost:8001")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
        self.timeout = 30.0
        self.use_mock = not (self.policy_service_url and self.user_service_url)
        
        if self.use_mock:
            logger.info("Mock 모드로 실행됩니다 (MSA 서비스 URL이 설정되지 않음)")
    
    async def get_bank_products(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """정책/상품 MSA에서 은행 상품 조회"""
        if self.use_mock:
            # Mock 모드: 샘플 데이터 반환
            raw_products = mock_data_service.get_bank_products(filters)
            return self._convert_bank_products(raw_products)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.policy_service_url}/api/v1/bank-products",
                    params=filters or {},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # API 응답 구조에 맞게 데이터 변환
                raw_products = data.get("data", [])
                return self._convert_bank_products(raw_products)
                
        except httpx.HTTPError as e:
            logger.error(f"은행 상품 조회 실패: {e}")
            raise Exception(f"은행 상품 조회 실패: {str(e)}")
        except Exception as e:
            logger.error(f"은행 상품 조회 중 오류: {e}")
            raise
    
    def _convert_bank_products(self, raw_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """은행 상품 데이터 변환"""
        converted_products = []
        
        for product in raw_products:
            converted_product = {
                "product_code": product.get("productId", ""),
                "product_name": product.get("productName", ""),
                "product_type": product.get("productType", ""),
                "bank_name": product.get("bankName", ""),
                "bank_code": product.get("bankCode", ""),
                "interest_rate": float(product.get("interestRate", 0)),
                "min_amount": float(product.get("minAmount", 0)),
                "max_amount": float(product.get("maxAmount", 0)),
                "term_months": int(product.get("termMonths", 0)),
                "risk_level": int(product.get("riskLevel", 1)),
                "description": product.get("description", ""),
                "features": product.get("features", []),
                "target_customer": product.get("targetCustomer", ""),
                "raw_data": product  # 원본 데이터 보존
            }
            converted_products.append(converted_product)
        
        return converted_products
    
    async def get_youth_policies(self, age: Optional[int] = None) -> List[Dict[str, Any]]:
        """정책/상품 MSA에서 청년 정책 조회"""
        if self.use_mock:
            # Mock 모드: 샘플 데이터 반환
            raw_policies = mock_data_service.get_youth_policies(age)
            return self._convert_youth_policies(raw_policies)
        
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if age:
                    params["age"] = age
                
                response = await client.get(
                    f"{self.policy_service_url}/api/v1/youth-policies",
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # API 응답 구조에 맞게 데이터 변환
                raw_policies = data.get("data", [])
                return self._convert_youth_policies(raw_policies)
                
        except httpx.HTTPError as e:
            logger.error(f"청년 정책 조회 실패: {e}")
            raise Exception(f"청년 정책 조회 실패: {str(e)}")
        except Exception as e:
            logger.error(f"청년 정책 조회 중 오류: {e}")
            raise
    
    def _convert_youth_policies(self, raw_policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """청년 정책 데이터 변환"""
        converted_policies = []
        
        for policy in raw_policies:
            converted_policy = {
                "policy_code": policy.get("policyId", ""),
                "policy_name": policy.get("policyName", ""),
                "target_age_min": int(policy.get("targetAgeMin", 0)),
                "target_age_max": int(policy.get("targetAgeMax", 0)),
                "benefit_amount": float(policy.get("benefitAmount", 0)),
                "requirements": policy.get("requirements", ""),
                "application_period": policy.get("applicationPeriod", ""),
                "policy_type": policy.get("policyType", ""),
                "description": policy.get("description", ""),
                "raw_data": policy  # 원본 데이터 보존
            }
            converted_policies.append(converted_policy)
        
        return converted_policies
    
    async def send_processed_products(self, processed_products: List[Dict[str, Any]]) -> bool:
        """전처리된 은행 상품을 정책/상품 MSA로 전송"""
        if self.use_mock:
            # Mock 모드: 전송 시뮬레이션
            logger.info(f"Mock 모드: 전처리된 은행 상품 전송 시뮬레이션 - {len(processed_products)}개")
            return True
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.policy_service_url}/api/v1/bank-products/processed",
                    json={
                        "data": processed_products,
                        "source": "ai_service",
                        "timestamp": datetime.now().isoformat()
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"전처리된 은행 상품 전송 완료: {len(processed_products)}개")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"전처리된 은행 상품 전송 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"은행 상품 전송 중 오류: {e}")
            return False
    
    async def send_processed_policies(self, processed_policies: List[Dict[str, Any]]) -> bool:
        """전처리된 청년 정책을 정책/상품 MSA로 전송"""
        if self.use_mock:
            # Mock 모드: 전송 시뮬레이션
            logger.info(f"Mock 모드: 전처리된 청년 정책 전송 시뮬레이션 - {len(processed_policies)}개")
            return True
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.policy_service_url}/api/v1/youth-policies/processed",
                    json={
                        "data": processed_policies,
                        "source": "ai_service",
                        "timestamp": datetime.now().isoformat()
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"전처리된 청년 정책 전송 완료: {len(processed_policies)}개")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"전처리된 청년 정책 전송 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"청년 정책 전송 중 오류: {e}")
            return False
    
    async def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """사용자/포트폴리오 MSA에서 사용자 프로필 조회"""
        if self.use_mock:
            # Mock 모드: 샘플 데이터 반환
            user_data = mock_data_service.get_user_profile(user_id)
            if not user_data:
                raise Exception(f"사용자 {user_id}를 찾을 수 없습니다")
            return self._convert_user_profile(user_data)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.user_service_url}/api/v1/users/{user_id}",
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # API 응답 구조에 맞게 데이터 변환
                user_data = data.get("data", {})
                return self._convert_user_profile(user_data)
                
        except httpx.HTTPError as e:
            logger.error(f"사용자 프로필 조회 실패: {e}")
            raise Exception(f"사용자 프로필 조회 실패: {str(e)}")
        except Exception as e:
            logger.error(f"사용자 프로필 조회 중 오류: {e}")
            raise
    
    def _convert_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 프로필 데이터 변환"""
        return {
            "id": user_data.get("userId", user_data.get("id", 0)),
            "email": user_data.get("email", ""),
            "name": user_data.get("name", ""),
            "age": int(user_data.get("age", 25)),
            "income_level": user_data.get("incomeLevel", ""),
            "total_assets": float(user_data.get("totalAssets", 0)),
            "investment_preference": user_data.get("investmentPreference", ""),
            "interest_sectors": user_data.get("interestSectors", []),
            "risk_tolerance": int(user_data.get("riskTolerance", 5)),
            "investment_goal": user_data.get("investmentGoal", ""),
            "investment_horizon": user_data.get("investmentHorizon", ""),
            "raw_data": user_data  # 원본 데이터 보존
        }
    
    async def send_portfolio_recommendation(
        self, 
        user_id: int, 
        recommendation: Dict[str, Any]
    ) -> bool:
        """포트폴리오 추천 결과를 사용자/포트폴리오 MSA로 전송"""
        if self.use_mock:
            # Mock 모드: 전송 시뮬레이션
            logger.info(f"Mock 모드: 포트폴리오 추천 전송 시뮬레이션 - 사용자 {user_id}")
            return True
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.user_service_url}/api/v1/users/{user_id}/portfolio/recommendations",
                    json={
                        "recommendation": recommendation,
                        "source": "ai_service",
                        "timestamp": datetime.now().isoformat()
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                logger.info(f"포트폴리오 추천 전송 완료: 사용자 {user_id}")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"포트폴리오 추천 전송 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"포트폴리오 추천 전송 중 오류: {e}")
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """연결된 MSA 서비스들의 헬스 체크"""
        health_status = {}
        
        # 정책/상품 MSA 헬스 체크
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.policy_service_url}/health",
                    timeout=5.0
                )
                health_status["policy_service"] = response.status_code == 200
        except:
            health_status["policy_service"] = False
        
        # 사용자/포트폴리오 MSA 헬스 체크
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.user_service_url}/health",
                    timeout=5.0
                )
                health_status["user_service"] = response.status_code == 200
        except:
            health_status["user_service"] = False
        
        return health_status

# MSA 클라이언트 인스턴스
msa_client = MSAClient()
