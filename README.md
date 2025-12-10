# Jules Telegram Bot

Telegram бот для взаимодействия с Jules API. Бот позволяет просматривать список сессий и отслеживать изменения в фоновом режиме.

## Функционал

- **Список сессий**: Получение и отображение текущих сессий через команду `/list`.
- **Мониторинг**: Фоновая задача, проверяющая изменения в сессиях и уведомляющая администратора о новых или обновленных данных.

## Запуск

Бот доступен в виде Docker-образа: `ghcr.io/attid/jules_telegram_bot:latest`.

### Использование с Docker Compose

Создайте файл `docker-compose.yml` со следующим содержимым:

```yaml
services:
  jules-bot:
    image: ghcr.io/attid/jules_telegram_bot:latest
    restart: unless-stopped
    environment:
      - TG_TOKEN=your_telegram_bot_token
      - JULES_TOKEN=your_jules_api_key
      - ADMIN_CHAT_ID=your_chat_id
```

Замените значения переменных окружения на ваши данные и запустите:

```bash
docker-compose up -d
```
