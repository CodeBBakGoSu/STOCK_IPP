from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time, json
from datetime import datetime

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service("")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://tossinvest.com/stocks/US20100629001/community")
time.sleep(2)

comments_set = set()
last_count = -1

while True:
    soup = BeautifulSoup(driver.page_source, "html.parser")
    articles = soup.find_all("article", class_="comment")

    for article in articles:
        # 텍스트 내용 추출
        spans = article.find_all("span", class_="tw-1r5dc8g0 _1sihfl60")
        full_text = " ".join(span.get_text(strip=True) for span in spans if span.get_text(strip=True))
        
        # 시간 추출
        time_tag = article.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            timestamp = time_tag["datetime"]
        else:
            timestamp = None

        if full_text and timestamp:
            comments_set.add((timestamp, full_text))

    if len(comments_set) == last_count:
        break
    last_count = len(comments_set)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

driver.quit()

# 저장
data = [{"timestamp": ts, "content": text} for (ts, text) in comments_set]

with open("toss_community_comments_with_time.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 총 {len(data)}개의 댓글 저장 완료 (내용 + 시간 포함)")