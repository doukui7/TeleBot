"""
TeleBot Main Entry Point
- Render에서 실행하는 메인 파일
"""
import asyncio
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Python 경로에 python 폴더 추가
sys.path.insert(0, 'python')

from scheduler import NewsScheduler


async def main():
    """메인 실행 함수"""
    logger.info("TeleBot 스케줄러 시작...")

    scheduler = NewsScheduler()
    scheduler.start()

    # 스케줄러가 계속 실행되도록 유지
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("종료 신호 수신")
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
