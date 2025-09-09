"""
파일 기반 전처리 서비스
data/bank.json, data/policy.json을 읽어서 Gemini로 요약/정규화 전처리
LangChain 미사용(환경 제약) - 동일 구조를 Gemini로 대체
"""
import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_AVAILABLE = False
logger.info("FilePreprocessor: 현재 LLM 비활성화(정규화-only)")


class FilePreprocessor:
    def __init__(self) -> None:
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.gemini_api_key = ""
        self.use_mock = True  # 항상 정규화-only

    def _read_json(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def preprocess_bank(self, limit: int = 100) -> List[Dict[str, Any]]:
        raw = self._read_json('bank.json')
        container = raw.get('result') or raw
        # 다양한 후보 키 대응
        candidates = [
            container.get('bankProducts'),
            container.get('products'),
            container.get('list'),
            container.get('items'),
        ]
        items = next((lst for lst in candidates if isinstance(lst, list)), None)
        # 일부 데이터셋은 정책 리스트만 포함하므로 None일 수 있음
        if not items and isinstance(container.get('youthPolicyList'), list):
            logger.info('bank.json에 상품 리스트가 없어 정책 리스트 감지됨 → 빈 결과 반환')
            return []

        items = (items or [])[:limit]
        results: List[Dict[str, Any]] = []
        for p in items:
            results.append(self._normalize_bank(p))
        return results

    async def preprocess_policy(self, limit: int = 200) -> List[Dict[str, Any]]:
        raw = self._read_json('policy.json')
        container = raw.get('result') or raw
        candidates = [
            container.get('youthPolicyList'),
            container.get('policies'),
            container.get('list'),
            container.get('items'),
        ]
        items = next((lst for lst in candidates if isinstance(lst, list)), [])[:limit]
        results: List[Dict[str, Any]] = []
        for p in items:
            results.append(self._normalize_policy(p))
        return results

    def _normalize_bank(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "product_code": p.get("productId") or p.get("id") or p.get("code", ""),
            "product_name": p.get("productName") or p.get("name") or p.get("title", ""),
            "product_type": p.get("productType") or p.get("type") or p.get("category", ""),
            "bank_name": p.get("bankName") or p.get("bank") or p.get("issuer", ""),
            "interest_rate": float(p.get("interestRate") or p.get("rate") or 0),
            "min_amount": float(p.get("minAmount") or p.get("min") or 0),
            "max_amount": float(p.get("maxAmount") or p.get("max") or 0),
            "term_months": int(p.get("termMonths") or p.get("term") or 0),
            "risk_level": int(p.get("riskLevel") or p.get("risk") or 1),
            "features": p.get("features") or [],
            "target_customer": p.get("targetCustomer") or p.get("target") or "",
        }

    def _normalize_policy(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "policy_code": p.get("policyId") or p.get("plcyNo") or p.get("id", ""),
            "policy_name": p.get("policyName") or p.get("plcyNm") or p.get("name", ""),
            "target_age_min": int(p.get("targetAgeMin") or p.get("sprtTrgtMinAge") or 0),
            "target_age_max": int(p.get("targetAgeMax") or p.get("sprtTrgtMaxAge") or 0),
            "benefit_amount": float(p.get("benefitAmount") or p.get("bnftAmt") or 0),
            "requirements": p.get("requirements") or p.get("addAplyQlfcCndCn") or "",
            "application_period": p.get("applicationPeriod") or p.get("aplyYmd") or "",
            "policy_type": p.get("policyType") or p.get("lclsfNm") or "",
            "description": p.get("description") or p.get("plcyExplnCn") or "",
        }

    # LLM 미사용: 프롬프트 빌더 제거

    # LLM 미사용: 프롬프트 빌더 제거


file_preprocessor = FilePreprocessor()


