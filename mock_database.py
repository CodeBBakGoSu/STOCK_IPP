import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# 사용자 제공 함수 (변경 없음)
def generate_mock_stock_data(
    event_date_str,
    base_price=10000,
    volatility=0.02,
    event_impact=0.05,
    recovery_days=20,
    trend_before=0.0001,  # 이벤트 전 추세
    trend_after=0.0002,   # 이벤트 후 추세
    volume_multiplier_on_event=3  # 이벤트 당일 거래량 증가 배수
):
    """현실적인 주가 데이터를 생성합니다."""
    event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
    start_date = event_date - timedelta(days=30)
    end_date = event_date + timedelta(days=30)

    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    n = len(dates)
    prices = [] # 초기화 위치 변경 및 조건부 base_price 추가
    
    # 이벤트 발생일 인덱스 찾기
    event_idx = -1
    for idx, d in enumerate(dates):
        if d == event_date:
            event_idx = idx
            break
    if event_idx == -1 : # 만약 event_date가 dates에 없다면 (주말 등) 가장 가까운 미래의 영업일로 조정될 수 있으나, 여기서는 입력된 날짜가 영업일이라고 가정.
        # 실제로는 event_date가 영업일이 아닐 경우에 대한 처리가 필요할 수 있음. 여기서는 pandas가 영업일만 생성하므로 event_idx는 찾아짐.
        # 만약 freq='D' 등으로 변경되어 주말이 포함되고 event_date가 주말이면 문제가 될 수 있음. 현재 'B'이므로 괜찮음.
        pass


    current_price = base_price
    # 이벤트 전 가격 생성
    for i in range(event_idx):
        if not prices: # 첫 가격 설정
             prices.append(base_price * (1 - trend_before * (event_idx - i))) # 이벤트 날짜에 base_price에 가깝도록 역산 추세 적용 (근사치)
        else:
            change = np.random.normal(trend_before, volatility)
            prices.append(prices[-1] * (1 + change))
    
    # prices가 비어있을 경우 (event_idx가 0인 경우) base_price로 시작
    if not prices:
        prices.append(base_price)

    # 이벤트 당일 가격 변화
    prices.append(prices[-1] * (1 + event_impact))

    # 이벤트 후 가격 생성
    for i in range(event_idx + 1, n):
        # 이벤트 발생일로부터 며칠이 지났는지 계산
        days_after_event = i - event_idx
        recovery_effect = 0
        if days_after_event <= recovery_days and recovery_days > 0 : # recovery_days가 0일때 ZeroDivisionError 방지
            # 점진적 회복 (선형 또는 비선형으로 조정 가능)
            # 여기서는 event_impact의 일부가 점진적으로 회복/소멸된다고 가정
            # event_impact가 양수였다면 (상승), 회복은 하락 압력으로 작용할 수 있고 (차익실현 등)
            # event_impact가 음수였다면 (하락), 회복은 상승 압력으로 작용
            # 아래 로직은 event_impact의 방향과 반대로 점진적 회복을 의미
            recovery_effect = (-event_impact / recovery_days) * (1 - (days_after_event / recovery_days)) # 초기 강한 회복, 점차 약화
            # 또는 단순 선형 회복: recovery_effect = -event_impact / recovery_days
        
        change = np.random.normal(trend_after + recovery_effect, volatility)
        prices.append(prices[-1] * (1 + change))
    
    # 거래량 생성
    volumes = np.random.lognormal(mean=np.log(100000), sigma=0.5, size=n)
    volumes = volumes.astype(int)
    # 이벤트 당일 거래량 증가 (event_idx가 유효한 경우)
    if 0 <= event_idx < n:
        volumes[event_idx] = int(volumes[event_idx] * volume_multiplier_on_event)

    # prices 리스트 길이가 n보다 짧을 경우 마지막 값으로 채우기 (예외처리)
    while len(prices) < n:
        prices.append(prices[-1] * (1 + np.random.normal(trend_after, volatility)))


    return pd.DataFrame({
        "Date": dates,
        "Close": prices[:n], # 길이를 n으로 맞춤
        "Volume": volumes
    })

# 확장된 이벤트 유형별 기본 설정
EVENT_SETTINGS = {
    "유상증자": {
        "event_impact": -0.05, "recovery_days": 20, "trend_before": 0.0001, "trend_after": 0.0002, "volume_multiplier_on_event": 3
    },
    "무상증자": {
        "event_impact": 0.03, "recovery_days": 10, "trend_before": 0.0002, "trend_after": -0.0001, "volume_multiplier_on_event": 2.5
    },
    "실적발표_긍정": {
        "event_impact": 0.07, "recovery_days": 5, "trend_before": 0.0001, "trend_after": 0.0003, "volume_multiplier_on_event": 4
    },
    "실적발표_부정": {
        "event_impact": -0.08, "recovery_days": 15, "trend_before": -0.0001, "trend_after": -0.0002, "volume_multiplier_on_event": 3.5
    },
    "신제품출시_성공적": {
        "event_impact": 0.06, "recovery_days": 10, "trend_before": 0.0002, "trend_after": 0.00025, "volume_multiplier_on_event": 2.5
    },
    "신제품출시_반응미지근": {
        "event_impact": -0.02, "recovery_days": 10, "trend_before": 0.0001, "trend_after": -0.00005, "volume_multiplier_on_event": 1.5
    },
    "M&A_피인수": {
        "event_impact": 0.15, "recovery_days": 3, "trend_before": 0.0001, "trend_after": 0.0000, "volume_multiplier_on_event": 6
    },
    "M&A_인수발표": { # 인수하는 회사
        "event_impact": -0.03, "recovery_days": 20, "trend_before": 0.0000, "trend_after": 0.0001, "volume_multiplier_on_event": 2.5
    },
    "자사주매입": {
        "event_impact": 0.025, "recovery_days": 15, "trend_before": 0.0001, "trend_after": 0.00015, "volume_multiplier_on_event": 1.8
    },
    "자사주소각": {
        "event_impact": 0.04, "recovery_days": 10, "trend_before": 0.00015, "trend_after": 0.0002, "volume_multiplier_on_event": 2.2
    },
    "정부규제강화": {
        "event_impact": -0.10, "recovery_days": 30, "trend_before": 0.0000, "trend_after": -0.0003, "volume_multiplier_on_event": 3
    },
    "정부정책수혜": {
        "event_impact": 0.09, "recovery_days": 25, "trend_before": 0.0001, "trend_after": 0.00025, "volume_multiplier_on_event": 3.2
    },
    "대규모공급계약": {
        "event_impact": 0.10, "recovery_days": 7, "trend_before": 0.0002, "trend_after": 0.0004, "volume_multiplier_on_event": 4.5
    },
    "계약파기_주요고객": {
        "event_impact": -0.12, "recovery_days": 20, "trend_before": -0.0001, "trend_after": -0.0003, "volume_multiplier_on_event": 3.8
    },
    "CEO교체_긍정적": {
        "event_impact": 0.04, "recovery_days": 15, "trend_before": -0.0001, "trend_after": 0.0002, "volume_multiplier_on_event": 2.0
    },
    "CEO리스크_횡령등": {
        "event_impact": -0.15, "recovery_days": 40, "trend_before": 0.0000, "trend_after": -0.0004, "volume_multiplier_on_event": 4.0
    },
    "특허취득_핵심기술": {
        "event_impact": 0.08, "recovery_days": 12, "trend_before": 0.0002, "trend_after": 0.0003, "volume_multiplier_on_event": 3.0
    },
    "특허분쟁패소": {
        "event_impact": -0.09, "recovery_days": 22, "trend_before": 0.0000, "trend_after": -0.00025, "volume_multiplier_on_event": 2.8
    },
    "배당발표_기대이상": {
        "event_impact": 0.03, "recovery_days": 7, "trend_before": 0.0001, "trend_after": 0.0001, "volume_multiplier_on_event": 2.0
    },
    "배당삭감": {
        "event_impact": -0.06, "recovery_days": 18, "trend_before": -0.00005, "trend_after": -0.00015, "volume_multiplier_on_event": 2.5
    },
    "해외시장진출성공": {
        "event_impact": 0.07, "recovery_days": 20, "trend_before": 0.00015, "trend_after": 0.0003, "volume_multiplier_on_event": 3.3
    },
    "공장화재_생산차질": {
        "event_impact": -0.07, "recovery_days": 25, "trend_before": 0.0001, "trend_after": -0.0001, "volume_multiplier_on_event": 2.7
    },
    "투자유치_대규모": {
        "event_impact": 0.11, "recovery_days": 10, "trend_before": 0.0001, "trend_after": 0.00035, "volume_multiplier_on_event": 4.2
    },
    "임상시험성공_바이오": {
        "event_impact": 0.20, "recovery_days": 10, "trend_before": 0.0005, "trend_after": 0.001, "volume_multiplier_on_event": 7
    },
    "임상시험실패_바이오": {
        "event_impact": -0.30, "recovery_days": 50, "trend_before": 0.0005, "trend_after": -0.001, "volume_multiplier_on_event": 6
    },
    "국제유가급등_항공석유화학": { # 항공사/해운사엔 부정적, 정유/화학 일부엔 긍정적일수도 있지만 여기선 비용증가 초점
        "event_impact": -0.06, "recovery_days": 15, "trend_before": 0.0000, "trend_after": -0.0001, "volume_multiplier_on_event": 2.0
    },
     "금리인상발표_성장주": { # 기술주, 바이오주 등 성장주에 일반적으로 부정적
        "event_impact": -0.04, "recovery_days": 15, "trend_before": -0.0001, "trend_after": -0.0002, "volume_multiplier_on_event": 2.2
    },
    "ESG등급상향": {
        "event_impact": 0.015, "recovery_days": 10, "trend_before": 0.00005, "trend_after": 0.0001, "volume_multiplier_on_event": 1.5
    },
    "데이터센터화재_IT서비스":{
        "event_impact": -0.09, "recovery_days": 20, "trend_before": 0.0001, "trend_after": -0.0002, "volume_multiplier_on_event": 3.0
    },
    "지분매각_대주주":{ # 오버행 이슈 등 부정적 인식 가능
        "event_impact": -0.05, "recovery_days": 15, "trend_before": 0.0000, "trend_after": -0.0001, "volume_multiplier_on_event": 2.5
    }
}

def get_random_date_str(start_year=2022, end_year=2024):
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28) # Keep it simple for days
    return f"{year}-{month:02d}-{day:02d}"

# 기업 목록 (약 50개, 티커와 기본 주가)
COMPANIES_DATA = [
    {"name": "삼성전자", "ticker": "005930.KS", "base_price": 70000, "sector": "IT"},
    {"name": "SK하이닉스", "ticker": "000660.KS", "base_price": 120000, "sector": "IT"},
    {"name": "NAVER", "ticker": "035420.KS", "base_price": 200000, "sector": "플랫폼"},
    {"name": "카카오", "ticker": "035720.KS", "base_price": 50000, "sector": "플랫폼"},
    {"name": "현대차", "ticker": "005380.KS", "base_price": 250000, "sector": "자동차"},
    {"name": "기아", "ticker": "000270.KS", "base_price": 120000, "sector": "자동차"},
    {"name": "LG에너지솔루션", "ticker": "373220.KS", "base_price": 400000, "sector": "배터리"},
    {"name": "삼성SDI", "ticker": "006400.KS", "base_price": 450000, "sector": "배터리"},
    {"name": "삼성바이오로직스", "ticker": "207940.KS", "base_price": 750000, "sector": "바이오"},
    {"name": "셀트리온", "ticker": "068270.KQ", "base_price": 180000, "sector": "바이오"},
    {"name": "POSCO홀딩스", "ticker": "005490.KS", "base_price": 400000, "sector": "철강"},
    {"name": "LG화학", "ticker": "051910.KS", "base_price": 400000, "sector": "화학"},
    {"name": "현대모비스", "ticker": "012330.KS", "base_price": 230000, "sector": "자동차부품"},
    {"name": "KB금융", "ticker": "105560.KS", "base_price": 70000, "sector": "금융"},
    {"name": "신한지주", "ticker": "055550.KS", "base_price": 45000, "sector": "금융"},
    {"name": "삼성물산", "ticker": "028260.KS", "base_price": 150000, "sector": "종합상사/건설"},
    {"name": "SK이노베이션", "ticker": "096770.KS", "base_price": 120000, "sector": "에너지/화학"},
    {"name": "카카오뱅크", "ticker": "323410.KS", "base_price": 25000, "sector": "금융"},
    {"name": "하이브", "ticker": "352820.KS", "base_price": 200000, "sector": "엔터테인먼트"},
    {"name": "엔씨소프트", "ticker": "036570.KS", "base_price": 200000, "sector": "게임"},
    {"name": "대한항공", "ticker": "003490.KS", "base_price": 22000, "sector": "운송"},
    {"name": "HMM", "ticker": "011200.KS", "base_price": 18000, "sector": "해운"},
    {"name": "아모레퍼시픽", "ticker": "090430.KS", "base_price": 130000, "sector": "화장품"},
    {"name": "LG생활건강", "ticker": "051900.KS", "base_price": 350000, "sector": "생활용품/화장품"},
    {"name": "이마트", "ticker": "139480.KS", "base_price": 70000, "sector": "유통"},
    {"name": "CJ제일제당", "ticker": "097950.KS", "base_price": 300000, "sector": "식품"},
    {"name": "SK바이오사이언스", "ticker": "302440.KS", "base_price": 70000, "sector": "바이오"},
    {"name": "한미약품", "ticker": "128940.KS", "base_price": 300000, "sector": "제약"},
    {"name": "두산에너빌리티", "ticker": "034020.KS", "base_price": 15000, "sector": "에너지/기계"},
    {"name": "한국전력", "ticker": "015760.KS", "base_price": 20000, "sector": "유틸리티"},
    {"name": "KT&G", "ticker": "033780.KS", "base_price": 80000, "sector": "소비재"},
    {"name": "고려아연", "ticker": "010130.KS", "base_price": 500000, "sector": "비철금속"},
    {"name": "S-Oil", "ticker": "010950.KS", "base_price": 70000, "sector": "정유"},
    {"name": "현대제철", "ticker": "004020.KS", "base_price": 30000, "sector": "철강"},
    {"name": "삼성생명", "ticker": "032830.KS", "base_price": 80000, "sector": "보험"},
    {"name": "한화솔루션", "ticker": "009830.KS", "base_price": 30000, "sector": "화학/태양광"},
    {"name": "크래프톤", "ticker": "259960.KS", "base_price": 250000, "sector": "게임"},
    {"name": "포스코퓨처엠", "ticker": "003670.KS", "base_price": 300000, "sector": "소재"},
    {"name": "에코프로비엠", "ticker": "247540.KQ", "base_price": 250000, "sector": "소재"},
    {"name": "JYP Ent.", "ticker": "035900.KQ", "base_price": 70000, "sector": "엔터테인먼트"},
    {"name": "에스엠", "ticker": "041510.KQ", "base_price": 80000, "sector": "엔터테인먼트"},
    {"name": "펄어비스", "ticker": "263750.KQ", "base_price": 40000, "sector": "게임"},
    {"name": "위메이드", "ticker": "112040.KQ", "base_price": 50000, "sector": "게임"},
    {"name": "현대건설", "ticker": "000720.KS", "base_price": 35000, "sector": "건설"},
    {"name": "한화에어로스페이스", "ticker": "012450.KS", "base_price": 200000, "sector": "방산/항공"},
    {"name": "LIG넥스원", "ticker": "079550.KS", "base_price": 150000, "sector": "방산"},
    {"name": "OCI홀딩스", "ticker": "456040.KS", "base_price": 100000, "sector": "화학"},
    {"name": "코스모신소재", "ticker": "005070.KS", "base_price": 150000, "sector": "소재"},
    {"name": "SKC", "ticker": "011790.KS", "base_price": 100000, "sector": "화학/소재"},
    {"name": "두산밥캣", "ticker": "241560.KS", "base_price": 50000, "sector": "기계"}
]

# 이벤트 설명을 위한 템플릿 및 샘플 데이터
QUARTERS = ["1분기", "2분기", "3분기", "4분기"]
SAMPLE_PRODUCTS = {"IT": "차세대 AI 반도체", "플랫폼": "확장현실(XR) 플랫폼", "자동차": "레벨4 자율주행 기술", "배터리": "고성능 전고체 배터리", "바이오": "면역항암제 후보물질", "철강": "수소환원제철용 특수강", "화학": "생분해성 플라스틱 신소재", "게임": "글로벌 기대작 MMORPG", "엔터테인먼트": "신인 아이돌 그룹"}
SAMPLE_REASONS_NEGATIVE_EARNINGS = ["글로벌 공급망 불안정", "주요 시장 수요 감소", "신사업 투자 비용 증가", "환율 변동성 확대"]
SAMPLE_MA_TARGETS = {"IT": "AI 솔루션 스타트업", "플랫폼": "데이터 분석 전문기업", "자동차": "전장부품 개발사", "바이오": "희귀질환 치료제 개발사", "게임": "유망 게임 스튜디오"}
SAMPLE_INDUSTRIES_REGULATION = ["온라인 플랫폼 서비스", "가상자산 거래", "기업형 임대주택", "모바일 게임 확률형 아이템"]
SAMPLE_INDUSTRIES_POLICY_BENEFIT = ["시스템 반도체 설계", "인공지능(AI) 신약 개발", "차세대 배터리 소재", "우주항공 및 방위산업", "해상풍력 발전단지"]
SAMPLE_GLOBAL_COMPANIES = ["글로빅스社", "테크노젠 그룹", "이노베이트 파트너스", "퀀텀솔루션즈", "오리온인더스트리"]
SAMPLE_AMOUNTS_KRW = ["500억원", "1,200억원", "3,000억원", "1조원"]
SAMPLE_CEO_BACKGROUNDS = ["해외 사업부문 총괄 부사장", "기술개발 연구소장 출신", "M&A 전략 전문가", "재무 담당 최고책임자(CFO)"]
SAMPLE_CEO_RISKS = ["배임 및 횡령 혐의 조사", "경영권 분쟁 가능성", "과도한 겸직 논란"]
SAMPLE_TECH_AREAS = {"IT": "신개념 메모리 기술", "바이오": "유전자 가위 기술", "배터리": "실리콘 음극재 기술", "화학": "탄소 포집 활용(CCU) 기술"}
SAMPLE_COMPETITORS = ["글로벌 경쟁사 A", "국내 선두기업 B"]
SAMPLE_DIVIDEND_PER_SHARE = ["주당 350원", "주당 700원", "주당 1,500원"]
SAMPLE_MARKETS_GLOBAL = ["미국", "유럽연합(EU)", "중국", "동남아시아 신흥국", "중동"]
SAMPLE_FACTORIES_LOCATIONS = ["국내 평택 신공장", "베트남 생산기지", "미국 오하이오 공장", "헝가리 배터리 공장"]
SAMPLE_INVESTORS_GLOBAL = ["블랙스톤", "칼라일 그룹", "KKR", "싱가포르 국부펀드 GIC", "사우디아라비아 국부펀드 PIF"]
SAMPLE_CLINICAL_PHASES = ["1상(안전성)", "2a상(탐색적 효능)", "2b상(용량 결정)", "3상(확증적 효능)"]
SAMPLE_FUEL_COST_IMPACT_AREAS = {"운송": "항공유 및 선박유 가격", "해운": "연료유 할증료", "정유":"정제마진 변동성", "화학":"나프타 가격"}
SAMPLE_GROWTH_SECTORS_IMPACTED = {"IT": "빅테크 기업", "플랫폼": "온라인 서비스 기업", "바이오": "신약 개발 기업", "게임":"콘텐츠 개발 기업"}
SAMPLE_ESG_RATINGS_NEW = ["A+ (Outstanding)", "A (Leader)", "BBB (Average)"]
SAMPLE_IDC_LOCATIONS_MAJOR = ["수도권 제1 데이터센터", "부산 글로벌 클라우드 데이터센터"]
SAMPLE_SHAREHOLDERS_MAJOR = ["창업주 일가", "2대 주주인 해외 투자조합", "국민연금공단"]


def generate_event_description(company_name, company_sector, event_type):
    """이벤트 유형 및 회사 정보에 기반하여 동적 설명 생성"""
    desc_template = f"{company_name}, {event_type} 관련 이슈 발생." # 기본 템플릿

    if event_type == "실적발표_긍정":
        profit_margin = random.choice(["5~10%", "10~15%", "15% 이상"])
        sales_growth = random.choice(["전년 동기 대비 10%", "시장 예상치 5% 상회", "사상 최대 분기 매출"])
        desc_template = f"{company_name}, {random.choice(QUARTERS)} 실적발표. {sales_growth} 달성, 영업이익률 {profit_margin} 기록하며 어닝 서프라이즈."
    elif event_type == "실적발표_부정":
        reason = random.choice(SAMPLE_REASONS_NEGATIVE_EARNINGS)
        desc_template = f"{company_name}, {random.choice(QUARTERS)} 실적발표. {reason}으로 인해 시장 기대치 하회하는 부진한 성과."
    elif event_type == "신제품출시_성공적":
        product = SAMPLE_PRODUCTS.get(company_sector, "주력 신제품")
        desc_template = f"{company_name}, 야심차게 준비한 {product} 출시! 초기 시장 반응 폭발적, 판매 호조 기대."
    elif event_type == "신제품출시_반응미지근":
        product = SAMPLE_PRODUCTS.get(company_sector, "기대 신제품")
        desc_template = f"{company_name}, {product} 출시하였으나, 소비자 반응은 예상보다 미미한 수준."
    elif event_type == "M&A_피인수":
        acquirer = random.choice(SAMPLE_GLOBAL_COMPANIES)
        desc_template = f"{company_name}, 글로벌 대기업 {acquirer}에 의한 인수합병(M&A) 절차 돌입 발표. 기업가치 재평가 기대."
    elif event_type == "M&A_인수발표":
        target_sector = random.choice(list(SAMPLE_MA_TARGETS.keys()))
        target_company_type = SAMPLE_MA_TARGETS.get(target_sector, "성장 잠재력이 큰 기업")
        desc_template = f"{company_name}, 신성장 동력 확보 위해 {target_sector} 분야의 {target_company_type} 인수 결정 발표."
    elif event_type == "자사주매입":
        amount = random.choice(SAMPLE_AMOUNTS_KRW)
        desc_template = f"{company_name}, 주주가치 제고 및 책임경영 강화 위해 {amount} 규모의 자사주 매입 결정 공시."
    elif event_type == "자사주소각":
        amount = random.choice(SAMPLE_AMOUNTS_KRW)
        desc_template = f"{company_name}, 주주환원 정책의 일환으로 {amount} 규모의 자사주 소각 결정. 유통 주식 수 감소 효과."
    elif event_type == "정부규제강화":
        industry = SAMPLE_INDUSTRIES_REGULATION[random.randint(0, len(SAMPLE_INDUSTRIES_REGULATION)-1)]
        desc_template = f"{company_name}가 속한 {industry}에 대한 정부의 규제 강화 움직임 포착. 투자심리 단기적 위축 우려."
    elif event_type == "정부정책수혜":
        industry = SAMPLE_INDUSTRIES_POLICY_BENEFIT[random.randint(0, len(SAMPLE_INDUSTRIES_POLICY_BENEFIT)-1)]
        desc_template = f"정부의 {industry} 육성 정책 발표. {company_name}, 핵심 기술력 바탕으로 대표 수혜 기업으로 부상."
    elif event_type == "대규모공급계약":
        partner = random.choice(SAMPLE_GLOBAL_COMPANIES)
        amount = random.choice(SAMPLE_AMOUNTS_KRW)
        item = SAMPLE_PRODUCTS.get(company_sector, "핵심 부품")
        desc_template = f"{company_name}, 글로벌 기업 {partner}와 {amount} 규모의 {item} 장기 공급 계약 체결 성공!"
    elif event_type == "계약파기_주요고객":
        client = random.choice(SAMPLE_GLOBAL_COMPANIES)
        desc_template = f"{company_name}, 주요 고객사였던 {client}와의 장기 계약이 예상치 못하게 종료/파기됨. 실적 타격 불가피."
    elif event_type == "CEO교체_긍정적":
        new_ceo_bg = random.choice(SAMPLE_CEO_BACKGROUNDS)
        desc_template = f"{company_name}, {new_ceo_bg} 출신의 신임 대표이사 선임. 경영 혁신 및 성장 가속화 기대감 고조."
    elif event_type == "CEO리스크_횡령등":
        risk_type = random.choice(SAMPLE_CEO_RISKS)
        desc_template = f"{company_name} 현 대표이사, {risk_type} 관련 의혹으로 검찰 조사 착수. 기업 신뢰도 급락."
    elif event_type == "특허취득_핵심기술":
        tech_field = SAMPLE_TECH_AREAS.get(company_sector, "미래 핵심 기술")
        desc_template = f"{company_name}, {tech_field} 분야에서 독보적인 원천 기술 특허 취득. 기술 경쟁 우위 확보."
    elif event_type == "특허분쟁패소":
        opponent = random.choice(SAMPLE_COMPETITORS)
        tech_field = SAMPLE_TECH_AREAS.get(company_sector, "주요 기술")
        desc_template = f"{company_name}, {opponent}와의 {tech_field} 관련 특허 침해 소송에서 최종 패소 판결. 관련 사업 차질 우려."
    elif event_type == "배당발표_기대이상":
        dividend = random.choice(SAMPLE_DIVIDEND_PER_SHARE)
        desc_template = f"{company_name}, 파격적인 {dividend} 현금 배당 결정! 주주친화 정책 강화로 시장의 주목."
    elif event_type == "배당삭감":
        desc_template = f"{company_name}, 경영 환경 악화 및 대규모 투자 재원 마련을 위해 올해 배당금 대폭 삭감 발표."
    elif event_type == "해외시장진출성공":
        market = random.choice(SAMPLE_MARKETS_GLOBAL)
        item = SAMPLE_PRODUCTS.get(company_sector, "주력 제품")
        desc_template = f"{company_name}, {market} 시장에 성공적으로 진출. {item} 현지 판매량 급증하며 성장세 견인."
    elif event_type == "공장화재_생산차질":
        factory_loc = random.choice(SAMPLE_FACTORIES_LOCATIONS)
        desc_template = f"{company_name}의 {factory_loc}에서 대형 화재 발생. 주요 생산 라인 가동 중단으로 단기적 생산 차질 예상."
    elif event_type == "투자유치_대규모":
        investor = random.choice(SAMPLE_INVESTORS_GLOBAL)
        amount = random.choice(SAMPLE_AMOUNTS_KRW)
        desc_template = f"{company_name}, 글로벌 투자 기관 {investor}로부터 {amount} 규모의 전략적 투자 유치 성공. 신사업 탄력."
    elif event_type == "임상시험성공_바이오":
        phase = random.choice(SAMPLE_CLINICAL_PHASES)
        drug_name = f"{company_name}의 차세대 신약 파이프라인 'CX-{random.randint(100,999)}'"
        desc_template = f"대형 호재! {drug_name}, {phase}에서 긍정적 데이터 확보하며 성공적인 결과 발표. 기술수출 기대감 상승."
    elif event_type == "임상시험실패_바이오":
        phase = random.choice(SAMPLE_CLINICAL_PHASES)
        drug_name = f"{company_name}의 핵심 신약 후보물질 'BIO-{random.randint(100,999)}'"
        desc_template = f"안타까운 소식. {drug_name}, 임상 {phase}에서 유효성 입증에 실패하며 개발 잠정 중단 결정."
    elif event_type == "국제유가급등_항공석유화학":
        sector_impact_detail = SAMPLE_FUEL_COST_IMPACT_AREAS.get(company_sector, "원가")
        desc_template = f"국제 유가 급등세 지속. {company_name}의 경우 {sector_impact_detail} 부담 가중으로 수익성 악화 우려."
    elif event_type == "금리인상발표_성장주":
        sector_impact_detail = SAMPLE_GROWTH_SECTORS_IMPACTED.get(company_sector, "고PER 주식")
        desc_template = f"중앙은행의 기준금리 인상 결정. {company_name}과 같은 {sector_impact_detail}의 투자 매력도 감소 우려 확산."
    elif event_type == "ESG등급상향":
        new_rating = random.choice(SAMPLE_ESG_RATINGS_NEW)
        desc_template = f"{company_name}, 글로벌 ESG 평가 기관으로부터 {new_rating}으로 등급 상향 조정. 지속가능경영 노력 인정."
    elif event_type == "데이터센터화재_IT서비스":
        idc_location = random.choice(SAMPLE_IDC_LOCATIONS_MAJOR)
        desc_template = f"{company_name}가 임차 중인 {idc_location}에서 화재 발생. 일부 서비스 장애 및 손실 복구에 시일 소요될 전망."
    elif event_type == "지분매각_대주주":
        seller = random.choice(SAMPLE_SHAREHOLDERS_MAJOR)
        desc_template = f"{company_name}의 {seller}가(이) 보유 지분 일부를 시간외 대량매매(블록딜) 방식으로 매각. 오버행 우려 부각."

    return desc_template


# MOCK_EVENTS_DB 초기화
MOCK_EVENTS_DB = {}
for event_type_key in EVENT_SETTINGS.keys():
    MOCK_EVENTS_DB[event_type_key] = []

event_type_keys = list(EVENT_SETTINGS.keys())
company_event_counts = {comp["ticker"]: 0 for comp in COMPANIES_DATA}
event_type_usage_count = {etype: 0 for etype in event_type_keys}

total_events_target = 120 # 목표 총 이벤트 수 (50개 회사 * 약 2.4개)
max_events_per_company = 3 # 한 회사당 너무 많은 이벤트가 몰리지 않도록
min_events_per_type = int(total_events_target / len(event_type_keys) * 0.5) # 각 이벤트 타입이 최소한 몇번은 나오도록

generated_event_count = 0

# 1. 각 이벤트 타입 최소 사용 횟수 보장
for etype in event_type_keys:
    for _ in range(max(1,min_events_per_type)): # 최소 1번은 나오도록
        if generated_event_count >= total_events_target * 1.2: break # 너무 많이 생성되는 것 방지

        selected_company = random.choice(COMPANIES_DATA)
        # 특정 회사에 이벤트가 몰리지 않도록, 이미 최대 할당량 채운 회사는 스킵
        attempts = 0
        while company_event_counts[selected_company["ticker"]] >= max_events_per_company and attempts < len(COMPANIES_DATA):
            selected_company = random.choice(COMPANIES_DATA)
            attempts +=1
        if attempts >= len(COMPANIES_DATA) and company_event_counts[selected_company["ticker"]] >= max_events_per_company : # 모든 회사가 꽉찼으면 더이상 진행 불가
             continue


        # 바이오 이벤트는 바이오/제약 회사에 우선 할당
        if "바이오" in etype and selected_company["sector"] not in ["바이오", "제약"]:
            bio_companies = [c for c in COMPANIES_DATA if c["sector"] in ["바이오", "제약"] and company_event_counts[c["ticker"]] < max_events_per_company]
            if bio_companies:
                selected_company = random.choice(bio_companies)
            else: # 적합한 바이오 회사가 없으면 스킵
                continue
        
        # IT서비스 이벤트는 IT/플랫폼 회사에 우선 할당
        if "IT서비스" in etype and selected_company["sector"] not in ["IT", "플랫폼"]:
            it_companies = [c for c in COMPANIES_DATA if c["sector"] in ["IT", "플랫폼"] and company_event_counts[c["ticker"]] < max_events_per_company]
            if it_companies:
                selected_company = random.choice(it_companies)
            else: continue

        event_date_str = get_random_date_str()
        description = generate_event_description(selected_company["name"], selected_company["sector"], etype)

        event_data = {
            "company": selected_company["name"],
            "ticker": selected_company["ticker"],
            "event_date": event_date_str,
            "description": description,
            "event_type": etype,
            "price_series": generate_mock_stock_data(
                event_date_str,
                base_price=selected_company["base_price"],
                **EVENT_SETTINGS[etype]
            )
        }
        MOCK_EVENTS_DB[etype].append(event_data)
        company_event_counts[selected_company["ticker"]] += 1
        event_type_usage_count[etype] += 1
        generated_event_count += 1

# 2. 목표 총 이벤트 수까지 추가 생성
while generated_event_count < total_events_target:
    selected_company = random.choice(COMPANIES_DATA)
    if company_event_counts[selected_company["ticker"]] >= max_events_per_company:
        # 모든 회사가 max_events_per_company에 도달했는지 확인
        if all(count >= max_events_per_company for count in company_event_counts.values()):
            break # 더 이상 생성할 수 없음
        continue # 다른 회사 시도

    random_event_type = random.choice(event_type_keys)

    # 바이오 이벤트는 바이오/제약 회사에 우선 할당
    if "바이오" in random_event_type and selected_company["sector"] not in ["바이오", "제약"]:
        bio_companies = [c for c in COMPANIES_DATA if c["sector"] in ["바이오", "제약"] and company_event_counts[c["ticker"]] < max_events_per_company]
        if bio_companies:
            selected_company = random.choice(bio_companies)
        else: continue
            
    if "IT서비스" in random_event_type and selected_company["sector"] not in ["IT", "플랫폼"]:
        it_companies = [c for c in COMPANIES_DATA if c["sector"] in ["IT", "플랫폼"] and company_event_counts[c["ticker"]] < max_events_per_company]
        if it_companies:
            selected_company = random.choice(it_companies)
        else: continue


    event_date_str = get_random_date_str()
    description = generate_event_description(selected_company["name"], selected_company["sector"], random_event_type) + " (추가)"

    event_data = {
        "company": selected_company["name"],
        "ticker": selected_company["ticker"],
        "event_date": event_date_str,
        "description": description,
        "event_type": random_event_type,
        "price_series": generate_mock_stock_data(
            event_date_str,
            base_price=selected_company["base_price"],
            **EVENT_SETTINGS[random_event_type]
        )
    }
    MOCK_EVENTS_DB[random_event_type].append(event_data)
    company_event_counts[selected_company["ticker"]] += 1
    event_type_usage_count[random_event_type] += 1
    generated_event_count += 1

# 사용자가 요청한 함수들
def get_similar_events(event_type, limit=5):
    """특정 이벤트 유형과 관련된 과거 사례들을 반환합니다."""
    # event_type이 "실적발표"와 같이 일반적인 경우, 하위 상세 유형(_긍정, _부정)을 모두 포함할지 여부 결정 필요
    # 현재 MOCK_EVENTS_DB는 "실적발표_긍정", "실적발표_부정" 등 상세 유형을 키로 가짐
    # 만약 "실적발표"로 검색 시 "_긍정", "_부정" 모두 가져오려면 아래와 같이 처리
    
    related_events = []
    if event_type in MOCK_EVENTS_DB: # 정확한 이벤트 타입 매칭 (예: "실적발표_긍정")
        related_events.extend(MOCK_EVENTS_DB[event_type])
    else: # 포괄적인 이벤트 타입 검색 (예: "실적발표" 검색 시 "실적발표_긍정", "실적발표_부정" 모두)
        for key in MOCK_EVENTS_DB.keys():
            if key.startswith(event_type):
                related_events.extend(MOCK_EVENTS_DB[key])
    
    # 중복 제거 (만약 같은 이벤트가 여러 카테고리에 속할 가능성이 있다면, 현재 구조에서는 없음)
    # related_events = [dict(t) for t in {tuple(d.items()) for d in related_events}] # 매우 느릴 수 있음. 내용물이 hashable해야 함.
    # DataFrame을 사용하지 않으므로 간단히는 어려움. 현재는 중복 가능성 낮음.

    # 날짜순 정렬 등 추가 가능
    # 여기서는 단순히 limit 만큼 반환
    return related_events[:limit]

def get_event_types():
    """사용 가능한 모든 이벤트 유형을 반환합니다."""
    # 상세 유형 ("실적발표_긍정") 또는 대표 유형 ("실적발표") 중 어떤 것을 반환할지 정책 필요
    # 여기서는 EVENT_SETTINGS에 정의된 모든 상세 유형을 반환
    return list(EVENT_SETTINGS.keys())

# # 예시 사용법:
# print(f"생성된 총 이벤트 수: {generated_event_count}")
# for etype, count in event_type_usage_count.items():
# print(f"이벤트 타입 '{etype}': {count}개")

# samsung_jusang_events = get_similar_events("유상증자")
# if samsung_jusang_events:
#     print(f"\n--- 유상증자 유사 사례 (최대 5개) ---")
#     for event in samsung_jusang_events:
#         print(f"{event['company']} ({event['event_date']}): {event['description']}")
#         # print(event['price_series'].head(3)) # 주가 데이터 확인
# else:
#     print("유상증자 유사 사례 없음")

# positive_earnings_events = get_similar_events("실적발표_긍정")
# print(f"\n--- 긍정적 실적발표 유사 사례 (최대 5개) ---")
# for event in positive_earnings_events:
#      print(f"{event['company']} ({event['event_date']}): {event['description']}")

# all_earnings_events = get_similar_events("실적발표") # "실적발표_긍정", "실적발표_부정" 모두 검색
# print(f"\n--- 모든 실적발표 유사 사례 (최대 5개) ---")
# for event in all_earnings_events:
#      print(f"{event['company']} ({event['event_date']} - {event['event_type']}): {event['description']}")


# print("\n--- 사용 가능한 이벤트 유형 ---")
# print(get_event_types())