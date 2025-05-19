# 주식 뉴스 분석 프로젝트 (STOCK)

이 프로젝트는 주식 관련 뉴스 데이터를 수집하고 분석하여 투자 의사결정을 지원하는 도구입니다.

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