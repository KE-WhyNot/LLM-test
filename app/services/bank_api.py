import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.schemas.bank_product import BankProductCreate
from app.database.models import BankProduct
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class BankAPIService:
    """은행 상품 API 서비스"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def fetch_products(self, product_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """은행 상품 정보 조회"""
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if product_type:
                    params["product_type"] = product_type
                
                response = await client.get(
                    f"{self.base_url}/products",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("data", [])
                
        except httpx.HTTPError as e:
            logger.error(f"은행 API 요청 실패: {e}")
            raise Exception(f"은행 상품 조회 실패: {str(e)}")
        except Exception as e:
            logger.error(f"은행 API 처리 중 오류: {e}")
            raise
    
    async def fetch_product_detail(self, product_code: str) -> Dict[str, Any]:
        """특정 상품 상세 정보 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/products/{product_code}",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("data", {})
                
        except httpx.HTTPError as e:
            logger.error(f"은행 상품 상세 조회 실패: {e}")
            raise Exception(f"상품 상세 조회 실패: {str(e)}")
    
    def sync_products_to_db(self, products: List[Dict[str, Any]], db: Session) -> int:
        """API에서 받은 상품 정보를 DB에 동기화"""
        synced_count = 0
        
        for product_data in products:
            try:
                # 기존 상품 확인
                existing_product = db.query(BankProduct).filter(
                    BankProduct.product_code == product_data.get("product_code")
                ).first()
                
                if existing_product:
                    # 기존 상품 업데이트
                    existing_product.product_name = product_data.get("product_name", existing_product.product_name)
                    existing_product.interest_rate = product_data.get("interest_rate", existing_product.interest_rate)
                    existing_product.min_amount = product_data.get("min_amount", existing_product.min_amount)
                    existing_product.max_amount = product_data.get("max_amount", existing_product.max_amount)
                    existing_product.term_months = product_data.get("term_months", existing_product.term_months)
                    existing_product.risk_level = product_data.get("risk_level", existing_product.risk_level)
                    existing_product.product_data = product_data.get("product_data", existing_product.product_data)
                    existing_product.is_active = product_data.get("is_active", True)
                else:
                    # 새 상품 생성
                    new_product = BankProduct(
                        product_code=product_data.get("product_code"),
                        product_name=product_data.get("product_name"),
                        product_type=product_data.get("product_type"),
                        bank_name=product_data.get("bank_name"),
                        interest_rate=product_data.get("interest_rate"),
                        min_amount=product_data.get("min_amount"),
                        max_amount=product_data.get("max_amount"),
                        term_months=product_data.get("term_months"),
                        risk_level=product_data.get("risk_level"),
                        product_data=product_data.get("product_data"),
                        is_active=product_data.get("is_active", True)
                    )
                    db.add(new_product)
                
                synced_count += 1
                
            except Exception as e:
                logger.error(f"상품 동기화 실패: {product_data.get('product_code', 'Unknown')} - {e}")
                continue
        
        try:
            db.commit()
            logger.info(f"{synced_count}개 상품 동기화 완료")
        except Exception as e:
            db.rollback()
            logger.error(f"DB 커밋 실패: {e}")
            raise
        
        return synced_count
