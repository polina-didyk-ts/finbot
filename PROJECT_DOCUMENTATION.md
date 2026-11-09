# Finance Receipt Bot — Повна документація проекту

## 📋 Зміст

1. [Загальний опис](#загальний-опис)
2. [Архітектура та компоненти](#архітектура-та-компоненти)
3. [Залежності](#залежності)
4. [Налаштування](#налаштування)
5. [Встановлення та запуск](#встановлення-та-запуск)
6. [Як працює бот](#як-працює-бот)
7. [Файлова структура](#файлова-структура)
8. [Детальний опис модулів](#детальний-опис-модулів)
9. [Змінні середовища](#змінні-середовища)
10. [Розробка та тестування](#розробка-та-тестування)

---

## Загальний опис

**Finance Receipt Bot** — це Telegram-бот, який автоматично обробляє фінансові документи (чеки, квитанції) та організує їх у Google Drive і Google Sheets. Бот дозволяє користувачам:

- Завантажувати фото/скани чеків до бота
- Вказувати опис покупки у підписі до зображення
- Автоматично зберігати чек у Google Drive (з організацією за місяцями)
- Записувати витрати у Google Sheets у вкладку конкретного користувача
- Витягувати дату і суму з чека за допомогою OCR (Anthropic API)

### Основні можливості:

✅ Інтеграція з Telegram API  
✅ Завантаження файлів на Google Drive  
✅ Запис даних у Google Sheets  
✅ OCR обробка чеків (розпізнавання суми та дати)  
✅ Контроль доступу за user_id  
✅ Автоматична організація файлів за місяцями  
✅ Підтримка часових зон  

---

## Архітектура та компоненти

### Основна схема взаємодії:

```
┌─────────────┐
│   Telegram  │
└──────┬──────┘
       │
       │ (користувач надсилає фото)
       ▼
┌─────────────────┐
│  app.py         │ (головний обробник подій)
└────┬──────┬─────┘
     │      │
     ▼      ▼
┌──────────────────┐    ┌──────────────────┐
│ google_drive.py  │    │ google_sheets.py │
│ (Upload)         │    │ (Append row)     │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         │                       │
    ┌────▼───────────────────────▼─────┐
    │   google_clients.py (OAuth 2.0)   │
    └────┬──────────────────────────┬───┘
         │                          │
         ▼                          ▼
    ┌──────────────┐         ┌──────────────┐
    │  Google      │         │  Google      │
    │  Drive API   │         │  Sheets API  │
    └──────────────┘         └──────────────┘
```

### Блоки компонентів:

| Компонент | Відповідальність |
|-----------|------------------|
| `app.py` | Основна логіка бота, обробка команд та повідомлень |
| `google_clients.py` | Управління Google OAuth 2.0 авторизацією |
| `google_drive.py` | Завантаження файлів на Google Drive |
| `google_sheets.py` | Запис даних у Google Sheets |
| `ocr.py` | OCR обробка чеків через Anthropic API |
| `users.py` | База користувачів та їх конфігурацій |
| `config.py` | Конфігурація змінних середовища |

---

## Залежності

### Python пакети:

```
python-telegram-bot>=20.0          # Telegram Bot API обробник
python-dotenv>=1.0.0               # Завантаження змінних з .env
google-api-python-client>=2.70.0   # Google Sheets та Drive API
google-auth>=2.20.0                # Google авторизація
google-auth-oauthlib>=1.0.0        # OAuth обробка для Google
anthropic>=0.25.0                  # Anthropic API для OCR
```

### Зовнішні сервіси:

- **Telegram Bot API** — для взаємодії з ботом
- **Google Cloud API** — для роботи з Drive та Sheets
- **Anthropic Claude API** — для OCR обробки документів

---

## Налаштування

### Крок 1: Telegram Bot

1. Напишіть [BotFather](https://t.me/botfather) в Telegram
2. Виконайте `/newbot`
3. Дайте імя та юзернейм боту
4. Отримайте `TELEGRAM_BOT_TOKEN`

**Приклад токена:** `123456789:ABCDefGhIJKlmnOpQrStUVwxYzAbCdEfGhI`

### Крок 2: Google Cloud Project

1. Перейдіть до [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новий проект
3. Увімкніть наступні API:
   - Google Drive API
   - Google Sheets API

### Крок 3: OAuth 2.0 Client ID (для Drive)

1. В Google Cloud Console перейдіть до `APIs & Services` → `Credentials`
2. Натисніть `Create Credentials` → `OAuth client ID`
3. Виберіть `Application type: Desktop app`
4. Завантажте JSON файл
5. Перейменуйте його в `client_secret.json`
6. Покладіть його у корневу папку проекту (поруч з `app.py`)

### Крок 4: Service Account (для Sheets, опціонально)

Якщо хочете використовувати Service Account для Sheets (рекомендується):

1. В Google Cloud Console перейдіть до `Service Accounts`
2. Создайте новий сервіс-акаунт
3. Генеруйте JSON ключ
4. Помістіть вміст JSON у змінну `GOOGLE_SERVICE_ACCOUNT_JSON` у `.env`

Або просто залиште його порожним — бот буде використовувати OAuth для Sheets.

### Крок 5: Google Drive Folder

1. Создайте папку у вашому Google Drive (наприклад: "Finance Receipts")
2. Відкрийте папку та скопіюйте ID з URL:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID
   ```
3. Це буде `GOOGLE_DRIVE_ROOT_FOLDER_ID`

### Крок 6: Google Sheets

1. Создайте новий Google Sheets документ
2. Для кожного користувача создайте вкладку (наприклад: "Поля", "Ксюша", "Марина")
3. У першому рядку кожної вкладки додайте колонки:
   ```
   дата | (пусто) | (пусто) | опис | (пусто) | сума | чек
   A    | B       | C       | D    | E       | F    | G
   ```
4. Скопіюйте ID документа з URL:
   ```
   https://docs.google.com/spreadsheets/d/SHEET_ID/edit
   ```
5. Це буде `GOOGLE_SHEET_ID`

### Крок 7: Anthropic API (для OCR, опціонально)

1. Зареєструйтесь на [Anthropic](https://console.anthropic.com/)
2. Отримайте API ключ
3. Помістіть його у `.env` як `ANTHROPIC_API_KEY`

Якщо не налаштуєте API ключ, OCR буде повертати пусті значення для суми та дати.

---

## Встановлення та запуск

### 1. Клонування/Підготовка проекту

```bash
cd /Users/polina/Desktop/finbot/finance_receipt_bot
```

### 2. Створення віртуального середовища

```bash
python3 -m venv .venv
source .venv/bin/activate  # На macOS/Linux
# або
.venv\Scripts\activate  # На Windows
```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Налаштування змінних середовища

Створіть файл `.env` у корневій папці проекту:

```bash
# .env

# Telegram
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Google OAuth (для Drive)
GOOGLE_OAUTH_CLIENT_SECRET_FILE=client_secret.json
GOOGLE_OAUTH_TOKEN_FILE=token.json

# Google IDs
GOOGLE_DRIVE_ROOT_FOLDER_ID=YOUR_FOLDER_ID
GOOGLE_SHEET_ID=YOUR_SHEET_ID

# Anthropic (опціонально)
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_KEY

# Часова зона (за замовчуванням: Europe/Warsaw)
TIMEZONE=Europe/Warsaw
```

### 5. Запуск бота

```bash
python app.py
```

При першому запуску:
- Якщо `token.json` не існує, відкриється браузер для авторизації Google
- Натисніть "Allow" для надання прав доступу
- Токен автоматично збереться у `token.json`

### 6. Отримання user_id

Для додання нового користувача:

1. Напишіть боту команду `/whoami`
2. Бот поверне ваш `user_id` та `username`
3. Додайте цей `user_id` у `users.py`:

```python
USERS: Dict[int, Dict[str, Any]] = {
    # ...
    YOUR_USER_ID: {
        "name": "YOUR_USERNAME",
        "sheet_tab": "YOUR_SHEET_TAB_NAME",
    },
}
```

---

## Як працює бот

### Основний workflow:

```
1. Користувач надсилає фото/документ з описом (caption)
                          ▼
2. Бот отримує повідомлення (handle_receipt)
                          ▼
3. Перевірка доступу за user_id (get_user_config)
                          ▼
4. Якщо доступу немає → повідомлення про помилку
                          ▼
5. Якщо є доступ → отримання файлу від Telegram
                          ▼
6. Завантаження файлу у тимчасову папку
                          ▼
7. OCR обробка через Anthropic (витяг суми та дати)
                          ▼
8. Завантаження файлу на Google Drive
                          ▼
9. Запис рядка у Google Sheets (з датою, описом, посиланням)
                          ▼
10. Відправка підтвердження користувачеві
```

### Команди бота:

#### `/start`
Стартова команда, яка показує привіт.

```
Привіт! Надішли фото або файл чеку з описом у підписі, наприклад: ягоди в офіс
```

#### `/whoami`
Повертає `user_id` та `username` користувача.

```
user_id: 696461653
username: polyanakw
```

### Обробка фото/документа

Користувач надсилає фото або файл з caption (підписом):

```
📷 [Фото чеку]
Підпис: "ягоди в офіс"
```

Бот:
1. ✅ Зберігає файл у Google Drive у папку поточного місяця
2. ✅ Розпізнає суму та дату через OCR
3. ✅ Додає рядок у Google Sheets з колонками:
   - **Дата**: розпізнана OCR (або поточна дата)
   - **Опис**: з підпису користувача
   - **Сума**: розпізнана OCR (або пусто)
   - **Чек**: посилання на файл у Google Drive

4. ✅ Повертає підтвердження:

```
Чек додано ✅

Користувач: polyanakw
Вкладка: Поля
Дата: 25.06.2026
Опис: ягоди в офіс
Сума: 320.50
Чек: https://drive.google.com/file/d/...
```

---

## Файлова структура

```
finance_receipt_bot/
├── app.py                          # Головний файл бота (точка входу)
├── config.py                       # Конфігурація змінних
├── users.py                        # База користувачів
├── google_clients.py               # OAuth 2.0 управління
├── google_drive.py                 # Функції завантаження на Drive
├── google_sheets.py                # Функції запису у Sheets
├── ocr.py                          # OCR обробка через Anthropic
├── test_ocr.py                     # Тести для OCR
├── requirements.txt                # Python залежності
├── .env                            # Змінні середовища (gitignore)
├── .env.example                    # Приклад .env
├── client_secret.json              # OAuth 2.0 credentials (gitignore)
├── token.json                      # OAuth 2.0 токен (gitignore)
├── service-account.json            # Service Account JSON (gitignore)
├── README.md                       # Коротке описання
└── PROJECT_DOCUMENTATION.md        # Ця файл
```

### Файли, які НЕ комітяться:

```
.env
client_secret.json
token.json
service-account.json
.venv/
__pycache__/
```

---

## Детальний опис модулів

### 📄 app.py

**Назва:** Головна логіка бота  
**Призначення:** Обробка команд та повідомлень від користувачів

#### Функції:

##### `async def start_command(update, context)`
Обробляє команду `/start`.

```python
await update.message.reply_text("Привіт! Надішли фото або файл чеку...")
```

##### `async def whoami_command(update, context)`
Повертає `user_id` та `username` користувача.

```python
user_id: 696461653
username: polyanakw
```

##### `async def handle_receipt(update, context)`
**Основна логіка обробки чеків:**

1. Отримує файл (фото або документ)
2. Перевіряє доступ користувача
3. Валідує caption (опис)
4. Завантажує файл у тимчасову папку
5. Запускає OCR обробку
6. Завантажує на Google Drive
7. Записує рядок у Google Sheets
8. Відправляє підтвердження

#### Стартування бота:

```python
if __name__ == "__main__":
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("whoami", whoami_command))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))
    
    app.run_polling()
```

---

### 📄 config.py

**Назва:** Конфігурація  
**Призначення:** Завантаження змінних середовища

```python
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_OAUTH_CLIENT_SECRET_FILE = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_FILE")
GOOGLE_OAUTH_TOKEN_FILE = os.getenv("GOOGLE_OAUTH_TOKEN_FILE")
GOOGLE_DRIVE_ROOT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Warsaw")
```

Всі змінні мають вигляд: `Optional[str]` (можуть бути None)

---

### 📄 users.py

**Назва:** База користувачів  
**Призначення:** Управління дозволами та конфігурацією користувачів

```python
USERS: Dict[int, Dict[str, Any]] = {
    696461653: {
        "name": "polyanakw",
        "sheet_tab": "Поля",
    },
    156994725: {
        "name": "KseniiaTsarik",
        "sheet_tab": "Ксюша",
    },
    # ... більше користувачів
}

def get_user_config(telegram_user_id: int) -> Optional[Dict[str, Any]]:
    """Повертає конфіг користувача або None"""
    return USERS.get(int(telegram_user_id))
```

#### Як додати користувача:

1. Користувач отримує свій `user_id` через `/whoami`
2. Додайте запис у `USERS`:

```python
YOUR_USER_ID: {
    "name": "YOUR_USERNAME",
    "sheet_tab": "NAME_OF_SHEET_TAB",
}
```

---

### 📄 google_clients.py

**Назна:** Google OAuth 2.0 управління  
**Призначення:** Отримання авторизованих сервісів для Drive та Sheets

#### Функція:

##### `get_google_services() -> Tuple[drive_service, sheets_service]`

**Алгоритм:**

```
1. Для Drive (OAuth):
   - Спробувати загрузити з GOOGLE_TOKEN_JSON (env)
   - Спробувати загрузити з token.json (файл)
   - Якщо немає → запустити інтерактивний OAuth flow

2. Для Sheets:
   - Якщо є GOOGLE_SERVICE_ACCOUNT_JSON → використати Service Account
   - Інакше → використати тойсамий OAuth токен, що й для Drive

3. Повернути обидва сервіси
```

**Характеристики:**

- Підтримує три типи авторизації Google:
  - OAuth 2.0 (user credentials)
  - Service Account (server-to-server)
  - Заново-токене (refresh token)
  
- Автоматично оновлює expired токени
- Зберігає токен у `token.json` при першому запуску

---

### 📄 google_drive.py

**Назва:** Функції для Google Drive  
**Призначення:** Завантаження файлів та організація папок

#### Функції:

##### `get_current_month_folder_name() -> str`

Повертає назву поточного місяця українською мовою:

```python
get_current_month_folder_name()  # → "Червень" (для червня)
```

Місяці:
```
1 → "Січень"
2 → "Лютий"
...
12 → "Грудень"
```

##### `get_or_create_month_folder(drive_service) -> str`

Отримує або створює папку поточного місяця у кореневій папці.

**Логіка:**

```
1. Отримати GOOGLE_DRIVE_ROOT_FOLDER_ID з config
2. Знайти папку з назвою поточного місяця у корені
3. Якщо знайдена → повернути її ID
4. Якщо не знайдена → створити нову папку
```

**Повертає:** ID папки месяца

##### `make_safe_filename_part(text: str) -> str`

Очищає текст для використання у назві файлу:

```python
make_safe_filename_part("ягоди в офіс")  
# → "yagody-v-ofis" (результат залежить від кодування)
```

**Трансформації:**
- Нижній регістр
- Пробіли → дефіси
- Видаляє недозволені символи

##### `upload_receipt_to_drive(drive_service, local_file_path, original_filename, description) -> str`

Завантажує файл на Google Drive.

**Логіка:**

```
1. Отримати або створити папку місяця
2. Сформувати назву файлу:
   YYYY-MM-DD_HH-MM-SS_safe-description.ext
3. Завантажити файл
4. Повернути посилання на файл
```

**Повертає:** URL для перегляду файлу

```
https://drive.google.com/file/d/{FILE_ID}/view
```

---

### 📄 google_sheets.py

**Назва:** Функції для Google Sheets  
**Призначення:** Запис даних у Google Sheets

#### Функція:

##### `append_expense_row(sheets_service, sheet_tab, date, amount, description, receipt_link)`

Додає новий рядок у вкладку Google Sheets.

**Структура рядка:**

| Колона | Назва | Значення |
|--------|-------|----------|
| A | Дата | `date` (ДД.МММ.РРРР) |
| B | (резерв) | (пусто) |
| C | (резерв) | (пусто) |
| D | Описание | `description` |
| E | Приход | (пусто) |
| F | Расход | `amount` |
| G | Чек | `receipt_link` (URL на Google Drive) |

**Приклад:**

```
25.06.2026 | | | ягоди в офіс | | 320.50 | https://drive.google.com/...
```

---

### 📄 ocr.py

**Назва:** OCR обробка  
**Призначення:** Витяг суми та дати з чеків за допомогою Anthropic API

#### Функції:

##### `extract_receipt_data(image_path: str) -> dict[str, str]`

**Вхідні дані:**
- Шлях до фото або скану чека

**Вихідні дані:**
```python
{
    "amount": "320.50",      # Сума операції
    "date": "15.06.2026"     # Дата у форматі ДД.МММ.РРРР
}
```

**Як працює:**

1. Перевіряє наявність файлу та API ключа
2. Кодує файл у base64
3. Визначає тип MIME (image/jpeg, image/png, application/pdf)
4. Надсилає до Anthropic Claude з промптом для OCR
5. Парсить JSON відповідь
6. Повертає результат (або пусті рядки, якщо помилка)

**Промпт для Claude:**

```
Це фото або скан фінансового документу...
Витягни два значення:
1. Суму операції/платежу/покупки
2. Дату операції у форматі ДД.МММ.РРРР

Відповідай ТІЛЬКИ у форматі JSON:
{"amount": "320.50", "date": "15.06.2026"}
```

**Обробка помилок:**

- Файл не знайдено → повертає `{"amount": "", "date": ""}`
- API ключ не налаштований → повертає `{"amount": "", "date": ""}`
- Невдалий парсинг JSON → повертає `{"amount": "", "date": ""}`

---

### 📄 test_ocr.py

**Назва:** Тести для OCR  
**Призначення:** Локальне тестування функціональності OCR

Дозволяє протестувати OCR обробку без запуску бота:

```bash
python test_ocr.py
```

---

## Змінні середовища

### Обов'язкові змінні:

| Змінна | Приклад | Опис |
|--------|---------|------|
| `TELEGRAM_BOT_TOKEN` | `123456:ABCdef...` | Токен Telegram бота від BotFather |
| `GOOGLE_DRIVE_ROOT_FOLDER_ID` | `1abc2DEF3ghI4jkl5MNO6pqR7s8t9u0V` | ID папки на Google Drive для файлів |
| `GOOGLE_SHEET_ID` | `1abc2DEF3ghI4jkl5MNO6pqR7s8t9u0V` | ID Google Sheets документа |

### Для авторизації Google (вибір одного):

**Вариант 1: OAuth 2.0 файл (default)**
```
GOOGLE_OAUTH_CLIENT_SECRET_FILE=client_secret.json
GOOGLE_OAUTH_TOKEN_FILE=token.json
```

**Варіант 2: OAuth 2.0 JSON в env**
```
GOOGLE_CLIENT_SECRET_JSON={"type": "oauth2_installed", ...}
GOOGLE_TOKEN_JSON={"type": "authorized_user", ...}
```

**Варіант 3: Service Account (для Sheets)**
```
GOOGLE_SERVICE_ACCOUNT_JSON={"type": "service_account", ...}
```

### Опціональні змінні:

| Змінна | За замовчуванням | Опис |
|--------|------------------|------|
| `ANTHROPIC_API_KEY` | (не встановлено) | API ключ для OCR обробки |
| `TIMEZONE` | `Europe/Warsaw` | Часова зона для записання дат |

### Приклад .env файлу:

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCDefGhIJKlmnOpQrStUVwxYzAbCdEfGhI

# Google OAuth
GOOGLE_OAUTH_CLIENT_SECRET_FILE=client_secret.json
GOOGLE_OAUTH_TOKEN_FILE=token.json

# Google IDs
GOOGLE_DRIVE_ROOT_FOLDER_ID=1abc2DEF3ghI4jkl5MNO6pqR7s8t9u0V
GOOGLE_SHEET_ID=1xyz9ABC2DEF3ghI4jkl5MNO6pqR7s8t9u0V

# Anthropic (опціонально)
ANTHROPIC_API_KEY=sk-ant-v0-...

# Часова зона (опціонально)
TIMEZONE=Europe/Kyiv
```

---

## Розробка та тестування

### Встановлення в режимі розробки:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Тестування OCR:

```bash
python test_ocr.py <path_to_image>
```

Приклад:

```bash
python test_ocr.py ./sample_receipt.jpg
```

### Запуск бота локально:

```bash
python app.py
```

Бот запуститься та буде слухати повідомлення.

### Отримання логів:

Додайте логування у `app.py`:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Бот запущено")
logger.error("Помилка при завантаженні файла")
```

### Типові помилки та вирішення:

#### "TELEGRAM_BOT_TOKEN not configured"
- Перевіріть, що `.env` файл існує
- Перевіріть, що `python-dotenv` встановлений
- Перевіріть, що токен скопійований правильно

#### "GOOGLE_DRIVE_ROOT_FOLDER_ID not configured"
- Переконайтесь, що папка на Google Drive існує
- Скопіюйте ID з URL правильно
- Переконайтесь, що в `.env` встановлені правильні значення

#### "OAuth token expired"
- Видаліть файл `token.json`
- Запустіть бота заново
- Авторизуйтесь в браузері, коли з'явиться запит

#### "user_id: XXXX не знайдено"
- Додайте `user_id` у `users.py`
- Переконайтесь, що заповнені поля `name` та `sheet_tab`
- Переконайтесь, що `sheet_tab` відповідає назві вкладки у Google Sheets

---

## Часті питання

### Q: Як змінити часову зону?
**A:** Змініть значення `TIMEZONE` у `.env`:
```
TIMEZONE=Europe/Kyiv
```

### Q: Як додати нового користувача?
**A:**
1. Користувач пише боту `/whoami` та отримує свій `user_id`
2. Додайте запис у `users.py`:
```python
YOUR_ID: {
    "name": "USERNAME",
    "sheet_tab": "SHEET_TAB_NAME",
}
```

### Q: Чому OCR не працює?
**A:** Перевіріть:
- Чи встановлена змінна `ANTHROPIC_API_KEY`?
- Чи активний API ключ на Anthropic?
- Чи правильно кодований файл?

### Q: Як розгорнути бота на сервері?
**A:** Рекомендується використовувати:
- **Heroku** (вбудований git deploy)
- **AWS EC2/Lightsail** (на Python сервері)
- **DigitalOcean App Platform**
- **PythonAnywhere** (для Pythonботів)

Переконайтесь, що на сервері:
- Python 3.8+
- Змінні середовища правильно встановлені
- Бот запускається з `python app.py`

---

## Ліцензія

Проект розроблений для внутрішнього використання.

---

## Контакти та підтримка

Для питань та проблем:
1. Перевіріть цю документацію
2. Перевіріть логи бота
3. Напишіть розробнику

---

**Остання оновлення:** 2026-06-25  
**Версія:** 1.0 (MVP)
