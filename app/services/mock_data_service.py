"""
Mock 데이터 서비스
실제 MSA 서비스가 없을 때 사용할 샘플 데이터 제공
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class MockDataService:
    """Mock 데이터 서비스"""
    
    def __init__(self):
        self.bank_products = self._load_bank_products_from_json()
        self.youth_policies = self._load_policies_from_json()
        self.user_profiles = self._get_mock_user_profiles()

    def _safe_load_json(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            if not os.path.exists(path):
                logger.warning(f"JSON 파일을 찾을 수 없습니다: {path}")
                return None
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON 로드 실패 ({path}): {e}")
            return None

    def _load_bank_products_from_json(self) -> List[Dict[str, Any]]:
        """data/bank.json에서 은행 상품 로드. 실패 시 기존 Mock 사용"""
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "bank.json")
        data = self._safe_load_json(data_path)
        if not data:
            return self._get_mock_bank_products()

        # 다양한 스키마 대응
        products: List[Dict[str, Any]] = []
        try:
            # 케이스 1: { result: { bankProducts: [...] } }
            if isinstance(data, dict):
                container = data.get("result") or data
                candidate_lists = [
                    container.get("bankProducts"),
                    container.get("products"),
                    container.get("list"),
                    container.get("items"),
                ]

                # 일부 데이터셋에서 정책 리스트가 들어올 수 있어 필터링 필요
                for lst in candidate_lists:
                    if isinstance(lst, list) and lst:
                        # 최소한 상품 식별자 키가 존재하는지 검사
                        sample = lst[0]
                        # 정책 데이터(youthPolicyList) 오탑재 회피
                        if any(k in sample for k in ["productId", "productName", "bankName", "interestRate", "productType"]):
                            products = lst
                            break

                # 직접 youthPolicyList가 온 경우는 상품이 아님 → 기본 Mock 반환
                if not products and container.get("youthPolicyList"):
                    logger.warning("bank.json에 정책 리스트가 포함되어 있어 기본 Mock 상품을 사용합니다")
                    return self._get_mock_bank_products()

            # 정규화: msa_client에서 기대하는 필드로 정제
            normalized: List[Dict[str, Any]] = []
            for p in products[:200]:
                normalized.append({
                    "productId": p.get("productId") or p.get("id") or p.get("code") or p.get("prodId", "BANK_UNKNOWN"),
                    "productName": p.get("productName") or p.get("name") or p.get("title", "상품"),
                    "productType": p.get("productType") or p.get("type") or p.get("category", "DEPOSIT"),
                    "bankCode": p.get("bankCode") or p.get("bank_code") or p.get("bankId", "000"),
                    "bankName": p.get("bankName") or p.get("bank") or p.get("issuer", "은행"),
                    "interestRate": p.get("interestRate") or p.get("rate") or p.get("yield") or 3.0,
                    "minAmount": p.get("minAmount") or p.get("min") or 0,
                    "maxAmount": p.get("maxAmount") or p.get("max") or 0,
                    "termMonths": p.get("termMonths") or p.get("term") or 0,
                    "riskLevel": p.get("riskLevel") or p.get("risk") or 2,
                    "description": p.get("description") or p.get("desc") or "",
                    "features": p.get("features") or [],
                    "targetCustomer": p.get("targetCustomer") or p.get("target") or "일반고객"
                })
            if normalized:
                logger.info(f"bank.json에서 {len(normalized)}개 상품 로드 완료")
                return normalized
        except Exception as e:
            logger.error(f"bank.json 파싱 실패: {e}")

        return self._get_mock_bank_products()

    def _load_policies_from_json(self) -> List[Dict[str, Any]]:
        """data/policy.json에서 청년 정책 로드. 실패 시 기존 Mock 사용"""
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "policy.json")
        data = self._safe_load_json(data_path)
        if not data:
            # bank.json에 youthPolicyList가 있는 케이스를 보완
            alt_bank_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "bank.json")
            alt = self._safe_load_json(alt_bank_path)
            if alt and isinstance(alt, dict) and isinstance(alt.get("result", {}).get("youthPolicyList"), list):
                data = alt
            else:
                return self._get_mock_youth_policies()

        try:
            policies_list = None
            if isinstance(data, dict):
                container = data.get("result") or data
                # 대표 키 탐색
                for key in ["youthPolicyList", "policies", "list", "items"]:
                    if isinstance(container.get(key), list):
                        policies_list = container.get(key)
                        break

            if not isinstance(policies_list, list):
                return self._get_mock_youth_policies()

            normalized: List[Dict[str, Any]] = []
            for p in policies_list[:300]:
                normalized.append({
                    "policyId": p.get("policyId") or p.get("plcyNo") or p.get("id", "YOUTH_UNKNOWN"),
                    "policyName": p.get("policyName") or p.get("plcyNm") or p.get("name", "정책"),
                    "targetAgeMin": int(p.get("targetAgeMin") or p.get("sprtTrgtMinAge") or 0),
                    "targetAgeMax": int(p.get("targetAgeMax") or p.get("sprtTrgtMaxAge") or 0),
                    "benefitAmount": float(p.get("benefitAmount") or p.get("bnftAmt") or 0),
                    "requirements": p.get("requirements") or p.get("addAplyQlfcCndCn") or "",
                    "applicationPeriod": p.get("applicationPeriod") or p.get("aplyYmd") or "",
                    "policyType": p.get("policyType") or p.get("lclsfNm") or "",
                    "description": p.get("description") or p.get("plcyExplnCn") or ""
                })
            if normalized:
                logger.info(f"policy.json에서 {len(normalized)}개 정책 로드 완료")
                return normalized
        except Exception as e:
            logger.error(f"policy.json 파싱 실패: {e}")

        return self._get_mock_youth_policies()
    
    def _get_mock_bank_products(self) -> List[Dict[str, Any]]:
        """Mock 은행 상품 데이터"""
        return [
            {
                "productId": "BANK001",
                "productName": "정기예금",
                "productType": "DEPOSIT",
                "bankCode": "001",
                "bankName": "국민은행",
                "interestRate": 3.5,
                "minAmount": 1000000,
                "maxAmount": 100000000,
                "termMonths": 12,
                "riskLevel": 1,
                "description": "안전한 정기예금 상품",
                "features": ["안전성", "정기적 수익"],
                "targetCustomer": "일반고객"
            },
            {
                "productId": "BANK002",
                "productName": "정기적금",
                "productType": "SAVINGS",
                "bankCode": "002",
                "bankName": "신한은행",
                "interestRate": 4.0,
                "minAmount": 500000,
                "maxAmount": 50000000,
                "termMonths": 24,
                "riskLevel": 1,
                "description": "정기적금 상품",
                "features": ["안전성", "정기적 저축"],
                "targetCustomer": "일반고객"
            },
            {
                "productId": "BANK003",
                "productName": "청년도약계좌",
                "productType": "YOUTH_ACCOUNT",
                "bankCode": "001",
                "bankName": "국민은행",
                "interestRate": 5.0,
                "minAmount": 100000,
                "maxAmount": 10000000,
                "termMonths": 36,
                "riskLevel": 2,
                "description": "청년을 위한 특별 상품",
                "features": ["청년특혜", "높은 금리"],
                "targetCustomer": "청년"
            },
            {
                "productId": "BANK004",
                "productName": "주식형펀드",
                "productType": "FUND",
                "bankCode": "003",
                "bankName": "우리은행",
                "interestRate": 7.0,
                "minAmount": 1000000,
                "maxAmount": 1000000000,
                "termMonths": 0,
                "riskLevel": 4,
                "description": "주식형 펀드 상품",
                "features": ["높은 수익", "시장참여"],
                "targetCustomer": "투자자"
            },
            {
                "productId": "BANK005",
                "productName": "채권형펀드",
                "productType": "BOND_FUND",
                "bankCode": "004",
                "bankName": "하나은행",
                "interestRate": 4.5,
                "minAmount": 500000,
                "maxAmount": 500000000,
                "termMonths": 0,
                "riskLevel": 2,
                "description": "채권형 펀드 상품",
                "features": ["안정성", "중간수익"],
                "targetCustomer": "보수적투자자"
            }
        ]
    
    def _get_mock_youth_policies(self) -> List[Dict[str, Any]]:
        """Mock 청년 정책 데이터"""
        return [
            {
                "policyId": "YOUTH001",
                "policyName": "청년도약계좌",
                "targetAgeMin": 19,
                "targetAgeMax": 34,
                "benefitAmount": 5000000,
                "requirements": "만 19세~34세 청년",
                "applicationPeriod": "상시",
                "policyType": "FINANCIAL_SUPPORT",
                "description": "청년을 위한 금융지원 정책"
            },
            {
                "policyId": "YOUTH002",
                "policyName": "청년주택청약",
                "targetAgeMin": 20,
                "targetAgeMax": 39,
                "benefitAmount": 2000000,
                "requirements": "만 20세~39세 청년, 무주택자",
                "applicationPeriod": "상시",
                "policyType": "HOUSING_SUPPORT",
                "description": "청년 주택 구매 지원"
            },
            {
                "policyId": "YOUTH003",
                "policyName": "청년취업지원",
                "targetAgeMin": 18,
                "targetAgeMax": 29,
                "benefitAmount": 1000000,
                "requirements": "만 18세~29세 청년, 구직자",
                "applicationPeriod": "상시",
                "policyType": "EMPLOYMENT_SUPPORT",
                "description": "청년 취업 지원 정책"
            }
        ]
    
    def _get_mock_user_profiles(self) -> List[Dict[str, Any]]:
        """Mock 사용자 프로필 데이터 (요구 필드 포함)":
        - totalAssets: 가용 가능 자산
        - investmentPreference: 투자 성향 (공격적/균형형/안정형/위험 회피형/중립형)
        - investmentGoal: 투자 목표
        - interestSectors: 관심 주식 분야
        """
        return [
            {
                "userId": 1,
                "email": "user1@example.com",
                "name": "김청년",
                "age": 25,
                "incomeLevel": "중간소득",
                "totalAssets": 15000000,
                "investmentPreference": "중립형",
                "investmentGoal": "주택구입",
                "interestSectors": ["IT", "금융", "필수소비재"],
                "riskTolerance": 6,
                "investmentHorizon": "5년"
            },
            {
                "userId": 2,
                "email": "user2@example.com",
                "name": "이투자자",
                "age": 30,
                "incomeLevel": "고소득",
                "totalAssets": 50000000,
                "investmentPreference": "고위험 고수익",
                "investmentGoal": "자산증식",
                "interestSectors": ["IT", "바이오", "반도체", "2차전지"],
                "riskTolerance": 8,
                "investmentHorizon": "10년"
            },
            {
                "userId": 3,
                "email": "user3@example.com",
                "name": "박안전",
                "age": 28,
                "incomeLevel": "중간소득",
                "totalAssets": 20000000,
                "investmentPreference": "안정형",
                "investmentGoal": "안전한자산증식",
                "interestSectors": ["금융", "공공", "통신"],
                "riskTolerance": 3,
                "investmentHorizon": "3년"
            }
        ]
    
    def get_bank_products(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Mock 은행 상품 조회"""
        products = self.bank_products.copy()
        
        if filters:
            if "product_type" in filters:
                products = [p for p in products if p["productType"] == filters["product_type"]]
            if "bank_name" in filters:
                products = [p for p in products if p["bankName"] == filters["bank_name"]]
        
        return products
    
    def get_youth_policies(self, age: Optional[int] = None) -> List[Dict[str, Any]]:
        """Mock 청년 정책 조회"""
        policies = self.youth_policies.copy()
        
        if age:
            policies = [
                p for p in policies 
                if p["targetAgeMin"] <= age <= p["targetAgeMax"]
            ]
        
        return policies
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Mock 사용자 프로필 조회"""
        for profile in self.user_profiles:
            if profile["userId"] == user_id:
                return profile
        return None

# Mock 데이터 서비스 인스턴스
mock_data_service = MockDataService()
