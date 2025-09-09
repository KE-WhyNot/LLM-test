# 금융 포트폴리오 추천 API

은행 상품과 청년 정책을 활용한 AI 기반 포트폴리오 추천 서비스입니다.

## 🚀 주요 기능

- **AI 데이터 전처리**: Vertex AI를 사용한 은행 상품 및 청년 정책 데이터 전처리
- **포트폴리오 추천**: Gemini를 활용한 개인화된 포트폴리오 추천
- **MSA 통신**: 다른 마이크로서비스와의 통신 및 데이터 교환
- **Mock 모드**: 실제 MSA 서비스 없이도 테스트 가능한 샘플 데이터 제공
- **자동 데이터 변환**: API 응답 구조를 내부 스키마로 자동 변환

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL
- **AI**: Google Vertex AI (Gemini 1.5 Pro)
- **External APIs**: 은행 상품 API, 온통청년 API
- **Container**: Docker, Docker Compose

## 📋 사전 요구사항

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (선택사항)
- Google Cloud Platform 계정 (Vertex AI 사용)

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd financial-portfolio-api
```

### 2. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp env.example .env
# .env 파일을 편집하여 필요한 설정값 입력
```

### 5. 데이터베이스 설정
```bash
# PostgreSQL 설치 및 실행
# 데이터베이스 생성
createdb financial_portfolio
```

### 6. 애플리케이션 실행
```bash
python main.py
```

### Docker를 사용한 실행
```bash
# Docker Compose로 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f app
```

## 📖 API 문서

애플리케이션 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 환경 변수

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | ✅ |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP 서비스 계정 키 파일 경로 | ✅ |
| `PROJECT_ID` | Google Cloud 프로젝트 ID | ✅ |
| `LOCATION` | Vertex AI 리전 | ✅ |
| `BANK_API_KEY` | 은행 상품 API 키 | ✅ |
| `BANK_API_URL` | 은행 상품 API URL | ✅ |
| `YOUTH_POLICY_API_KEY` | 청년 정책 API 키 | ✅ |
| `YOUTH_POLICY_API_URL` | 청년 정책 API URL | ✅ |

## 📊 데이터베이스 스키마

### 주요 테이블
- `users`: 사용자 정보
- `bank_products`: 은행 상품 정보
- `youth_policies`: 청년 정책 정보
- `user_portfolios`: 사용자 포트폴리오
- `recommendation_history`: 추천 히스토리

## 🔄 API 엔드포인트

### 전처리 API
- `POST /api/v1/bank-products/preprocess` - 은행 상품 전처리
- `POST /api/v1/youth-policies/preprocess` - 청년 정책 전처리

### 포트폴리오 추천 API
- `POST /api/v1/portfolio/recommend/{user_id}` - AI 포트폴리오 추천

### 테스트 API
- `GET /health` - 서비스 헬스 체크
- `GET /sample-data` - 샘플 데이터 조회 (Mock 모드)

## 🧪 테스트

```bash
# 단위 테스트 실행
pytest

# API 테스트
curl -X GET "http://localhost:8000/health"
```

## 📈 모니터링

- **헬스 체크**: `GET /health`
- **로그**: 애플리케이션 로그를 통해 API 호출 및 오류 추적

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.
