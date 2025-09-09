"""
정책/상품 전처리 마이크로서비스
Vertex AI를 사용하여 데이터를 전처리하고 Policy 마이크로서비스로 전송
"""
import asyncio
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Google Cloud Vertex AI (로컬 개발용 Mock 포함)
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("Vertex AI를 사용할 수 없습니다. Mock 모드로 실행됩니다.")

load_dotenv()

logger = logging.getLogger(__name__)

class PreprocessingService:
    """정책/상품 전처리 서비스"""
    
    def __init__(self):
        self.policy_service_url = os.getenv("POLICY_SERVICE_URL", "http://localhost:8001")
        self.project_id = os.getenv("PROJECT_ID", "")
        self.location = os.getenv("LOCATION", "us-central1")
        
        # Vertex AI 초기화 (로컬 개발용 Mock 포함)
        if VERTEX_AI_AVAILABLE and self.project_id:
            try:
                vertexai.init(project=self.project_id, location=self.location)
                self.model = GenerativeModel("gemini-1.5-pro")
                self.use_mock = False
                logger.info("Vertex AI 초기화 완료")
            except Exception as e:
                logger.warning(f"Vertex AI 초기화 실패, Mock 모드 사용: {e}")
                self.use_mock = True
        else:
            self.use_mock = True
            logger.info("Mock 모드로 실행됩니다")
    
    async def preprocess_bank_products(self, raw_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """은행 상품 데이터 전처리"""
        try:
            processed_products = []
            
            for product in raw_products:
                if self.use_mock:
                    # Mock 데이터 처리
                    processed_product = self._mock_preprocess_bank_product(product)
                else:
                    # Vertex AI를 사용한 실제 전처리
                    processed_product = await self._ai_preprocess_bank_product(product)
                
                processed_products.append(processed_product)
            
            logger.info(f"{len(processed_products)}개 은행 상품 전처리 완료")
            return processed_products
            
        except Exception as e:
            logger.error(f"은행 상품 전처리 실패: {e}")
            raise
    
    async def preprocess_youth_policies(self, raw_policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """청년 정책 데이터 전처리"""
        try:
            processed_policies = []
            
            for policy in raw_policies:
                if self.use_mock:
                    # Mock 데이터 처리
                    processed_policy = self._mock_preprocess_youth_policy(policy)
                else:
                    # Vertex AI를 사용한 실제 전처리
                    processed_policy = await self._ai_preprocess_youth_policy(policy)
                
                processed_policies.append(processed_policy)
            
            logger.info(f"{len(processed_policies)}개 청년 정책 전처리 완료")
            return processed_policies
            
        except Exception as e:
            logger.error(f"청년 정책 전처리 실패: {e}")
            raise
    
    async def _ai_preprocess_bank_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Vertex AI를 사용한 은행 상품 전처리"""
        try:
            prompt = f"""
            다음 은행 상품 데이터를 분석하고 구조화해주세요:
            
            원본 데이터:
            {json.dumps(product, ensure_ascii=False, indent=2)}
            
            다음 형식으로 응답해주세요:
            {{
                "product_code": "상품코드",
                "product_name": "상품명",
                "product_type": "상품유형",
                "bank_name": "은행명",
                "interest_rate": 금리(숫자),
                "min_amount": 최소금액(숫자),
                "max_amount": 최대금액(숫자),
                "term_months": 기간월수(숫자),
                "risk_level": 리스크레벨(1-5),
                "features": ["특징1", "특징2"],
                "target_customer": "대상고객",
                "preprocessed_at": "전처리일시"
            }}
            """
            
            response = self.model.generate_content(prompt)
            processed_data = json.loads(response.text)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"AI 은행 상품 전처리 실패: {e}")
            # 실패 시 원본 데이터 반환
            return self._mock_preprocess_bank_product(product)
    
    async def _ai_preprocess_youth_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Vertex AI를 사용한 청년 정책 전처리"""
        try:
            prompt = f"""
            다음 청년 정책 데이터를 분석하고 구조화해주세요:
            
            원본 데이터:
            {json.dumps(policy, ensure_ascii=False, indent=2)}
            
            다음 형식으로 응답해주세요:
            {{
                "policy_code": "정책코드",
                "policy_name": "정책명",
                "target_age_min": 최소연령(숫자),
                "target_age_max": 최대연령(숫자),
                "benefit_amount": 혜택금액(숫자),
                "requirements": "신청요건",
                "application_period": "신청기간",
                "policy_type": "정책유형",
                "eligibility_criteria": ["자격요건1", "자격요건2"],
                "preprocessed_at": "전처리일시"
            }}
            """
            
            response = self.model.generate_content(prompt)
            processed_data = json.loads(response.text)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"AI 청년 정책 전처리 실패: {e}")
            # 실패 시 원본 데이터 반환
            return self._mock_preprocess_youth_policy(policy)
    
    def _mock_preprocess_bank_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 은행 상품 전처리 (로컬 개발용)"""
        return {
            "product_code": product.get("product_code", f"PROD_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "product_name": product.get("product_name", "상품명"),
            "product_type": product.get("product_type", "예금"),
            "bank_name": product.get("bank_name", "은행명"),
            "interest_rate": float(product.get("interest_rate", 3.0)),
            "min_amount": float(product.get("min_amount", 1000000)),
            "max_amount": float(product.get("max_amount", 100000000)),
            "term_months": int(product.get("term_months", 12)),
            "risk_level": int(product.get("risk_level", 2)),
            "features": product.get("features", ["안전한 투자", "정기적 수익"]),
            "target_customer": product.get("target_customer", "일반고객"),
            "preprocessed_at": datetime.now().isoformat()
        }
    
    def _mock_preprocess_youth_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 청년 정책 전처리 (로컬 개발용)"""
        return {
            "policy_code": policy.get("policy_code", f"POLICY_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "policy_name": policy.get("policy_name", "정책명"),
            "target_age_min": int(policy.get("target_age_min", 18)),
            "target_age_max": int(policy.get("target_age_max", 39)),
            "benefit_amount": float(policy.get("benefit_amount", 1000000)),
            "requirements": policy.get("requirements", "신청요건"),
            "application_period": policy.get("application_period", "상시"),
            "policy_type": policy.get("policy_type", "금융지원"),
            "eligibility_criteria": policy.get("eligibility_criteria", ["청년", "소득기준"]),
            "preprocessed_at": datetime.now().isoformat()
        }
    
    async def send_to_policy_service(self, data: List[Dict[str, Any]], data_type: str) -> bool:
        """Policy 마이크로서비스로 전처리된 데이터 전송"""
        try:
            async with httpx.AsyncClient() as client:
                endpoint = f"{self.policy_service_url}/api/v1/{data_type}"
                
                response = await client.post(
                    endpoint,
                    json={
                        "data": data,
                        "source": "preprocessing_service",
                        "timestamp": datetime.now().isoformat()
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                logger.info(f"Policy 서비스로 {data_type} 데이터 전송 완료: {len(data)}개")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"Policy 서비스 전송 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"데이터 전송 중 오류: {e}")
            return False
    
    async def process_and_send_bank_products(self, raw_products: List[Dict[str, Any]]) -> bool:
        """은행 상품 전처리 및 Policy 서비스 전송"""
        try:
            # 1. 데이터 전처리
            processed_products = await self.preprocess_bank_products(raw_products)
            
            # 2. Policy 서비스로 전송
            success = await self.send_to_policy_service(processed_products, "bank-products")
            
            return success
            
        except Exception as e:
            logger.error(f"은행 상품 처리 및 전송 실패: {e}")
            return False
    
    async def process_and_send_youth_policies(self, raw_policies: List[Dict[str, Any]]) -> bool:
        """청년 정책 전처리 및 Policy 서비스 전송"""
        try:
            # 1. 데이터 전처리
            processed_policies = await self.preprocess_youth_policies(raw_policies)
            
            # 2. Policy 서비스로 전송
            success = await self.send_to_policy_service(processed_policies, "youth-policies")
            
            return success
            
        except Exception as e:
            logger.error(f"청년 정책 처리 및 전송 실패: {e}")
            return False

# 전처리 서비스 인스턴스
preprocessing_service = PreprocessingService()
