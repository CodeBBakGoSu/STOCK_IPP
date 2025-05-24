import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# from datetime import datetime, timedelta # 사용되지 않으므로 주석 처리 또는 삭제
# import random # 사용되지 않으므로 주석 처리 또는 삭제
from news_analysis.news_analyzer import NewsAnalyzer # NewsAnalyzer 임포트
import re # 정규표현식 사용을 위해 추가
import yfinance as yf # yfinance 임포트
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from dotenv import load_dotenv
from mock_database import get_similar_events, get_event_types, COMPANIES_DATA
import numpy as np

# 환경 변수 로드
load_dotenv()

# Gemini API 설정
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일에 GOOGLE_API_KEY를 설정해주세요.")
    st.stop()

# Gemini 모델 설정
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

# 페이지 설정
st.set_page_config(
    page_title="주식 뉴스 분석 대시보드",
    page_icon="📈",
    layout="wide"
)

# 제목
st.title("📈 주식 뉴스 분석 대시보드")

# 뉴스 내용 입력
news_text = st.text_area("뉴스 내용을 입력하세요", "여기에 뉴스 기사 내용을 붙여넣으세요.", height=200)

# 세션 상태 초기화
if 'analyzer_instance' not in st.session_state:
    st.session_state.analyzer_instance = None
if 'keywords_ml' not in st.session_state: # KeyBERT 결과
    st.session_state.keywords_ml = []
if 'keywords_llm' not in st.session_state:
    st.session_state.keywords_llm = []
if 'current_news_company' not in st.session_state:
    st.session_state.current_news_company = None
if 'selected_keyword_for_history' not in st.session_state:
    st.session_state.selected_keyword_for_history = None
if 'selected_keyword_source' not in st.session_state: # 키워드 출처 (ml/llm)
    st.session_state.selected_keyword_source = None

def extract_market_sentiment(text):
    """텍스트에서 시장 분위기 관련 키워드를 추출합니다."""
    # 기본 시장 분위기 키워드
    MARKET_KEYWORDS = {
        "코스피": "지수",
        "코스닥": "지수",
        "혼조세": "시장 동향",
        "상승세": "시장 동향",
        "하락세": "시장 동향",
        "강보합": "시장 동향",
        "약보합": "시장 동향",
        "보합세": "시장 동향",
        "마감": "시점",
        "출발": "시점",
        "긴축": "통화정책",
        "완화": "통화정책",
        "기준금리": "통화정책",
        "연준": "통화정책",
        "매수세": "투자자 동향",
        "매도세": "투자자 동향",
        "순매수": "투자자 동향",
        "순매도": "투자자 동향",
        "기관": "투자자",
        "외국인": "투자자",
        "개인": "투자자"
    }
    
    # 텍스트에서 키워드 찾기
    found_keywords = {}
    for keyword, category in MARKET_KEYWORDS.items():
        if keyword in text:
            if category not in found_keywords:
                found_keywords[category] = []
            found_keywords[category].append(keyword)
    
    return found_keywords

def get_stock_code_from_keyword_web_search(keyword):
    """키워드(회사명)의 주식 코드를 검색합니다."""
    if not keyword:
        return None
    try:
        # 시장 분위기 키워드 분석
        market_keywords = extract_market_sentiment(keyword)
        if market_keywords:
            # 지수가 포함된 경우
            if "지수" in market_keywords:
                if "코스피" in market_keywords["지수"]:
                    return "^KS11"
                elif "코스닥" in market_keywords["지수"]:
                    return "^KQ11"
            
            # 시장 전반적인 키워드인 경우
            if any(category in market_keywords for category in ["시장 동향", "통화정책", "투자자 동향"]):
                return "MARKET_SENTIMENT"
        
        # 지수 처리
        indices = {
            "코스피": "^KS11",
            "코스닥": "^KQ11",
            "코스피200": "^KS200"
        }
        if keyword in indices:
            return indices[keyword]
            
        # 먼저 COMPANIES_DATA에서 검색
        for company in COMPANIES_DATA:
            if keyword.lower() in company["name"].lower():
                return company["ticker"].split('.')[0]  # .KS 또는 .KQ 제외한 코드만 반환
                
        # COMPANIES_DATA에서 찾지 못한 경우 웹 검색 시도
        search_query = f"{keyword} 주식 코드 KRX"
        st.write(f"'{keyword}'에 대한 주식 코드를 검색 중...")
        
        # 정규표현식 패턴
        code_patterns = [
            r'(?:종목코드|주식코드)[:\s]*(\d{6})',
            r'KRX[:\s]*(\d{6})',
            r'\((\d{6})\)',
            r'\b(\d{6})\b'
        ]
        
        return None
        
    except Exception as e:
        st.error(f"주식 코드 검색 중 오류 발생: {e}")
        return None

def get_stock_data_around_event(ticker, event_date_str, days_before=30, days_after=30):
    """이벤트 발생일 전후의 주가 데이터를 가져옵니다."""
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        start_date = event_date - timedelta(days=days_before)
        end_date = event_date + timedelta(days=days_after)
        
        # 지수 처리
        if ticker.startswith('^'):
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        else:
            # 한국 주식의 경우 .KS(코스피) 또는 .KQ(코스닥) 접미사 처리
            if not (ticker.endswith('.KS') or ticker.endswith('.KQ')):
                ticker_ks = f"{ticker}.KS"
                ticker_kq = f"{ticker}.KQ"
                
                # 코스피와 코스닥 모두 시도
                data_ks = yf.download(ticker_ks, start=start_date, end=end_date, progress=False)
                data_kq = yf.download(ticker_kq, start=start_date, end=end_date, progress=False)
                
                # 데이터가 있는 쪽 사용
                if not data_ks.empty:
                    data = data_ks
                elif not data_kq.empty:
                    data = data_kq
                else:
                    st.warning(f"{ticker}에 대한 주가 데이터를 찾을 수 없습니다.")
                    return None
            else:
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            st.warning(f"{ticker}에 대한 주가 데이터를 찾을 수 없습니다.")
            return None
            
        # 주가 데이터 정규화 (시작일 기준 100으로)
        first_price = data['Close'].iloc[0]
        data['Normalized'] = (data['Close'] / first_price) * 100
        
        # 거래량 데이터 추가
        if 'Volume' in data.columns:  # 지수의 경우 거래량이 없을 수 있음
            data['Volume_MA5'] = data['Volume'].rolling(window=5).mean()
        else:
            data['Volume'] = 0
            data['Volume_MA5'] = 0
        
        return data
        
    except Exception as e:
        st.error(f"{ticker} 주가 데이터 조회 중 오류 발생: {e}")
        return None

def extract_keywords_with_gemini(text):
    """Gemini를 사용하여 뉴스 텍스트에서 키워드를 추출합니다."""
    try:
        prompt = f"""
        다음 뉴스 텍스트에서 주요 키워드를 추출해주세요.
        특히 다음 항목들에 주의해서 추출해주세요:
        
        1. 기업명 (예: 삼성전자, SK하이닉스, NAVER 등)
        
        2. 주요 이벤트 유형 (다음 중 하나와 일치하도록):
        - 유상증자/무상증자
        - 실적발표 (긍정/부정)
        - 신제품출시 (성공적/반응미지근)
        - M&A (인수/피인수)
        - 자사주매입/소각
        - 정부규제강화/정책수혜
        - 대규모공급계약/계약파기
        - CEO교체/리스크
        - 특허취득/분쟁
        - 배당발표/삭감
        - 해외시장진출
        - 공장화재/생산차질
        - 투자유치
        - 임상시험 (성공/실패)
        - ESG등급변동
        - 데이터센터장애
        - 지분매각
        
        3. 중요한 수치나 지표 (금액, 비율, 기간 등)

        각 키워드마다 중요도를 0에서 1 사이의 숫자로 표현해주세요.
        
        응답 형식:
        키워드1, 0.9
        키워드2, 0.8
        키워드3, 0.7
        
        뉴스 텍스트:
        {text}
        """
        
        st.write("### Gemini API 호출 로그")
        st.write("보내는 프롬프트:")
        st.code(prompt)
        
        response = model.generate_content(prompt)
        
        st.write("Gemini API 응답:")
        st.code(response.text)
        
        if not response or not response.text:
            st.warning("Gemini API가 유효한 응답을 반환하지 않았습니다.")
            return []
            
        # 응답 텍스트를 파싱하여 (키워드, 점수) 형태의 리스트로 변환
        keywords = []
        for line in response.text.split('\n'):
            if ',' in line:
                try:
                    keyword, score = line.split(',')
                    score = float(score.strip())
                    if 0 <= score <= 1:  # 유효한 점수 범위 확인
                        keywords.append((keyword.strip(), score))
                    else:
                        st.warning(f"유효하지 않은 점수 범위: {score} (키워드: {keyword})")
                except (ValueError, IndexError) as e:
                    st.warning(f"라인 파싱 실패: {line} (에러: {str(e)})")
                    continue
                    
        # 결과가 없으면 경고
        if not keywords:
            st.warning("키워드를 추출하지 못했습니다. 파싱된 결과가 없습니다.")
            return []
            
        st.write("### 추출된 키워드:")
        for keyword, score in keywords:
            st.write(f"- {keyword}: {score}")
            
        return sorted(keywords, key=lambda x: x[1], reverse=True)[:5]  # 상위 5개 반환
        
    except Exception as e:
        st.error(f"Gemini API 호출 중 오류 발생: {str(e)}")
        st.error("전체 에러:", exc_info=True)
        return []

def plot_stock_data(data, event_date, company_name):
    """주가 데이터를 시각화합니다."""
    fig = go.Figure()
    
    # 주가 차트
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Normalized'],
        mode='lines',
        name='정규화된 주가 (시작=100)',
        line=dict(color='blue')
    ))
    
    # 거래량 차트
    fig.add_trace(go.Bar(
        x=data.index,
        y=data['Volume'],
        name='거래량',
        yaxis='y2',
        opacity=0.3
    ))
    
    # 5일 이동평균 거래량
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Volume_MA5'],
        mode='lines',
        name='5일 이동평균 거래량',
        yaxis='y2',
        line=dict(color='red', dash='dot')
    ))
    
    # 이벤트 발생일 표시 (datetime 객체를 타임스탬프로 변환)
    if isinstance(event_date, str):
        event_date_obj = datetime.strptime(event_date, "%Y-%m-%d")
    else:
        event_date_obj = event_date
        
    fig.add_vline(
        x=event_date_obj.timestamp() * 1000,  # 밀리초 단위 타임스탬프로 변환
        line_width=1.5,
        line_dash="dash",
        line_color="red",
        annotation_text="이벤트 발생일",
        annotation_position="top right"
    )
    
    # 레이아웃 설정
    fig.update_layout(
        title=f"{company_name} 주가 및 거래량 추이",
        xaxis_title="날짜",
        yaxis_title="정규화된 주가 (시작=100)",
        yaxis2=dict(
            title="거래량",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig

def plot_event_comparison(events, normalize=True):
    """여러 이벤트의 주가 데이터를 비교 그래프로 표시합니다."""
    fig = go.Figure()
    
    # 이벤트 데이터 처리
    for event in events:
        df = event['price_series']
        company = event['company']
        event_date = datetime.strptime(event['event_date'], "%Y-%m-%d")
        
        # 이벤트 날짜 기준으로 날짜 인덱스 조정
        df['days_from_event'] = (df['Date'] - event_date).dt.days
        
        if normalize:
            # 이벤트 당일 종가를 100으로 정규화
            event_day_price = df.loc[df['days_from_event'] == 0, 'Close'].iloc[0]
            normalized_prices = (df['Close'] / event_day_price) * 100
            fig.add_trace(go.Scatter(
                x=df['days_from_event'],
                y=normalized_prices,
                name=f"{company} (정규화)",
                mode='lines',
                hovertemplate="일자: %{x}일<br>정규화 주가: %{y:.2f}%<extra></extra>"
            ))
        else:
            fig.add_trace(go.Scatter(
                x=df['days_from_event'],
                y=df['Close'],
                name=company,
                mode='lines',
                hovertemplate="일자: %{x}일<br>주가: %{y:,.0f}원<extra></extra>"
            ))
        
        # 거래량 추가 (두 번째 y축)
        volume_ma5 = df['Volume'].rolling(window=5).mean()
        fig.add_trace(go.Bar(
            x=df['days_from_event'],
            y=df['Volume'],
            name=f"{company} 거래량",
            yaxis='y2',
            opacity=0.3,
            hovertemplate="일자: %{x}일<br>거래량: %{y:,.0f}<extra></extra>"
        ))
        
        # 5일 이동평균 거래량
        fig.add_trace(go.Scatter(
            x=df['days_from_event'],
            y=volume_ma5,
            name=f"{company} 5일 이동평균 거래량",
            yaxis='y2',
            line=dict(dash='dot'),
            hovertemplate="일자: %{x}일<br>5일 평균 거래량: %{y:,.0f}<extra></extra>"
        ))
    
    # 이벤트 발생일 표시
    fig.add_vline(
        x=0,
        line_width=1.5,
        line_dash="dash",
        line_color="red",
        annotation_text="이벤트 발생일",
        annotation_position="top right"
    )
    
    # 레이아웃 설정
    title_text = "이벤트 전후 주가 변동 비교"
    if normalize:
        title_text += " (이벤트 발생일=100)"
    
    fig.update_layout(
        title=title_text,
        xaxis_title="이벤트 발생일로부터의 일수",
        yaxis_title="정규화된 주가 (%)" if normalize else "주가 (원)",
        yaxis2=dict(
            title="거래량",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        height=600
    )
    
    # x축 범위 설정 (-30일 ~ +30일)
    fig.update_xaxes(range=[-30, 30])
    
    return fig

# 메인 컨테이너
if st.button("뉴스 분석 시작", key="start_analysis_button"):
    if not news_text or news_text == "여기에 뉴스 기사 내용을 붙여넣으세요.":
        st.warning("분석할 뉴스 내용을 입력해주세요.")
    else:
        with st.spinner("뉴스를 분석중입니다..."):
            try:
                # Gemini API를 사용하여 키워드 추출
                st.session_state.keywords_llm = extract_keywords_with_gemini(news_text)
                
                # KeyBERT를 사용한 키워드 추출
                st.session_state.analyzer_instance = NewsAnalyzer(csv_path=None)
                st.session_state.keywords_ml = st.session_state.analyzer_instance.extract_keywords(news_text, top_n=5)
                
                # 첫 번째 키워드를 현재 뉴스 기업으로 설정
                if st.session_state.keywords_llm:
                    st.session_state.current_news_company = st.session_state.keywords_llm[0][0]
                else:
                    st.session_state.current_news_company = "현재 기사 기업"
                
                st.session_state.selected_keyword_for_history = None
                st.session_state.selected_keyword_source = None
            except Exception as e:
                st.error(f"뉴스 분석 중 오류 발생: {e}")
                st.session_state.analyzer_instance = None
            st.rerun()

if st.session_state.analyzer_instance:
    analyzer = st.session_state.analyzer_instance
    
    st.header("📰 뉴스 요약")
    summary = analyzer.textrank_summarize(news_text)
    st.write(summary)

    st.header("🔑 주요 키워드 비교")
    st.markdown("키워드를 클릭하여 관련 주가 추이를 분석할 수 있습니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("머신러닝 기반 (KeyBERT)")
        if st.session_state.keywords_ml:
            for keyword, score in st.session_state.keywords_ml:
                stock_code = get_stock_code_from_keyword_web_search(keyword)
                button_label = f"{keyword} ({score:.2f})"
                if stock_code:
                    button_label += f" - 코드: {stock_code}"
                
                if st.button(button_label, key=f"ml_keyword_{keyword}"):
                    st.session_state.selected_keyword_for_history = keyword
                    st.session_state.selected_keyword_source = "ML"
                    st.session_state.selected_stock_code = stock_code
        else:
            st.write("추출된 키워드가 없습니다.")

    with col2:
        st.subheader("LLM 기반 (Gemini)")
        if st.session_state.keywords_llm:
            for keyword, score in st.session_state.keywords_llm:
                stock_code = get_stock_code_from_keyword_web_search(keyword)
                button_label = f"{keyword} (중요도: {score:.2f})"
                if stock_code:
                    button_label += f" - 코드: {stock_code}"

                if st.button(button_label, key=f"llm_keyword_{keyword}"):
                    st.session_state.selected_keyword_for_history = keyword
                    st.session_state.selected_keyword_source = "LLM"
                    st.session_state.selected_stock_code = stock_code
        else:
            st.write("추출된 키워드가 없습니다.")

    st.header("😊😐😠 감성 분석")
    sentiment_result = analyzer.analyze_sentiment(news_text)
    if sentiment_result:
        fig_sentiment = go.Figure()
        fig_sentiment.add_trace(go.Bar(x=list(sentiment_result.keys()), y=list(sentiment_result.values()), marker_color=['green', 'blue', 'red']))
        fig_sentiment.update_layout(title="감성 분석 결과")
        st.plotly_chart(fig_sentiment)
        dominant_sentiment = max(sentiment_result, key=sentiment_result.get)
        st.info(f"가장 우세한 감성: **{dominant_sentiment}** (점수: {sentiment_result[dominant_sentiment]:.2f})")
    else:
        st.write("감성 분석을 수행할 수 없습니다.")

    if st.session_state.selected_keyword_for_history:
        selected_keyword = st.session_state.selected_keyword_for_history
        source_display = f" ({st.session_state.selected_keyword_source}에서 선택)"
        
        st.header(f"🔍 '{selected_keyword}' 관련 분석{source_display}")
        
        # 시장 분위기 분석
        market_keywords = extract_market_sentiment(selected_keyword)
        
        if market_keywords:
            st.subheader("📊 시장 분위기 분석")
            
            # 키워드 분석 결과 표시
            st.write("### 감지된 키워드")
            for category, keywords in market_keywords.items():
                st.write(f"- {category}: {', '.join(keywords)}")
            
            # 지수 관련 분석
            if "지수" in market_keywords:
                st.write("### 주요 지수 동향")
                # KOSPI, KOSDAQ 지수 비교 차트
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                if "코스피" in market_keywords["지수"]:
                    kospi_data = get_stock_data_around_event("^KS11", end_date.strftime("%Y-%m-%d"), days_before=30, days_after=0)
                    if kospi_data is not None:
                        st.write("#### KOSPI 지수")
                        fig_kospi = plot_stock_data(kospi_data, end_date.strftime("%Y-%m-%d"), "KOSPI")
                        st.plotly_chart(fig_kospi)
                
                if "코스닥" in market_keywords["지수"]:
                    kosdaq_data = get_stock_data_around_event("^KQ11", end_date.strftime("%Y-%m-%d"), days_before=30, days_after=0)
                    if kosdaq_data is not None:
                        st.write("#### KOSDAQ 지수")
                        fig_kosdaq = plot_stock_data(kosdaq_data, end_date.strftime("%Y-%m-%d"), "KOSDAQ")
                        st.plotly_chart(fig_kosdaq)
            
            # 투자자 동향 분석
            if "투자자" in market_keywords or "투자자 동향" in market_keywords:
                st.write("### 투자자 동향")
                # 최근 5일간의 투자자별 순매수 데이터 (예시 데이터)
                investor_data = pd.DataFrame({
                    "날짜": pd.date_range(end=datetime.now(), periods=5, freq='B')[::-1],
                    "기관": np.random.randint(-1000, 1000, 5),
                    "외국인": np.random.randint(-1000, 1000, 5),
                    "개인": np.random.randint(-1000, 1000, 5)
                })
                
                fig_investors = go.Figure()
                for investor in ["기관", "외국인", "개인"]:
                    fig_investors.add_trace(go.Bar(
                        name=investor,
                        x=investor_data["날짜"],
                        y=investor_data[investor],
                        text=investor_data[investor].apply(lambda x: f"{x:,}억원"),
                        textposition='auto',
                    ))
                
                fig_investors.update_layout(
                    title="최근 5일간 투자자별 순매수 동향",
                    barmode='group',
                    yaxis_title="순매수액 (억원)"
                )
                st.plotly_chart(fig_investors)
            
            # 통화정책 관련 분석
            if "통화정책" in market_keywords:
                st.write("### 통화정책 영향 분석")
                # 금리 민감도가 높은 업종별 등락률 (예시 데이터)
                sectors = ['은행', '증권', '건설', '철강', 'IT']
                changes = np.random.uniform(-3, 3, len(sectors))
                
                fig_sectors = go.Figure([go.Bar(
                    x=sectors,
                    y=changes,
                    text=[f"{x:.1f}%" for x in changes],
                    textposition='auto',
                )])
                fig_sectors.update_layout(
                    title="금리 민감 업종 등락률",
                    yaxis_title="등락률 (%)"
                )
                st.plotly_chart(fig_sectors)
            
            # 시장 동향 요약
            if "시장 동향" in market_keywords:
                sentiment = "혼조" if "혼조세" in selected_keyword else \
                           "상승" if "상승세" in selected_keyword else \
                           "하락" if "하락세" in selected_keyword else "보합"
                
                st.info(f"""
                💡 시장 동향 분석:
                - 현재 시장 분위기: {sentiment}
                - 주요 특징: {', '.join(market_keywords.get('시장 동향', []))}
                - 관련 이벤트: {', '.join(market_keywords.get('통화정책', []) + market_keywords.get('투자자 동향', []))}
                """)
        
        else:
            # 기존 개별 종목 분석 로직
            stock_code = st.session_state.get('selected_stock_code')
            if stock_code:
                current_date = datetime.now().strftime("%Y-%m-%d")
                stock_data = get_stock_data_around_event(stock_code, current_date)
                
                if stock_data is not None and not stock_data.empty:
                    fig = plot_stock_data(stock_data, current_date, selected_keyword)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 변동률 계산 및 표시
                    try:
                        price_changes = {
                            "1주일": ((stock_data['Close'].iloc[5] / stock_data['Close'].iloc[0]) - 1) * 100 if len(stock_data) > 5 else None,
                            "1개월": ((stock_data['Close'].iloc[20] / stock_data['Close'].iloc[0]) - 1) * 100 if len(stock_data) > 20 else None,
                            "3개월": ((stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[0]) - 1) * 100 if len(stock_data) > 60 else None
                        }
                        
                        cols = st.columns(3)
                        for i, (period, change) in enumerate(price_changes.items()):
                            with cols[i]:
                                if change is not None:
                                    if isinstance(change, (int, float)):
                                        st.metric(period, f"{change:.2f}%")
                                    else:
                                        st.metric(period, "계산 불가")
                                else:
                                    st.metric(period, "데이터 없음")
                                
                    except Exception as e:
                        st.error(f"변동률 계산 중 오류 발생: {str(e)}")
                else:
                    st.write(f"'{selected_keyword}' ({stock_code})의 주가 정보를 가져오는데 실패했습니다.")
            else:
                st.info(f"'{selected_keyword}'는 시장 전반적인 키워드가 아니며, 개별 종목 정보도 찾을 수 없습니다.")

# 디버깅/테스트용 세션 초기화 버튼
if st.sidebar.button("전체 분석 상태 초기화"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
