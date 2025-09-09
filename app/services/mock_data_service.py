"""
Mock 데이터 서비스
실제 MSA 서비스가 없을 때 사용할 샘플 데이터 제공
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MockDataService:
    """Mock 데이터 서비스"""
    
    def __init__(self):
        self.bank_products = self._get_mock_bank_products()
        self.youth_policies = self._get_mock_youth_policies()
        self.user_profiles = self._get_mock_user_profiles()
    
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
        """Mock 사용자 프로필 데이터"""
        return [
            {
                "userId": 1,
                "email": "user1@example.com",
                "name": "김청년",
                "age": 25,
                "incomeLevel": "중간소득",
                "totalAssets": 10000000,
                "investmentPreference": "중립적",
                "interestSectors": ["IT", "금융"],
                "riskTolerance": 6,
                "investmentGoal": "주택구입",
                "investmentHorizon": "5년"
            },
            {
                "userId": 2,
                "email": "user2@example.com",
                "name": "이투자자",
                "age": 30,
                "incomeLevel": "고소득",
                "totalAssets": 50000000,
                "investmentPreference": "공격적",
                "interestSectors": ["IT", "바이오", "반도체"],
                "riskTolerance": 8,
                "investmentGoal": "자산증식",
                "investmentHorizon": "10년"
            },
            {
                "userId": 3,
                "email": "user3@example.com",
                "name": "박안전",
                "age": 28,
                "incomeLevel": "중간소득",
                "totalAssets": 20000000,
                "investmentPreference": "보수적",
                "interestSectors": ["금융", "공공"],
                "riskTolerance": 3,
                "investmentGoal": "안전한자산증식",
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
