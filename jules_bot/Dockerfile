FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables should be passed at runtime, but we declare them here for clarity
ENV TG_TOKEN=""
ENV JULES_TOKEN=""
ENV ADMIN_CHAT_ID=""

CMD ["python", "bot.py"]
