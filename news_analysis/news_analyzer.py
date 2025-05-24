import pandas as pd
import numpy as np
import re
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer, AutoModelForSequenceClassification
from keybert import KeyBERT
import konlpy
from konlpy.tag import Okt
import torch
import warnings
import matplotlib.pyplot as plt
from collections import Counter
import networkx as nx
import matplotlib.font_manager as fm
import platform
import os

# JVM 설정을 위한 환경변수 설정
os.environ["JAVA_HOME"] = "/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home"

warnings.filterwarnings('ignore')

class NewsAnalyzer:
    def __init__(self, csv_path=None):
        """
        뉴스 분석 클래스 초기화
        
        Args:
            csv_path (str, optional): CSV 파일 경로. 기본값 None.
        """
        self.csv_path = csv_path
        if csv_path:
            self.df = self._load_data()
        else:
            self.df = pd.DataFrame() # 빈 데이터프레임으로 초기화
        
        # 폰트 설정 - 한글 출력을 위한 설정
        if platform.system() == 'Darwin':  # macOS
            plt.rc('font', family='AppleGothic')
        elif platform.system() == 'Windows':
            plt.rc('font', family='Malgun Gothic')
        else:
            # Linux의 경우 NanumGothic 또는 다른 한글 폰트를 설치해야 함
            plt.rc('font', family='NanumGothic')
        
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 출력 문제 해결
        
        # Okt 초기화 (JVM이 자동으로 시작됨)
        try:
            self.okt = Okt()
            print("Okt 초기화 성공")
        except Exception as e:
            print(f"Okt 초기화 실패: {e}")
            print("Okt 기능 없이 계속합니다...")
            self.okt = None
        
        # finBERT 모델 로드
        self.finbert_model_name = "yiyanghkust/finbert-tone"
        self.finbert_tokenizer = AutoTokenizer.from_pretrained(self.finbert_model_name)
        self.finbert_model = AutoModelForSequenceClassification.from_pretrained(self.finbert_model_name)
        
        # KeyBERT 모델 로드
        self.keybert_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
        
    def _load_data(self):
        """CSV 파일에서 데이터 로드"""
        try:
            df = pd.read_csv(self.csv_path)
            # NaN 값을 빈 문자열로 대체
            df = df.fillna('')
            return df
        except Exception as e:
            print(f"데이터 로드 중 오류 발생: {e}")
            return pd.DataFrame()

    def preprocess_text(self, text):
        """
        텍스트 전처리 함수
        
        Args:
            text (str): 원본 텍스트
            
        Returns:
            str: 전처리된 텍스트
        """
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', ' ', text)
        # 특수 문자 제거
        text = re.sub(r'[^\w\s]', ' ', text)
        # 여러 공백을 하나로 변경
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def tokenize_korean(self, text):
        """
        한국어 텍스트 토큰화
        
        Args:
            text (str): 원본 텍스트
            
        Returns:
            list: 토큰화된 단어 리스트
        """
        if self.okt is None:
            # Okt가 없을 경우 간단한 공백 기반 토큰화 사용
            return text.split()
        
        # 명사, 형용사, 동사 추출
        words = self.okt.pos(text)
        words = [word for word, pos in words if pos in ['Noun', 'Adjective', 'Verb']]
        return words

    def textrank_summarize(self, text, num_sentences=3):
        """
        TextRank 알고리즘을 사용한 텍스트 요약
        
        Args:
            text (str): 원본 텍스트
            num_sentences (int, optional): 요약할 문장 수. 기본값 3.
            
        Returns:
            str: 요약된 텍스트
        """
        try:
            # 문장 추출
            sentences = sent_tokenize(text)
            
            # 문장이 너무 적으면 원문 반환
            if len(sentences) <= num_sentences:
                return text
                
            # TF-IDF 행렬 생성
            tfidf_vectorizer = TfidfVectorizer()
            tfidf_matrix = tfidf_vectorizer.fit_transform(sentences)
            
            # 문장 간 유사도 계산
            similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # TextRank 알고리즘 적용 (PageRank와 유사)
            nx_graph = nx.from_numpy_array(similarity_matrix)
            scores = nx.pagerank(nx_graph)
            
            # 점수에 따라 문장 정렬
            ranked_sentences = sorted(((scores[i], i, s) for i, s in enumerate(sentences)), reverse=True)
            
            # 원래 순서대로 상위 문장 선택
            top_sentence_indices = sorted([ranked_sentences[i][1] for i in range(min(num_sentences, len(ranked_sentences)))])
            summary = [sentences[i] for i in top_sentence_indices]
            
            return ' '.join(summary)
            
        except Exception as e:
            print(f"요약 생성 중 오류 발생: {e}")
            # 오류 발생 시 원본 텍스트의 앞부분만 반환
            return text[:500] + "..."

    def extract_keywords(self, text, top_n=5):
        """
        KeyBERT를 사용한 키워드 추출
        
        Args:
            text (str): 키워드를 추출할 텍스트
            top_n (int): 추출할 키워드 수
            
        Returns:
            list: (키워드, 점수) 튜플의 리스트
        """
        try:
            # KeyBERT로 키워드 추출
            keywords = self.keybert_model.extract_keywords(
                text, 
                keyphrase_ngram_range=(1, 2), 
                stop_words='english',  # 한국어는 stop_words 적용 안함
                top_n=top_n
            )
            return keywords
        except Exception as e:
            print(f"키워드 추출 중 오류 발생: {e}")
            return []

    def analyze_sentiment(self, text):
        """
        finBERT 모델을 사용한 감성 분석
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            dict: 감성 분석 결과 (positive, neutral, negative 점수)
        """
        try:
            # 한국어 텍스트 길이 제한 (모델 max_length 고려)
            if len(text) > 512:
                text = text[:512]
                
            inputs = self.finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            # 모델 예측
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
            
            # 확률로 변환
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # 결과 딕셔너리로 반환
            result = {
                'positive': float(probabilities[0][0]),
                'negative': float(probabilities[0][1]),
                'neutral': float(probabilities[0][2])
            }
            
            return result
        except Exception as e:
            print(f"감성 분석 중 오류 발생: {e}")
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}

    def extract_keywords_llm_mock(self, text, top_n=5):
        """
        [시뮬레이션] LLM을 이용한 키워드 추출을 흉내 냅니다.
        실제 LLM API를 호출하지 않습니다. Okt를 사용하여 명사를 추출하거나 간단한 분리를 사용합니다.
        LLM은 일반적으로 점수를 반환하지 않으므로, 여기서는 임의의 점수(1.0)를 부여합니다.
        Args:
            text (str): 키워드를 추출할 텍스트
            top_n (int): 추출할 키워드 수 (시뮬레이션에서는 근사치)
        Returns:
            list: (키워드, 가상_점수) 튜플의 리스트
        """
        print("[MOCK] LLM-based keyword extraction simulation running...")
        keywords = []
        if not text.strip():
            return []

        try:
            if self.okt:
                # Okt를 사용하여 명사 위주로 추출
                nouns = self.okt.nouns(text)
                # 중복 제거 및 순서 유지
                unique_nouns = list(dict.fromkeys(nouns))
                # 길이가 2 이상인 명사만 선택
                filtered_nouns = [n for n in unique_nouns if len(n) > 1]
                keywords = [(noun, 1.0) for noun in filtered_nouns[:top_n]]
            
            if not keywords:
                # Okt가 없거나 명사 추출 결과가 없는 경우, 공백 기준 분리 후 상위 N개 단어 사용
                words = text.split()
                # 중복 제거 및 순서 유지
                unique_words = list(dict.fromkeys(words))
                # 간단한 필터링 (예: 너무 짧은 단어 제외)
                filtered_words = [w for w in unique_words if len(w) > 1]
                keywords = [(word, 1.0) for word in filtered_words[:top_n]]
            
            # 만약 아무 키워드도 없다면, 원문에서 처음 몇 단어라도...
            if not keywords and len(text.split()) > 0:
                first_few_words = text.split()[:top_n]
                keywords = [(word, 0.5) for word in first_few_words] # 점수를 다르게 표시

        except Exception as e:
            print(f"[MOCK] LLM keyword extraction simulation error: {e}")
            # 오류 발생 시, 텍스트의 첫 단어라도 반환 시도
            try:
                words = text.split()
                if words:
                    keywords = [(words[0], 0.1)]
            except:
                keywords = [("오류", 0.0)]

        return keywords

    def find_similar_news(self, index, top_n=3):
        """
        TF-IDF와 코사인 유사도를 사용하여 유사한 뉴스 찾기
        
        Args:
            index (int): 기준 뉴스의 인덱스
            top_n (int): 찾을 유사 뉴스 수
            
        Returns:
            list: 유사 뉴스 인덱스와 유사도 점수
        """
        try:
            # 'content' 컬럼이 있는지 확인
            content_col = 'content' if 'content' in self.df.columns else 'description'
            
            # 모든 뉴스 내용으로 TF-IDF 행렬 생성
            contents = self.df[content_col].fillna('').tolist()
            vectorizer = TfidfVectorizer(stop_words='english')  # 한국어는 stop_words 적용 안함
            tfidf_matrix = vectorizer.fit_transform(contents)
            
            # 기준 뉴스와 다른 뉴스들 간의 코사인 유사도 계산
            cosine_similarities = cosine_similarity(tfidf_matrix[index], tfidf_matrix).flatten()
            
            # 유사도가 높은 뉴스 인덱스 찾기 (기준 뉴스 제외)
            similar_indices = cosine_similarities.argsort()[::-1]
            similar_indices = [i for i in similar_indices if i != index][:top_n]
            
            # 결과 반환: [(인덱스, 유사도 점수), ...]
            results = [(idx, cosine_similarities[idx]) for idx in similar_indices]
            
            return results
        except Exception as e:
            print(f"유사 뉴스 검색 중 오류 발생: {e}")
            return []

    def analyze_all(self, index):
        """
        특정 뉴스에 대해 모든 분석을 수행
        
        Args:
            index (int): 분석할 뉴스 인덱스
            
        Returns:
            dict: 분석 결과
        """
        if index >= len(self.df):
            print(f"인덱스가 범위를 벗어났습니다. 현재 데이터 크기: {len(self.df)}")
            return {}
        
        # 'content' 컬럼이 있는지 확인
        content_col = 'content' if 'content' in self.df.columns else 'description'
        
        news = self.df.iloc[index]
        content = news[content_col]
        
        # 모든 분석 수행
        summary = self.textrank_summarize(content)
        keywords = self.extract_keywords(content)
        sentiment = self.analyze_sentiment(content)
        similar_news = self.find_similar_news(index)
        
        # 결과 통합
        result = {
            'title': news['title'],
            'content': content[:200] + "..." if len(content) > 200 else content,
            'summary': summary,
            'keywords': keywords,
            'sentiment': sentiment,
            'similar_news': [
                {
                    'title': self.df.iloc[idx]['title'],
                    'similarity': score
                } for idx, score in similar_news
            ]
        }
        
        return result

    def batch_analyze_sentiment(self, start_idx=0, end_idx=None):
        """
        여러 뉴스 기사의 감성 분석을 배치로 수행
        
        Args:
            start_idx (int): 시작 인덱스
            end_idx (int): 종료 인덱스 (None이면 전체 데이터)
            
        Returns:
            pd.DataFrame: 감성 분석 결과
        """
        if end_idx is None:
            end_idx = len(self.df)
        
        # 'content' 컬럼이 있는지 확인
        content_col = 'content' if 'content' in self.df.columns else 'description'
        
        # 결과를 저장할 리스트
        results = []
        
        for i in range(start_idx, min(end_idx, len(self.df))):
            content = self.df.iloc[i][content_col]
            sentiment = self.analyze_sentiment(content)
            
            # 결과 추가
            results.append({
                'index': i,
                'title': self.df.iloc[i]['title'],
                'positive': sentiment['positive'],
                'negative': sentiment['negative'],
                'neutral': sentiment['neutral'],
                'sentiment': max(sentiment, key=sentiment.get)
            })
            
            # 진행 상황 출력
            if (i - start_idx + 1) % 10 == 0:
                print(f"진행 중: {i - start_idx + 1}/{min(end_idx, len(self.df)) - start_idx}")
                
        return pd.DataFrame(results)

    def visualize_sentiment_distribution(self, results_df):
        """
        감성 분석 결과의 분포를 시각화
        
        Args:
            results_df (pd.DataFrame): 감성 분석 결과 데이터프레임
        """
        # 감성 분포 계산
        sentiment_counts = results_df['sentiment'].value_counts()
        
        # 파이 차트 생성
        plt.figure(figsize=(10, 6))
        colors = ['#ff9999','#66b3ff','#99ff99']
        plt.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', 
                startangle=90, colors=colors)
        plt.axis('equal')
        plt.title('뉴스 기사 감성 분석 결과 분포')
        plt.show()
        
        # 감성 평균 점수 막대 그래프
        plt.figure(figsize=(10, 6))
        avg_scores = {
            'positive': results_df['positive'].mean(),
            'negative': results_df['negative'].mean(),
            'neutral': results_df['neutral'].mean()
        }
        
        plt.bar(avg_scores.keys(), avg_scores.values(), color=colors)
        plt.title('평균 감성 점수')
        plt.ylabel('점수')
        plt.ylim(0, 1)
        
        # 값 표시
        for i, (k, v) in enumerate(avg_scores.items()):
            plt.text(i, v + 0.02, f'{v:.3f}', ha='center')
            
        plt.show()


# 실행 예시
if __name__ == "__main__":
    import sys
    import os
    
    # 현재 디렉토리 기준으로 CSV 파일 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    csv_path = os.path.join(parent_dir, "stock_news_20250513_032406.csv")
    
    # 커맨드 라인 인자가 있으면 해당 경로 사용
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    print(f"분석할 CSV 파일: {csv_path}")
    
    try:
        # 뉴스 분석기 초기화
        analyzer = NewsAnalyzer(csv_path)
        
        # 메뉴 출력 및 기능 선택
        while True:
            print("\n=== 뉴스 분석 메뉴 ===")
            print("1. TextRank 기반 뉴스 요약")
            print("2. KeyBERT 기반 키워드 추출")
            print("3. finBERT 기반 감성 분석")
            print("4. TF-IDF 기반 유사 뉴스 검색")
            print("5. 모든 분석 수행")
            print("0. 종료")
            
            choice = input("\n원하는 기능을 선택하세요: ")
            
            if choice == '0':
                print("프로그램을 종료합니다.")
                break
                
            # 뉴스 선택
            if analyzer.df.empty:
                print("데이터가 없습니다.")
                continue
                
            print("\n분석할 뉴스를 선택하세요:")
            for i, title in enumerate(analyzer.df.iloc[:, 0].head(10)):  # 첫 10개 기사만 표시
                print(f"{i+1}. {title[:50]}...")
            
            try:
                news_idx = int(input("\n뉴스 번호 (1-10): ")) - 1
                if news_idx < 0 or news_idx >= len(analyzer.df):
                    print("유효하지 않은 뉴스 번호입니다.")
                    continue
                    
                # 선택된 뉴스 내용 가져오기
                news_content = ""
                for col in analyzer.df.columns:
                    if "content" in col.lower() or "description" in col.lower():
                        news_content = analyzer.df.iloc[news_idx][col]
                        break
                
                if not news_content:
                    print("뉴스 내용을 찾을 수 없습니다.")
                    continue
                    
                # 선택한 기능 실행
                if choice == '1':
                    print("\n=== TextRank 기반 뉴스 요약 ===")
                    summary = analyzer.textrank_summarize(news_content)
                    print(summary)
                    
                elif choice == '2':
                    print("\n=== KeyBERT 기반 키워드 추출 ===")
                    keywords = analyzer.extract_keywords(news_content)
                    for keyword, score in keywords:
                        print(f"{keyword}: {score:.4f}")
                        
                elif choice == '3':
                    print("\n=== finBERT 기반 감성 분석 ===")
                    sentiment = analyzer.analyze_sentiment(news_content)
                    print(f"긍정: {sentiment['positive']:.4f}")
                    print(f"중립: {sentiment['neutral']:.4f}")
                    print(f"부정: {sentiment['negative']:.4f}")
                    
                elif choice == '4':
                    print("\n=== TF-IDF 기반 유사 뉴스 검색 ===")
                    similar_news = analyzer.find_similar_news(news_idx)
                    for i, (idx, score) in enumerate(similar_news):
                        print(f"{i+1}. 유사도: {score:.4f}")
                        print(f"   제목: {analyzer.df.iloc[idx][0][:50]}...")
                        
                elif choice == '5':
                    print("\n=== 모든 분석 수행 ===")
                    
                    print("\n[TextRank 기반 뉴스 요약]")
                    summary = analyzer.textrank_summarize(news_content)
                    print(summary)
                    
                    print("\n[KeyBERT 기반 키워드 추출]")
                    keywords = analyzer.extract_keywords(news_content)
                    for keyword, score in keywords:
                        print(f"{keyword}: {score:.4f}")
                        
                    print("\n[finBERT 기반 감성 분석]")
                    sentiment = analyzer.analyze_sentiment(news_content)
                    print(f"긍정: {sentiment['positive']:.4f}")
                    print(f"중립: {sentiment['neutral']:.4f}")
                    print(f"부정: {sentiment['negative']:.4f}")
                    
                    print("\n[TF-IDF 기반 유사 뉴스 검색]")
                    similar_news = analyzer.find_similar_news(news_idx)
                    for i, (idx, score) in enumerate(similar_news):
                        print(f"{i+1}. 유사도: {score:.4f}")
                        print(f"   제목: {analyzer.df.iloc[idx][0][:50]}...")
                
                else:
                    print("유효하지 않은 선택입니다.")
                    
            except ValueError:
                print("숫자를 입력해주세요.")
                
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc() 