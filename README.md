# 주식 뉴스 분석 및 시장 동향 시각화 시스템

## Project Evolution & Troubleshooting Journey

### 1. Initial Implementation Challenges

#### 1.1. Gemini API Integration
- **Challenge**: Gemini API 연동 시 모듈 임포트 및 버전 호환성 문제 발생
- **Solution**: 
  - 적절한 API 버전 선택 (`gemini-2.5-flash-preview-04-17`)
  - 환경 변수를 통한 API 키 관리 구현
  - 예외 처리 로직 강화

#### 1.2. Mock Data Structure
- **Challenge**: 초기 목업 데이터의 비체계적 구조로 인한 확장성 문제
- **Solution**: 
  - `mock_database.py` 파일 생성
  - 체계적인 데이터 구조화 (이벤트 유형, 기업 정보, 주가 데이터)
  - 실제 한국 시장 데이터 기반의 샘플 데이터 구현

### 2. Data Visualization Enhancement

#### 2.1. Chart Rendering Issues
- **Challenge**: 다양한 데이터 타입(주가, 거래량, 지수)의 통합 시각화 문제
- **Solution**:
  - Plotly 라이브러리를 활용한 인터랙티브 차트 구현
  - 정규화된 데이터 표현 방식 도입
  - 멀티 축 차트 시스템 구축

#### 2.2. Real-time Data Processing
- **Challenge**: yfinance API를 통한 실시간 데이터 처리 시 발생하는 타입 에러
- **Solution**:
  - 데이터 타입 검증 로직 추가
  - 예외 처리 강화
  - 데이터 정규화 프로세스 개선

### 3. Market Sentiment Analysis Evolution

#### 3.1. Keyword Processing Limitations
- **Initial Problem**: 단일 키워드 기반의 제한된 분석
- **Evolution Process**:
  1. 기본 키워드 매칭 시스템 구현
  2. 복합 키워드 처리 기능 추가
  3. 카테고리 기반 키워드 분류 시스템 도입

#### 3.2. Market Context Integration
- **Challenge**: 직접적인 주가 영향이 없는 시장 분위기 키워드 처리
- **Solution**:
  - 키워드 카테고리화 (지수, 시장 동향, 통화정책, 투자자 동향)
  - 컨텍스트 기반 시각화 시스템 구현
  - 종합적 시장 분석 리포트 생성

### 4. Final System Architecture

#### 4.1. Key Components
- **News Analysis Engine**
  - Gemini API 기반 키워드 추출
  - 컨텍스트 인식 시스템
  - 감성 분석 모듈

- **Data Processing Pipeline**
  - 실시간 주가 데이터 처리
  - 시장 지표 계산
  - 데이터 정규화 모듈

- **Visualization System**
  - 인터랙티브 차트 생성
  - 멀티 데이터 통합 뷰
  - 커스텀 시각화 컴포넌트

#### 4.2. Enhanced Features
- 복합 키워드 분석 및 처리
- 카테고리별 맞춤형 시각화
- 실시간 시장 동향 분석
- 투자자 동향 트래킹
- 통화정책 영향 분석

## Future Improvements
1. 실시간 데이터 피드 확장
2. 머신러닝 기반 예측 모델 통합
3. 사용자 커스터마이즈 기능 강화
4. API 연동 확대
5. 백테스팅 시스템 구현

## Technical Stack
- **Backend**: Python, Streamlit
- **API Integration**: Gemini API, yfinance
- **Data Visualization**: Plotly
- **Data Processing**: Pandas, NumPy
- **Environment Management**: dotenv

## Installation & Setup
```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 GOOGLE_API_KEY 추가

# 실행
streamlit run front.py
```

## 🎯 프로젝트 목적

- 주식 관련 뉴스 데이터 수집 및 분석
- 뉴스와 주가의 상관관계 분석
- 시각화를 통한 직관적인 데이터 분석 제공
- 에널리스트 의견과 뉴스 데이터의 연계 분석

## 📁 프로젝트 구조

```
STOCK/
├── news_analysis/          # 뉴스 분석 관련 모듈
│   └── news_analyzer.py    # 뉴스 분석 핵심 모듈
├── data/                   # 수집된 데이터 저장
├── notebooks/             # Jupyter 노트북 분석 파일
├── outputs/               # 분석 결과 출력
├── resources/             # 리소스 파일
├── news_search_api.py     # 네이버 뉴스 API 연동
├── front.py              # Streamlit 기반 대시보드
└── requirements.txt      # 프로젝트 의존성
```

## 🛠️ 주요 기능

### 1. 뉴스 분석 모듈 (`news_analyzer.py`)
- TextRank 기반 뉴스 요약
- KeyBERT 기반 키워드 추출
- finBERT 기반 감성 분석
- TF-IDF 기반 유사 뉴스 검색
- 배치 처리 기능

### 2. 데이터 수집 및 분석
- 네이버 뉴스 API를 활용한 뉴스 검색 및 수집
- 뉴스 본문 내용 자동 추출
- 키워드 기반 필터링
- CSV 형식으로 데이터 저장

### 3. 데이터 분석 대시보드 (`front.py`)
- Streamlit 기반 대시보드 구현
- 뉴스 요약 및 키워드 분석
- 키워드별 주가 영향 분석
- 유사 뉴스 및 주가 흐름 시각화
- 에널리스트 의견 통합 분석

## 👥 팀원 역할 및 작업

### 조성민
- 키워드 기반 관련 뉴스 검색 모듈 개발
- 뉴스 데이터 전처리 및 필터링
- 키워드 추출 알고리즘 개선

### 이재영
- 주식 데이터 수집 모듈 개발
- OpenAPI를 활용한 주식 코드 매핑
- 뉴스-주식 연관성 분석
- 주가 추이 데이터 수집 및 분석

### 김두섭
- Streamlit 대시보드 개발 (`front.py`)
- 데이터 시각화 구현
- 에널리스트 의견 통합 및 시각화
- 사용자 인터페이스 개선

## 🚀 개발 가이드

### 브랜치 전략
- `main`: 메인 브랜치
- `feature/news-analysis`: 뉴스 분석 관련 기능
- `feature/stock-data`: 주식 데이터 관련 기능
- `feature/visualization`: 시각화 관련 기능

### 개발 환경 설정
1. Python 3.8 이상 설치
2. 가상환경 생성 및 활성화
3. 
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 의존성 설치
```bash
pip install -r requirements.txt
```

### API 키 설정
`news_search_api.py`에 네이버 API 키 설정:
```python
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
```

## 📊 데이터 구조

### 뉴스 데이터 (`stock_news_*.csv`)
- title: 뉴스 제목
- description: 뉴스 요약
- content: 뉴스 본문
- pubDate: 발행일
- link: 원본 링크

## 🔧 기술 스택
- Python 3.8+
- Streamlit
- BeautifulSoup4
- Pandas
- Plotly
- Naver News API
- Transformers (finBERT)
- KeyBERT
- TextRank

## 📝 주의사항
- 네이버 API 사용량 제한 확인
- 데이터 수집 간격 조절 필요
- 브랜치 작업 후 PR 생성 시 코드 리뷰 필수

## 🤝 기여하기
1. 각자 담당 브랜치 생성
2. 기능 개발 및 테스트
3. PR 생성 및 코드 리뷰
4. 승인 후 main 브랜치로 병합 