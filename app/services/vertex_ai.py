import vertexai
from vertexai.generative_models import GenerativeModel
from typing import List, Dict, Any, Optional
from app.schemas.user import UserProfile
from app.schemas.portfolio import PortfolioRecommendation, PortfolioItem
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)

class VertexAIService:
    """Google Vertex AI 서비스"""
    
    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.5-pro")
    
    async def preprocess_financial_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """금융 데이터 전처리"""
        try:
            prompt = f"""
            다음 금융 데이터를 분석하고 구조화해주세요:
            
            원본 데이터:
            {json.dumps(raw_data, ensure_ascii=False, indent=2)}
            
            다음 형식으로 응답해주세요:
            {{
                "product_type": "상품 유형",
                "risk_level": 1-5 숫자,
                "expected_return": 예상 수익률,
                "min_investment": 최소 투자 금액,
                "max_investment": 최대 투자 금액,
                "term_months": 기간(월),
                "features": ["특징1", "특징2"],
                "suitability": "적합한 투자자 유형"
            }}
            """
            
            response = self.model.generate_content(prompt)
            processed_data = json.loads(response.text)
            
            logger.info("금융 데이터 전처리 완료")
            return processed_data
            
        except Exception as e:
            logger.error(f"금융 데이터 전처리 실패: {e}")
            raise Exception(f"데이터 전처리 실패: {str(e)}")
    
    async def generate_portfolio_recommendation(
        self, 
        user_profile: UserProfile, 
        available_products: List[Dict[str, Any]],
        youth_policies: List[Dict[str, Any]]
    ) -> PortfolioRecommendation:
        """포트폴리오 추천 생성"""
        try:
            prompt = f"""
            다음 사용자 정보를 바탕으로 최적의 포트폴리오를 추천해주세요:
            
            사용자 프로필:
            - 나이: {user_profile.age}세
            - 소득분위: {user_profile.income_level}
            - 총 자산: {user_profile.total_assets}원
            - 투자성향: {user_profile.investment_preference}
            - 관심 종목: {', '.join(user_profile.interest_sectors)}
            - 리스크 허용도: {user_profile.risk_tolerance}/10
            
            사용 가능한 금융 상품:
            {json.dumps(available_products, ensure_ascii=False, indent=2)}
            
            청년 정책:
            {json.dumps(youth_policies, ensure_ascii=False, indent=2)}
            
            다음 형식으로 포트폴리오를 추천해주세요:
            {{
                "total_investment_amount": 총 투자 금액,
                "portfolio_items": [
                    {{
                        "bank_product_id": 상품ID,
                        "product_name": "상품명",
                        "bank_name": "은행명",
                        "product_type": "상품유형",
                        "allocation_percentage": 배분비율,
                        "investment_amount": 투자금액,
                        "expected_return": 예상수익률,
                        "risk_level": 리스크레벨
                    }}
                ],
                "expected_total_return": 예상총수익률,
                "total_risk_score": 총리스크점수,
                "recommendation_reason": "추천이유",
                "confidence_score": 신뢰도점수
            }}
            
            주의사항:
            1. 총 배분 비율은 100%가 되어야 합니다
            2. 사용자의 리스크 허용도에 맞는 상품을 선택하세요
            3. 청년 정책을 활용할 수 있는 상품을 우선 고려하세요
            4. 분산투자 원칙을 적용하세요
            """
            
            response = self.model.generate_content(prompt)
            recommendation_data = json.loads(response.text)
            
            # PortfolioRecommendation 객체 생성
            portfolio_items = []
            for item_data in recommendation_data.get("portfolio_items", []):
                portfolio_item = PortfolioItem(
                    bank_product_id=item_data["bank_product_id"],
                    product_name=item_data["product_name"],
                    bank_name=item_data["bank_name"],
                    product_type=item_data["product_type"],
                    allocation_percentage=Decimal(str(item_data["allocation_percentage"])),
                    investment_amount=Decimal(str(item_data["investment_amount"])),
                    expected_return=Decimal(str(item_data.get("expected_return", 0))),
                    risk_level=item_data["risk_level"]
                )
                portfolio_items.append(portfolio_item)
            
            recommendation = PortfolioRecommendation(
                user_id=user_profile.id if hasattr(user_profile, 'id') else 0,
                total_investment_amount=Decimal(str(recommendation_data["total_investment_amount"])),
                portfolio_items=portfolio_items,
                expected_total_return=Decimal(str(recommendation_data["expected_total_return"])),
                total_risk_score=Decimal(str(recommendation_data["total_risk_score"])),
                recommendation_reason=recommendation_data["recommendation_reason"],
                confidence_score=Decimal(str(recommendation_data.get("confidence_score", 0.8))),
                created_at=datetime.now()
            )
            
            logger.info("포트폴리오 추천 생성 완료")
            return recommendation
            
        except Exception as e:
            logger.error(f"포트폴리오 추천 생성 실패: {e}")
            raise Exception(f"포트폴리오 추천 실패: {str(e)}")
    
    async def analyze_portfolio_risk(self, portfolio_items: List[PortfolioItem]) -> Dict[str, Any]:
        """포트폴리오 리스크 분석"""
        try:
            prompt = f"""
            다음 포트폴리오의 리스크를 분석해주세요:
            
            포트폴리오 구성:
            {json.dumps([item.dict() for item in portfolio_items], ensure_ascii=False, indent=2)}
            
            다음 형식으로 리스크 분석 결과를 제공해주세요:
            {{
                "overall_risk_score": 전체리스크점수,
                "risk_breakdown": {{
                    "credit_risk": 신용리스크,
                    "market_risk": 시장리스크,
                    "liquidity_risk": 유동성리스크,
                    "concentration_risk": 집중리스크
                }},
                "risk_factors": ["리스크요인1", "리스크요인2"],
                "mitigation_strategies": ["완화전략1", "완화전략2"],
                "recommendations": ["개선권고1", "개선권고2"]
            }}
            """
            
            response = self.model.generate_content(prompt)
            risk_analysis = json.loads(response.text)
            
            logger.info("포트폴리오 리스크 분석 완료")
            return risk_analysis
            
        except Exception as e:
            logger.error(f"포트폴리오 리스크 분석 실패: {e}")
            raise Exception(f"리스크 분석 실패: {str(e)}")
