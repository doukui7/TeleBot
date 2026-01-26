"""
텔레그램 봇 메인 모듈
"""
import logging
from telegram import Bot
from telegram.error import TelegramError
from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsChannelBot:
    """뉴스 채널 봇 클래스"""
    
    def __init__(self, token: str, channel_id: str):
        self.bot = Bot(token=token)
        self.channel_id = channel_id
    
    async def send_news(self, message: str) -> bool:
        """
        채널에 뉴스 메시지 전송
        
        Args:
            message: 전송할 메시지
        
        Returns:
            성공 여부
        """
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False
            )
            logger.info(f"채널 {self.channel_id}로 메시지 전송 성공")
            return True
        
        except TelegramError as e:
            logger.error(f"텔레그램 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"메시지 전송 오류: {e}")
            return False
    
    async def send_photo_news(self, photo_url: str, caption: str) -> bool:
        """
        사진과 함께 뉴스 전송

        Args:
            photo_url: 사진 URL
            caption: 캡션

        Returns:
            성공 여부
        """
        try:
            await self.bot.send_photo(
                chat_id=self.channel_id,
                photo=photo_url,
                caption=caption,
                parse_mode="HTML"
            )
            logger.info(f"채널 {self.channel_id}로 사진 메시지 전송 성공")
            return True

        except TelegramError as e:
            logger.error(f"텔레그램 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"사진 전송 오류: {e}")
            return False

    async def send_photo_buffer(self, photo_buffer, caption: str = "") -> bool:
        """
        이미지 버퍼로 사진 전송

        Args:
            photo_buffer: BytesIO 이미지 버퍼
            caption: 캡션 (선택)

        Returns:
            성공 여부
        """
        try:
            from telegram import InputFile

            photo_buffer.seek(0)
            await self.bot.send_photo(
                chat_id=self.channel_id,
                photo=InputFile(photo_buffer, filename="chart.png"),
                caption=caption,
                parse_mode="HTML"
            )
            logger.info(f"채널 {self.channel_id}로 이미지 전송 성공")
            return True

        except TelegramError as e:
            logger.error(f"텔레그램 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"이미지 전송 오류: {e}")
            return False
    
    async def check_connection(self) -> bool:
        """
        봇 연결 확인
        
        Returns:
            연결 성공 여부
        """
        try:
            me = await self.bot.get_me()
            logger.info(f"봇 연결 성공: {me.username}")
            return True
        except TelegramError as e:
            logger.error(f"봇 연결 실패: {e}")
            return False
