"""
뉴스 데이터 가져오기 모듈 (Google News RSS 사용)
- 비트코인, 미국 증시, 한국 증시 뉴스
- 영어 뉴스 한국어 번역 지원
"""
import requests
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime

# googletrans는 선택적 (한국어 뉴스만 사용시 불필요)
try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Google News RSS에서 뉴스를 가져오는 클래스"""

    # 뉴스 피드 설정 (경제 전문 위주)
    NEWS_FEEDS = {
        'mk_stock': {
            'title': '매경 증권',
            'url_ko': 'https://www.mk.co.kr/rss/50200011/',
            'url_en': None,
            'limit': 3,
        },
        'mk_economy': {
            'title': '매경 경제',
            'url_ko': 'https://www.mk.co.kr/rss/30100041/',
            'url_en': None,
            'limit': 2,
        },
        'yonhap': {
            'title': '연합뉴스',
            'url_ko': 'https://www.yna.co.kr/rss/news.xml',
            'url_en': None,
            'limit': 2,
        },
        'kr_stock': {
            'title': '국내 증시',
            'url_ko': 'https://news.google.com/rss/search?q=국내+증시&hl=ko-KR&gl=KR&ceid=KR:ko',
            'url_en': None,
            'limit': 3,
        },
        'us_stock': {
            'title': '미국 증시',
            'url_ko': 'https://news.google.com/rss/search?q=미국+증시&hl=ko-KR&gl=KR&ceid=KR:ko',
            'url_en': None,
            'limit': 3,
        },
        'bitcoin': {
            'title': '비트코인',
            'url_ko': 'https://news.google.com/rss/search?q=비트코인&hl=ko-KR&gl=KR&ceid=KR:ko',
            'url_en': None,
            'limit': 3,
        },
    }

    def __init__(self, api_key: str = None, category: str = "business"):
        self.api_key = api_key  # 번역 API용 (선택적)
        self.category = category
        self.last_fetched_articles = []
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.translator = Translator() if TRANSLATOR_AVAILABLE else None

    def fetch_google_news_rss(self, url: str, limit: int = 10) -> List[Dict]:
        """
        Google News RSS에서 뉴스 가져오기

        Args:
            url: RSS URL
            limit: 가져올 뉴스 개수

        Returns:
            뉴스 기사 리스트
        """
        try:
            response = requests.get(url, headers=self._headers, timeout=10)
            response.raise_for_status()

            # XML 파싱
            root = ET.fromstring(response.content)

            articles = []
            for item in root.findall('.//item'):
                if len(articles) >= limit:
                    break

                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')

                article = {
                    'title': title.text if title is not None else '',
                    'link': link.text if link is not None else '',
                    'pubDate': pub_date.text if pub_date is not None else '',
                    'source': source.text if source is not None else '',
                }

                # 제목이 있는 것만 추가
                if article['title']:
                    articles.append(article)

            logger.info(f"Google News RSS에서 {len(articles)}개 기사 가져옴")
            return articles

        except requests.RequestException as e:
            logger.error(f"RSS 요청 오류: {e}")
            return []
        except ET.ParseError as e:
            logger.error(f"XML 파싱 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"뉴스 처리 오류: {e}")
            return []

    def translate_to_korean(self, text: str) -> str:
        """
        영어 텍스트를 한국어로 번역 (google-translate-new 사용)

        Args:
            text: 번역할 텍스트

        Returns:
            번역된 텍스트
        """
        if not text:
            return text

        # 이미 한국어인 경우 그대로 반환
        if self._is_korean(text):
            return text

        # 번역기 없으면 원문 반환
        if not self.translator:
            return text

        try:
            # googletrans 라이브러리 사용
            translated = self.translator.translate(text, src='en', dest='ko')
            if translated and getattr(translated, 'text', None):
                return translated.text
            return text  # 번역 실패시 원문 반환

        except Exception as e:
            logger.debug(f"번역 오류: {e}")
            return text

    def _is_korean(self, text: str) -> bool:
        """한국어 포함 여부 확인"""
        korean_pattern = re.compile('[가-힣]')
        return bool(korean_pattern.search(text))

    def _get_similarity(self, str1: str, str2: str) -> float:
        """두 문자열의 유사도 계산 (Jaccard Similarity)"""
        def clean(s: str) -> set:
            s = re.sub(r'[^\w\s가-힣]', '', s).lower()
            return set(s.split())

        s1 = clean(str1)
        s2 = clean(str2)

        if not s1 or not s2:
            return 0.0

        intersection = s1 & s2
        union = s1 | s2

        return len(intersection) / len(union) if union else 0.0

    def _deduplicate_articles(self, articles: List[Dict], threshold: float = 0.3) -> List[Dict]:
        """중복 기사 제거"""
        unique_articles = []

        for article in articles:
            title = article.get('title', '')
            is_duplicate = False

            for existing in unique_articles:
                existing_title = existing.get('title', '')
                similarity = self._get_similarity(title, existing_title)

                # 유사도 40% 이상이거나 서로 포함관계면 중복
                if similarity > threshold or title in existing_title or existing_title in title:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_articles.append(article)

        return unique_articles

    def _is_duplicate_global(self, title: str, seen_titles: List[str], threshold: float = 0.3) -> bool:
        """전체 카테고리에서 중복인지 확인"""
        for seen in seen_titles:
            similarity = self._get_similarity(title, seen)
            if similarity > threshold or title in seen or seen in title:
                return True
        return False

    def fetch_all_news(self, translate: bool = True) -> Dict[str, List[Dict]]:
        """
        모든 카테고리의 뉴스 가져오기 (전체 카테고리 중복 제거)

        Args:
            translate: 영어 뉴스 번역 여부

        Returns:
            카테고리별 뉴스 딕셔너리
        """
        all_news = {}
        seen_titles = []  # 전체 카테고리에서 본 제목들

        for category, config in self.NEWS_FEEDS.items():
            # 카테고리별 limit 사용 (기본값 3)
            cat_limit = config.get('limit', 3)
            articles = []

            # 한국어 뉴스 가져오기
            if config.get('url_ko'):
                ko_articles = self.fetch_google_news_rss(config['url_ko'], limit=cat_limit * 3)
                articles.extend(ko_articles)

            # 영어 뉴스 가져오기 (있는 경우)
            if config.get('url_en'):
                en_articles = self.fetch_google_news_rss(config['url_en'], limit=cat_limit)

                # 번역
                if translate:
                    for article in en_articles:
                        original_title = article.get('title', '')
                        translated_title = self.translate_to_korean(original_title)

                        # 번역된 경우 원문도 보존
                        if translated_title != original_title:
                            article['title'] = translated_title
                            article['original_title'] = original_title

                articles.extend(en_articles)

            # 카테고리 내 중복 제거
            articles = self._deduplicate_articles(articles)

            # 전체 카테고리에서 중복 제거
            unique_articles = []
            for article in articles:
                title = article.get('title', '')
                if title and not self._is_duplicate_global(title, seen_titles):
                    unique_articles.append(article)
                    seen_titles.append(title)

                if len(unique_articles) >= cat_limit:
                    break

            all_news[category] = unique_articles
            logger.info(f"{config['title']}: {len(unique_articles)}개 기사 (중복 {len(articles) - len(unique_articles)}개 제거)")

        return all_news

    def format_briefing_message(self, all_news: Dict[str, List[Dict]]) -> str:
        """
        브리핑 메시지 포맷

        Args:
            all_news: 카테고리별 뉴스 딕셔너리

        Returns:
            포맷된 메시지
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        message = f"📢 <b>오늘의 시장 브리핑</b>\n"
        message += f"📅 {now}\n\n"

        category_emojis = {
            'mk_stock': '📈',
            'mk_economy': '💰',
            'yonhap': '📰',
            'kr_stock': '🇰🇷',
            'us_stock': '🇺🇸',
            'bitcoin': '🪙',
        }

        for category, articles in all_news.items():
            config = self.NEWS_FEEDS.get(category, {})
            emoji = category_emojis.get(category, '📰')
            title = config.get('title', category)

            message += f"<b>{emoji} {title}</b>\n"

            if articles:
                for article in articles:  # 카테고리별 limit만큼 출력
                    news_title = article.get('title', '')
                    link = article.get('link', '')
                    source = article.get('source', '')

                    if news_title:
                        if link:
                            message += f"• <a href=\"{link}\">{news_title}</a>"
                        else:
                            message += f"• {news_title}"
                        if source:
                            message += f" <i>({source})</i>"
                        message += "\n"
            else:
                message += "• 관련 뉴스가 없습니다.\n"

            message += "\n"

        return message

    # 기존 API 호환성을 위한 메서드들
    def fetch_everything(self, query: str, limit: int = 5, sort_by: str = "publishedAt") -> List[Dict]:
        """기존 API 호환용 - Google News RSS로 대체"""
        # 쿼리에 따라 적절한 URL 생성
        url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
        return self.fetch_google_news_rss(url, limit)

    def is_relevant_news(self, article: Dict) -> bool:
        """기사가 관심 주제와 관련있는지 확인"""
        keywords = [
            "kospi", "코스피", "한국주식", "korea stock",
            "nasdaq", "dow jones", "s&p 500", "미국주식", "us stock",
            "bitcoin", "비트코인", "ethereum", "이더리움", "crypto", "cryptocurrency"
        ]

        title = (article.get("title") or "").lower()
        content = title

        for keyword in keywords:
            if keyword in content:
                return True

        return False

    def format_article(self, article: Dict) -> str:
        """기사를 텔레그램 메시지 형식으로 포맷"""
        title = article.get("title", "제목 없음")
        link = article.get("link", "")
        source = article.get("source", "출처 불명")

        message = f"📰 <b>{title}</b>\n\n"
        message += f"📌 출처: {source}\n"

        if link:
            message += f"🔗 <a href='{link}'>기사 읽기</a>"

        return message
