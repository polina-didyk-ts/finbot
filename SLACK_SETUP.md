# Slack-бот: налаштування (2027)

Slack-бот робить те саме, що Telegram-бот: чеки та надходження зі спільного Slack-каналу потрапляють у Google Sheets, а документи — у Google Drive. Логіка спільна (`processing.py`), тому обидва боти можуть працювати паралельно: Telegram — зі старою таблицею, Slack — з новою.

## Як користуватись

У спільному каналі:

| Повідомлення | Результат |
|---|---|
| фото/файл з підписом `ягоди в офіс` | витрата → колонка «Расход» |
| фото/файл з підписом `+ оплата від клієнта` | надходження → колонка «Приход» |
| текст `+5000 оплата від клієнта` / `+120 PLN повернення` | надходження без документа |
| `help` | підказка |

Бот відповідає в треді під повідомленням. Звичайні повідомлення без файлу і без `+` він ігнорує, тож у каналі можна спілкуватися. Кілька файлів в одному повідомленні записуються як окремі чеки з однаковим описом.

## 1. Створити Slack App

Може знадобитися схвалення адміністратора Slack-воркспейсу.

1. Відкрити https://api.slack.com/apps → **Create New App** → **From a manifest**.
2. Обрати воркспейс і вставити вміст файлу `slack_manifest.yaml`.
3. **Install to Workspace** → дозволити. Скопіювати **Bot User OAuth Token** (`xoxb-...`) → це `SLACK_BOT_TOKEN`.
4. **Basic Information → App-Level Tokens → Generate Token**, scope `connections:write`. Скопіювати токен (`xapp-...`) → це `SLACK_APP_TOKEN`.

## 2. Канал

1. Створити канал (наприклад `#finreports`) і додати бота: `/invite @finbot`.
2. ID каналу: клік на назву каналу → внизу вікна `Channel ID` (`C0...`) → `SLACK_CHANNEL_ID`.

## 3. Google-таблиця і папка на 2027

1. Створити таблицю з такою самою структурою: вкладка на людину, колонки A–G (дата | | | опис | приход | расход | чек).
2. Створити папку в Google Drive.
3. Дати доступ на редагування тому Google-акаунту, через який працює бот (той самий, що й для Telegram-бота).
4. ID з URL → `SLACK_GOOGLE_SHEET_ID` і `SLACK_GOOGLE_DRIVE_ROOT_FOLDER_ID`.

## 4. Змінні середовища

На додачу до наявних (`ANTHROPIC_API_KEY`, Google-авторизація, `TIMEZONE`):

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_CHANNEL_ID=C0123456789
SLACK_GOOGLE_SHEET_ID=...
SLACK_GOOGLE_DRIVE_ROOT_FOLDER_ID=...
```

`TELEGRAM_BOT_TOKEN`, `GOOGLE_SHEET_ID` і `GOOGLE_DRIVE_ROOT_FOLDER_ID` Slack-бот не використовує.

## 5. Користувачі

Кожен учасник надсилає в канал будь-яке повідомлення з `+`, наприклад `+1 тест`. Бот відповість його Slack ID (`U...`). Додати ID у `SLACK_USERS` у `users.py`:

```python
SLACK_USERS = {
    "U01ABCDEF": {"name": "polyanakw", "sheet_tab": "Поля"},
    ...
}
```

## 6. Запуск

```bash
pip install -r requirements.txt
python slack_bot.py
```

На хостингу Slack-бот — це **окремий сервіс/процес** з командою `python slack_bot.py`, поруч із Telegram-ботом (`python app.py`). Socket Mode не потребує публічної адреси чи вебхуків.
