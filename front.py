import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# 페이지 설정
st.set_page_config(
    page_title="주식 뉴스 분석 대시보드",
    page_icon="📈",
    layout="wide"
)

# 제목
st.title("📈 주식 뉴스 분석 대시보드")

# 뉴스 URL 입력
news_url = st.text_input("뉴스 URL을 입력하세요", "https://example.com/news/123")

# 샘플 데이터 생성 함수
def generate_sample_data():
    # 샘플 뉴스 데이터
    news_data = {
        "title": "삼성전자, AI 칩 개발로 주가 상승세",
        "content": "삼성전자가 새로운 AI 칩 개발을 발표하며 주가가 상승세를 보이고 있습니다. 이번 개발은 기존 대비 30% 이상의 성능 향상을 기대할 수 있으며, 시장 점유율 확대가 예상됩니다.",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "keywords": ["삼성전자", "AI", "반도체", "주가상승"],
        "sentiment": {
            "삼성전자": 0.8,
            "AI": 0.7,
            "반도체": 0.6,
            "주가상승": 0.9
        }
    }
    
    # 샘플 주가 데이터
    dates = pd.date_range(end=datetime.now(), periods=30)
    stock_data = pd.DataFrame({
        "date": dates,
        "price": [random.uniform(70000, 80000) for _ in range(30)]
    })
    
    # 유사 뉴스 데이터
    similar_news = [
        {
            "title": "삼성전자, AI 반도체 시장 진출",
            "date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "sentiment": 0.75
        },
        {
            "title": "반도체 업계, AI 칩 개발 경쟁 가속화",
            "date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
            "sentiment": 0.65
        }
    ]
    
    return news_data, stock_data, similar_news

# 메인 컨테이너
if st.button("분석 시작"):
    with st.spinner("뉴스를 분석중입니다..."):
        # 샘플 데이터 생성
        news_data, stock_data, similar_news = generate_sample_data()
        
        # 1. 뉴스 요약 및 키워드 섹션
        st.header("📰 뉴스 요약 및 키워드")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("뉴스 요약")
            st.write(news_data["content"])
            
        with col2:
            st.subheader("주요 키워드")
            for keyword, sentiment in news_data["sentiment"].items():
                st.metric(keyword, f"{sentiment*100:.1f}% 긍정도")
        
        # 2. 키워드별 주가 영향
        st.header("📊 키워드별 주가 영향")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(news_data["sentiment"].keys()),
            y=list(news_data["sentiment"].values()),
            name="긍정도"
        ))
        fig.update_layout(title="키워드별 긍정도 분석")
        st.plotly_chart(fig)
        
        # 3. 유사 뉴스 및 주가 흐름
        st.header("🔄 유사 뉴스 및 주가 흐름")
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("유사 뉴스")
            for news in similar_news:
                st.write(f"- {news['date']}: {news['title']} (긍정도: {news['sentiment']*100:.1f}%)")
        
        with col4:
            st.subheader("주가 추이")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=stock_data["date"],
                y=stock_data["price"],
                mode="lines",
                name="주가"
            ))
            fig.update_layout(title="최근 30일 주가 추이")
            st.plotly_chart(fig)
        
        # 4. 최종 결론
        st.header("🎯 분석 결론")
        st.info("""
        - 현재 뉴스는 삼성전자의 AI 칩 개발에 대한 긍정적인 내용을 담고 있습니다.
        - 주요 키워드들의 긍정도가 높게 나타나 주가 상승 가능성이 있습니다.
        - 과거 유사 뉴스들의 긍정도와 주가 상승 패턴이 유사한 것으로 보입니다.
        - 단기적으로 주가 상승이 예상되나, 시장 변동성에 주의가 필요합니다.
        """)
