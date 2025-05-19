# 주식 뉴스 분석 프로젝트 (STOCK)

이 프로젝트는 주식 관련 뉴스와 커뮤니티 데이터를 수집하고 분석하여 투자 의사결정을 지원하는 도구입니다.

## 🎯 프로젝트 목적

- 주식 관련 뉴스 데이터 수집 및 분석
- 투자자 커뮤니티 데이터 수집 및 분석
- 뉴스와 주가의 상관관계 분석
- 시각화를 통한 직관적인 데이터 분석 제공

## 📁 프로젝트 구조

```
STOCK/
├── news_analysis/          # 뉴스 분석 관련 모듈
├── data/                   # 수집된 데이터 저장
├── notebooks/             # Jupyter 노트북 분석 파일
├── outputs/               # 분석 결과 출력
├── resources/             # 리소스 파일
├── news_search_api.py     # 네이버 뉴스 API 연동
├── front.py              # Streamlit 기반 대시보드
├── toss_crawler.py       # 토스 투자 커뮤니티 크롤러
└── requirements.txt      # 프로젝트 의존성
```

## 🛠️ 주요 기능

### 1. 뉴스 데이터 수집 (`news_search_api.py`)
- 네이버 뉴스 API를 활용한 뉴스 검색 및 수집
- 뉴스 본문 내용 자동 추출
- 키워드 기반 필터링
- CSV 형식으로 데이터 저장

### 2. 커뮤니티 데이터 수집 (`toss_crawler.py`)
- 토스 투자 커뮤니티 댓글 수집
- Selenium을 활용한 동적 웹페이지 크롤링
- 댓글 내용과 시간 정보 저장

### 3. 데이터 분석 대시보드 (`front.py`)
- Streamlit 기반 대시보드 구현
- 뉴스 요약 및 키워드 분석
- 키워드별 주가 영향 분석
- 유사 뉴스 및 주가 흐름 시각화
- 분석 결론 제공

## 🚀 시작하기

### 환경 설정
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

### 실행 방법
1. 뉴스 데이터 수집:
```bash
python news_search_api.py
```

2. 커뮤니티 데이터 수집:
```bash
python toss_crawler.py
```

3. 대시보드 실행:
```bash
streamlit run front.py
```

## 📊 데이터 구조

### 뉴스 데이터 (`stock_news_*.csv`)
- title: 뉴스 제목
- description: 뉴스 요약
- content: 뉴스 본문
- pubDate: 발행일
- link: 원본 링크

### 커뮤니티 데이터 (`toss_community_comments_*.json`)
- timestamp: 댓글 작성 시간
- content: 댓글 내용

## 🔧 기술 스택
- Python 3.8+
- Streamlit
- Selenium
- BeautifulSoup4
- Pandas
- Plotly
- Naver News API

## 📝 주의사항
- 네이버 API 사용량 제한 확인
- 크롤링 시 웹사이트 정책 준수
- 데이터 수집 간격 조절 필요

## 🤝 기여하기
1. Fork the Project
2. Create your Feature Branch
3. Commit your Changes
4. Push to the Branch
5. Open a Pull Request 