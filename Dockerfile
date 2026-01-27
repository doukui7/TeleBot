# TeleBot Dockerfile
# Playwright가 미리 설치된 이미지 사용

FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

WORKDIR /app

# 의존성 파일 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 타임존 설정
ENV TZ=Asia/Seoul

# 실행
CMD ["python", "main.py"]
