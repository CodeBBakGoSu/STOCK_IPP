import requests
import pandas as pd
import re
import html
import json
import datetime
import time
from bs4 import BeautifulSoup  # 웹 스크래핑용 라이브러리 추가

# API 인증 정보
CLIENT_ID = "RzAnMJlsIJvDgy6qnY7B"
CLIENT_SECRET = "zi5GSf3Nkm"

def clean(text: str) -> str:
    """HTML 태그를 제거하고 엔티티를 디코딩합니다."""
    no_tag = re.sub(r"<[^>]+>", "", text)      # HTML 태그 제거
    return html.unescape(no_tag).strip()       # 엔티티 디코딩

def fetch_article_content(url, timeout=10, max_retries=3):
    """
    뉴스 URL에서 본문 내용을 추출합니다.
    
    Args:
        url (str): 뉴스 기사 URL
        timeout (int): 요청 타임아웃 시간(초)
        max_retries (int): 최대 재시도 횟수
        
    Returns:
        str: 추출된 본문 내용 또는 실패 시 빈 문자열
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 여러 뉴스 사이트 본문 추출 패턴
    content_patterns = [
        {'site': 'naver', 'selector': '#dic_area, #articleBodyContents, #articeBody, .news_end, #newsEndContents'},
        {'site': 'daum', 'selector': '.article_view'},
        {'site': 'news.nate', 'selector': '#content .articleCont'},
        {'site': 'mk.co.kr', 'selector': '.art_txt, #article_body'},
        {'site': 'yna.co.kr', 'selector': '.article-txt, .article'},
        {'site': 'hani.co.kr', 'selector': '.article-text, .article-contents'},
    ]
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # URL에 따른 인코딩 처리
            if 'yna.co.kr' in url:
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 다양한 뉴스 사이트 패턴 시도
            for pattern in content_patterns:
                article_element = soup.select_one(pattern['selector'])
                if article_element:
                    content_text = article_element.get_text(strip=True)
                    # 텍스트 정리
                    content_text = re.sub(r'\s+', ' ', content_text)
                    return content_text
            
            # 일치하는 패턴이 없으면 일반적인 방법 시도
            paragraphs = soup.find_all('p')
            if paragraphs:
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
                if content:
                    return content
                    
            return "본문 추출 실패 (패턴 불일치)"
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # 재시도 전 대기
            else:
                return f"본문 추출 실패: {str(e)}"
    
    return ""

def fetch_news(query, pages=5, display=100, delay=0.4, fetch_content=True):
    """
    네이버 뉴스 API에서 뉴스를 검색하여 DataFrame으로 반환합니다.
    
    Args:
        query (str): 검색 쿼리 (불리언 검색식 지원)
        pages (int): 가져올 페이지 수 (기본값: 5)
        display (int): 페이지당 결과 수 (기본값: 100, 최대: 100)
        delay (float): API 호출 간 지연 시간(초) (기본값: 0.4)
        fetch_content (bool): 본문 내용을 가져올지 여부 (기본값: True)
        
    Returns:
        pandas.DataFrame: 검색 결과를 담은 데이터프레임
    """
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
        "Accept": "application/json",
    }
    results = []
    
    for n in range(pages):
        params = {
            "query": query,
            "display": display,
            "start": n*display + 1,
            "sort": "date",
        }
        
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            
            for idx, it in enumerate(items):
                item_data = {
                    "title": clean(it["title"]),
                    "description": clean(it["description"]),
                    "originallink": it["originallink"],
                    "link": it["link"],
                    "pubDate": it["pubDate"],
                    "content": ""
                }
                
                # 본문 내용 가져오기 (선택적)
                if fetch_content:
                    try:
                        print(f"기사 {n*display+idx+1}/{(n+1)*display} 본문 추출 중... ", end="")
                        target_url = it["originallink"] if it["originallink"] else it["link"]
                        item_data["content"] = fetch_article_content(target_url)
                        print("완료")
                        time.sleep(1)  # 사이트 부하 방지
                    except Exception as e:
                        print(f"실패: {str(e)}")
                        item_data["content"] = ""
                
                results.append(item_data)
                
            print(f"페이지 {n+1}/{pages} 완료 - {len(items)}건 수집")
            
            # 과다 호출 방지를 위한 지연
            if n < pages - 1:
                time.sleep(delay)
                
        except Exception as e:
            print(f"페이지 {n+1} 수집 중 오류 발생: {str(e)}")
    
    return pd.DataFrame(results)

def filter_news(df, keywords=None):
    """
    키워드를 기준으로 뉴스를 필터링합니다.
    
    Args:
        df (pandas.DataFrame): 필터링할 뉴스 데이터프레임
        keywords (list): 필터링할 키워드 목록 (기본값: ["증시", "경제", "주가"])
        
    Returns:
        pandas.DataFrame: 필터링된 데이터프레임
    """
    if keywords is None:
        keywords = ["증시", "경제", "주가"]
        
    kw_pattern = "|".join(keywords)
    kw_re = re.compile(f"({kw_pattern})", re.I)
    
    # 제목이나 본문에 키워드가 포함된 항목만 필터링
    filtered_df = df[
        df["title"].apply(lambda x: bool(kw_re.search(x))) | 
        df["content"].apply(lambda x: bool(kw_re.search(x)))
    ]
    
    # 중복 제거
    return filtered_df.drop_duplicates("originallink")

def save_to_csv(df, prefix="stock_news"):
    """
    데이터프레임을 CSV 파일로 저장합니다.
    
    Args:
        df (pandas.DataFrame): 저장할 데이터프레임
        prefix (str): 파일명 접두사 (기본값: "stock_news")
        
    Returns:
        str: 저장된 파일 경로
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.csv"
    
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    return filename

def get_user_input():
    """사용자로부터 검색 설정을 입력받습니다."""
    print("\n=== 네이버 뉴스 검색기 ===")
    print("[불리언 검색식 예시]")
    print("- 'A AND B': A와 B가 모두 포함된 결과")
    print("- 'A OR B': A 또는 B가 포함된 결과")
    print("- 'A AND (B OR C)': A를 포함하고, B나 C 중 하나를 포함하는 결과\n")
    
    query = input("검색어를 입력하세요: ")
    
    try:
        pages = int(input("검색할 페이지 수를 입력하세요 (기본값: 5): ") or 5)
    except ValueError:
        print("유효하지 않은 입력입니다. 기본값 5를 사용합니다.")
        pages = 5
    
    # 필터링 키워드 입력
    filter_input = input("필터링 키워드를 입력하세요 (쉼표로 구분, 기본값: 증시,경제,주가): ")
    if filter_input.strip():
        filter_keywords = [k.strip() for k in filter_input.split(',')]
    else:
        filter_keywords = ["증시", "경제", "주가"]
    
    # 출력 파일 접두사 입력
    prefix = input("출력 파일 접두사를 입력하세요 (기본값: stock_news): ") or "stock_news"
    
    # 본문 추출 여부
    get_content = input("뉴스 본문도 추출하시겠습니까? (y/n, 기본값: y): ").lower() != 'n'
    if get_content:
        print("주의: 본문 추출은 시간이 오래 걸리고 일부 사이트에서는 차단될 수 있습니다.")
    
    return {
        "query": query,
        "pages": pages,
        "filter_keywords": filter_keywords,
        "prefix": prefix,
        "get_content": get_content
    }

def main():
    """메인 함수"""
    # 사용자 입력 받기
    user_input = get_user_input()
    
    query = user_input["query"]
    pages = user_input["pages"]
    filter_keywords = user_input["filter_keywords"]
    prefix = user_input["prefix"]
    get_content = user_input["get_content"]
    
    print(f"\n'{query}' 관련 뉴스 수집 시작...")
    df = fetch_news(query, pages=pages, fetch_content=get_content)
    
    print(f"수집 완료: 총 {len(df)}건")
    
    # 필터링 및 중복 제거
    filtered_df = filter_news(df, keywords=filter_keywords)
    print(f"필터링 후: {len(filtered_df)}건")
    
    # CSV 저장
    output_file = save_to_csv(filtered_df, prefix=prefix)
    print(f"{len(filtered_df)}건 저장 → {output_file}")

if __name__ == "__main__":
    main() 