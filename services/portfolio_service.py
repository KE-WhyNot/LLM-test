"""
포트폴리오 추천 서비스
사용자 정보를 받아서 Gemini를 사용하여 포트폴리오를 구성
"""
import asyncio
import httpx
import json
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import os
from dotenv import load_dotenv

# Google Gemini (로컬 개발용 Mock 포함)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Gemini를 사용할 수 없습니다. Mock 모드로 실행됩니다.")

load_dotenv()

logger = logging.getLogger(__name__)

class PortfolioService:
    """포트폴리오 추천 서비스"""
    
    def __init__(self):
        self.policy_service_url = os.getenv("POLICY_SERVICE_URL", "http://localhost:8001")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        
        # Gemini 초기화 (로컬 개발용 Mock 포함)
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                self.use_mock = False
                logger.info("Gemini 초기화 완료")
            except Exception as e:
                logger.warning(f"Gemini 초기화 실패, Mock 모드 사용: {e}")
                self.use_mock = True
        else:
            self.use_mock = True
            logger.info("Mock 모드로 실행됩니다")
    
    async def get_available_products(self) -> List[Dict[str, Any]]:
        """Policy 서비스에서 사용 가능한 상품 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.policy_service_url}/api/v1/bank-products",
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
                
        except httpx.HTTPError as e:
            logger.error(f"상품 조회 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"상품 조회 중 오류: {e}")
            return []
    
    async def get_youth_policies(self, age: int) -> List[Dict[str, Any]]:
        """Policy 서비스에서 청년 정책 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.policy_service_url}/api/v1/youth-policies",
                    params={"age": age},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
                
        except httpx.HTTPError as e:
            logger.error(f"청년 정책 조회 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"청년 정책 조회 중 오류: {e}")
            return []
    
    async def generate_portfolio_recommendation(
        self, 
        user_profile: Dict[str, Any],
        available_products: List[Dict[str, Any]],
        youth_policies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Gemini를 사용한 포트폴리오 추천 생성"""
        try:
            if self.use_mock:
                # Mock 포트폴리오 추천
                recommendation = self._mock_generate_portfolio(user_profile, available_products, youth_policies)
            else:
                # Gemini를 사용한 실제 추천
                recommendation = await self._ai_generate_portfolio(user_profile, available_products, youth_policies)
            
            logger.info("포트폴리오 추천 생성 완료")
            return recommendation
            
        except Exception as e:
            logger.error(f"포트폴리오 추천 생성 실패: {e}")
            raise
    
    async def _ai_generate_portfolio(
        self, 
        user_profile: Dict[str, Any],
        available_products: List[Dict[str, Any]],
        youth_policies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Gemini를 사용한 AI 포트폴리오 추천"""
        try:
            prompt = f"""
            다음 사용자 정보를 바탕으로 최적의 포트폴리오를 추천해주세요:
            
            사용자 프로필:
            - 나이: {user_profile.get('age', 0)}세
            - 소득분위: {user_profile.get('income_level', '')}
            - 총 자산: {user_profile.get('total_assets', 0)}원
            - 투자성향: {user_profile.get('investment_preference', '')}
            - 관심 종목: {', '.join(user_profile.get('interest_sectors', []))}
            - 리스크 허용도: {user_profile.get('risk_tolerance', 5)}/10
            
            사용 가능한 금융 상품:
            {json.dumps(available_products, ensure_ascii=False, indent=2)}
            
            청년 정책:
            {json.dumps(youth_policies, ensure_ascii=False, indent=2)}
            
            다음 형식으로 포트폴리오를 추천해주세요:
            {{
                "total_investment_amount": 총투자금액(숫자),
                "portfolio_items": [
                    {{
                        "product_id": 상품ID(숫자),
                        "product_name": "상품명",
                        "bank_name": "은행명",
                        "product_type": "상품유형",
                        "allocation_percentage": 배분비율(숫자),
                        "investment_amount": 투자금액(숫자),
                        "expected_return": 예상수익률(숫자),
                        "risk_level": 리스크레벨(숫자)
                    }}
                ],
                "expected_total_return": 예상총수익률(숫자),
                "total_risk_score": 총리스크점수(숫자),
                "recommendation_reason": "추천이유",
                "confidence_score": 신뢰도점수(0-1),
                "youth_policy_benefits": ["활용가능한청년정책1", "활용가능한청년정책2"]
            }}
            
            주의사항:
            1. 총 배분 비율은 100%가 되어야 합니다
            2. 사용자의 리스크 허용도에 맞는 상품을 선택하세요
            3. 청년 정책을 활용할 수 있는 상품을 우선 고려하세요
            4. 분산투자 원칙을 적용하세요
            5. 최대 5개 상품으로 구성하세요
            """
            
            response = self.model.generate_content(prompt)
            recommendation = json.loads(response.text)
            
            return recommendation
            
        except Exception as e:
            logger.error(f"AI 포트폴리오 추천 실패: {e}")
            # 실패 시 Mock 추천 반환
            return self._mock_generate_portfolio(user_profile, available_products, youth_policies)
    
    def _mock_generate_portfolio(
        self, 
        user_profile: Dict[str, Any],
        available_products: List[Dict[str, Any]],
        youth_policies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Mock 포트폴리오 추천 (로컬 개발용)"""
        total_assets = float(user_profile.get('total_assets', 10000000))
        risk_tolerance = user_profile.get('risk_tolerance', 5)
        
        # 간단한 Mock 포트폴리오 생성
        portfolio_items = []
        if available_products:
            # 첫 번째 상품 (40%)
            product1 = available_products[0]
            portfolio_items.append({
                "product_id": product1.get("id", 1),
                "product_name": product1.get("product_name", "정기예금"),
                "bank_name": product1.get("bank_name", "은행"),
                "product_type": product1.get("product_type", "예금"),
                "allocation_percentage": 40.0,
                "investment_amount": total_assets * 0.4,
                "expected_return": product1.get("interest_rate", 3.0),
                "risk_level": product1.get("risk_level", 2)
            })
            
            # 두 번째 상품 (30%)
            if len(available_products) > 1:
                product2 = available_products[1]
                portfolio_items.append({
                    "product_id": product2.get("id", 2),
                    "product_name": product2.get("product_name", "적금"),
                    "bank_name": product2.get("bank_name", "은행"),
                    "product_type": product2.get("product_type", "적금"),
                    "allocation_percentage": 30.0,
                    "investment_amount": total_assets * 0.3,
                    "expected_return": product2.get("interest_rate", 3.5),
                    "risk_level": product2.get("risk_level", 2)
                })
            
            # 세 번째 상품 (30%)
            if len(available_products) > 2:
                product3 = available_products[2]
                portfolio_items.append({
                    "product_id": product3.get("id", 3),
                    "product_name": product3.get("product_name", "펀드"),
                    "bank_name": product3.get("bank_name", "은행"),
                    "product_type": product3.get("product_type", "펀드"),
                    "allocation_percentage": 30.0,
                    "investment_amount": total_assets * 0.3,
                    "expected_return": product3.get("interest_rate", 5.0),
                    "risk_level": product3.get("risk_level", 3)
                })
        
        # 예상 총 수익률 계산
        expected_total_return = sum(
            item["expected_return"] * item["allocation_percentage"] / 100 
            for item in portfolio_items
        )
        
        # 총 리스크 점수 계산
        total_risk_score = sum(
            item["risk_level"] * item["allocation_percentage"] / 100 
            for item in portfolio_items
        )
        
        return {
            "total_investment_amount": total_assets,
            "portfolio_items": portfolio_items,
            "expected_total_return": expected_total_return,
            "total_risk_score": total_risk_score,
            "recommendation_reason": f"사용자의 리스크 허용도({risk_tolerance}/10)에 맞춘 분산투자 포트폴리오입니다.",
            "confidence_score": 0.85,
            "youth_policy_benefits": [policy.get("policy_name", "청년정책") for policy in youth_policies[:2]]
        }
    
    async def analyze_portfolio_risk(self, portfolio_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """포트폴리오 리스크 분석"""
        try:
            if self.use_mock:
                return self._mock_analyze_risk(portfolio_items)
            else:
                return await self._ai_analyze_risk(portfolio_items)
                
        except Exception as e:
            logger.error(f"포트폴리오 리스크 분석 실패: {e}")
            return self._mock_analyze_risk(portfolio_items)
    
    async def _ai_analyze_risk(self, portfolio_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gemini를 사용한 리스크 분석"""
        try:
            prompt = f"""
            다음 포트폴리오의 리스크를 분석해주세요:
            
            포트폴리오 구성:
            {json.dumps(portfolio_items, ensure_ascii=False, indent=2)}
            
            다음 형식으로 리스크 분석 결과를 제공해주세요:
            {{
                "overall_risk_score": 전체리스크점수(1-10),
                "risk_breakdown": {{
                    "credit_risk": 신용리스크(1-10),
                    "market_risk": 시장리스크(1-10),
                    "liquidity_risk": 유동성리스크(1-10),
                    "concentration_risk": 집중리스크(1-10)
                }},
                "risk_factors": ["리스크요인1", "리스크요인2"],
                "mitigation_strategies": ["완화전략1", "완화전략2"],
                "recommendations": ["개선권고1", "개선권고2"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            risk_analysis = json.loads(response.text)
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"AI 리스크 분석 실패: {e}")
            return self._mock_analyze_risk(portfolio_items)
    
    def _mock_analyze_risk(self, portfolio_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock 리스크 분석 (로컬 개발용)"""
        if not portfolio_items:
            return {
                "overall_risk_score": 5,
                "risk_breakdown": {
                    "credit_risk": 5,
                    "market_risk": 5,
                    "liquidity_risk": 5,
                    "concentration_risk": 5
                },
                "risk_factors": ["포트폴리오가 비어있습니다"],
                "mitigation_strategies": ["상품을 추가하세요"],
                "recommendations": ["다양한 상품으로 분산투자하세요"]
            }
        
        # 간단한 리스크 계산
        avg_risk = sum(item.get("risk_level", 3) for item in portfolio_items) / len(portfolio_items)
        
        return {
            "overall_risk_score": avg_risk,
            "risk_breakdown": {
                "credit_risk": avg_risk,
                "market_risk": avg_risk,
                "liquidity_risk": avg_risk,
                "concentration_risk": avg_risk
            },
            "risk_factors": ["시장 변동성", "금리 변동"],
            "mitigation_strategies": ["분산투자", "정기 리밸런싱"],
            "recommendations": ["더 안전한 상품 추가 고려", "정기적인 포트폴리오 검토"]
        }

# 포트폴리오 서비스 인스턴스
portfolio_service = PortfolioService()
