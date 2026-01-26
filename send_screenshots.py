"""Send captured screenshots to Telegram"""
import asyncio
import sys
sys.path.insert(0, 'src')

from telegram_bot import NewsChannelBot
from config import TELEGRAM_BOT_TOKEN, CHANNEL_ID

async def send_screenshots():
    bot = NewsChannelBot(TELEGRAM_BOT_TOKEN, CHANNEL_ID)

    # Fear & Greed screenshot
    print("Sending Fear & Greed screenshot...")
    with open('fear_greed_screenshot.png', 'rb') as f:
        from io import BytesIO
        buf = BytesIO(f.read())
        buf.seek(0)
        await bot.send_photo_buffer(buf, "CNN Fear & Greed Index")
    print("[OK] Fear & Greed sent")

    # Naver Finance screenshot
    print("Sending Naver Finance screenshot...")
    with open('naver_world_screenshot.png', 'rb') as f:
        buf = BytesIO(f.read())
        buf.seek(0)
        await bot.send_photo_buffer(buf, "Naver World Market")
    print("[OK] Naver Finance sent")

if __name__ == '__main__':
    asyncio.run(send_screenshots())
