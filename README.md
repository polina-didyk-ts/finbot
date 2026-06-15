# Finance Receipt Bot (MVP)

Цей Telegram-бот допомагає завантажувати чеки у спільний Google Drive та записувати рядки у Google Sheets (по вкладках для кожного користувача). Це MVP без OCR.

**Що робить бот**

- Приймає фото/документ (чек) з описом у підписі.
- Перевіряє, чи користувач дозволений.
- Завантажує файл у Google Drive у папку поточного місяця (наприклад: `2025-05`).
- Додає рядок у Google Sheets у вкладку конкретного користувача.
- Повертає підтвердження в Telegram.

**Workflow**

1. Користувач надсилає фото або документ у чат з ботом.
2. У підписі вказує опис покупки, наприклад: `ягоди в офіс`.
3. Бот зберігає файл у Google Drive у папку поточного місяця і додає рядок у вкладку користувача у Google Sheets.

## Налаштування

1. Створіть бота через BotFather та отримайте `TELEGRAM_BOT_TOKEN`.
2. Створіть Google Cloud Project.
3. Увімкніть API: Google Drive API та Google Sheets API.
4. Створіть OAuth 2.0 Client ID (Desktop app):
   - В Google Cloud Console зайдіть в `APIs & Services` → `Credentials` → `Create credentials` → `OAuth client ID`.
   - Виберіть `Application type: Desktop app`.
   - Завантажте JSON та перейменуйте його в `client_secret.json`.
   - Покладіть `client_secret.json` поруч з `app.py`.
5. Підготуйте Google Sheets: створіть вкладки для 4 користувачів. У кожній вкладці додайте колонки у першому рядку:
   `дата | расход | примечания | чек | статус`

## Отримання ідентифікаторів

- `GOOGLE_DRIVE_ROOT_FOLDER_ID` — ID папки у Google Drive, куди бот має додавати папки місяців.
- `GOOGLE_SHEET_ID` — ID Google Sheets (з URL файлу).

## .env

Скопіюйте `.env.example` у `.env` і заповніть змінні:

- `TELEGRAM_BOT_TOKEN`
- `GOOGLE_OAUTH_CLIENT_SECRET_FILE` (наприклад `client_secret.json`)
- `GOOGLE_OAUTH_TOKEN_FILE` (наприклад `token.json` — буде створено після авторизації)
- `GOOGLE_DRIVE_ROOT_FOLDER_ID`
- `GOOGLE_SHEET_ID`
- `TIMEZONE` (за замовчуванням `Europe/Warsaw`)

При першому запуску програми відкриється браузер для авторизації Google — після підтвердження збережеться файл `token.json`.
НЕ комітьте `client_secret.json` і `token.json` у VCS.

## Встановлення та запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Як отримати `user_id`

Відправте команду `/whoami` боту — він поверне ваш `user_id` і `username`. Додайте `user_id` у `users.py` за шаблоном.

## Тестування MVP

1. Додайте ваш `user_id` у `users.py` і вкажіть `sheet_tab`.
2. Надішліть фото чеку з caption `ягоди в офіс`.
3. Перевірте у Google Drive, що у папці поточного місяця з'явився файл.
4. Перевірте правильну вкладку у Google Sheets — має з'явитись рядок з датою, пустим `расход`, описом, посиланням на чек і статусом `uploaded`.

## Зауваги

- Використовується OAuth2 (user credentials). Після першого запуску авторизація пройде у браузері і буде створено `token.json`.
- Не додавайте `client_secret.json`, `token.json` та `.env` у систему контролю версій.
- OCR, автоматичний парсинг сум та база даних будуть додані пізніше.
