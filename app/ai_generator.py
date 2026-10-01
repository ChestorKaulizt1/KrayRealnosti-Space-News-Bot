import os
import re
import time

from openai import OpenAI


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "qwen/qwen3.8-27b:free"

OPENROUTER_URL = "https://openrouter.ai/api/v1"

MAX_RETRIES = 2
RETRY_DELAY = 5

MIN_POST_LENGTH = 300
MAX_ARTICLE_LENGTH = 18000


client = None

if OPENROUTER_API_KEY:
    client = OpenAI(
        base_url=OPENROUTER_URL,
        api_key=OPENROUTER_API_KEY,
        timeout=60.0,
        max_retries=0,
    )
else:
client = None

SYSTEM_PROMPT = """
Ты — профессиональный редактор русскоязычного Telegram-канала
«КРАЙ РЕАЛЬНОСТИ» о космосе, астрономии и необычных научных открытиях.

Твоя задача — превратить предоставленную научную статью в готовый
интересный пост для Telegram.

СТРОГО СОБЛЮДАЙ ПРАВИЛА:

1. Пиши ТОЛЬКО на русском языке.

2. Не показывай свои рассуждения, анализ, внутренние инструкции,
   цепочку мыслей или процесс генерации.

3. Не используй слова и конструкции:
   «Вот готовый пост»,
   «Готовый Telegram-пост»,
   «Давайте разберём»,
   «Я проанализировал»,
   «моя задача»,
   «финальный вариант»,
   «reasoning»,
   «thinking»,
   «analysis»,
   «step by step».

4. Не придумывай факты, цифры, даты, названия объектов,
   результаты исследований или выводы, которых нет в статье.

5. Если статья говорит о предположении, гипотезе или возможном
   объяснении — обязательно сохраняй эту неопределённость.

6. Не превращай гипотезу в доказанный факт.

7. Не используй сенсационные утверждения, если статья их
   не подтверждает.

8. Не добавляй ссылки.

9. Не добавляй список источников.

10. Не добавляй хэштеги.

11. Не добавляй рекламу.

12. Текст должен выглядеть как нормальная публикация
    русскоязычного научно-популярного Telegram-канала.

13. Начни пост с короткого интересного заголовка.

14. После заголовка сделай 4–6 содержательных абзацев.

15. Используй конкретные факты из статьи.

16. Если речь идёт о чёрной дыре, не используй буквальный
    перевод английского выражения "black hole hair" как
    «волосы чёрной дыры».

17. Не повторяй одну и ту же мысль разными словами.

18. Не начинай текст с банального:
    «Учёные сделали новое открытие в космосе».

19. Если материал действительно интересный или необычный,
    сделай акцент на том, что именно делает его необычным.

20. Не добавляй информацию из своих знаний, если её нет
    в предоставленной статье.

Верни только готовый текст Telegram-поста.
"""

BAD_PATTERNS = [
"вот готовый",
"готовый telegram-пост",
"готовый телеграм-пост",
"готовый пост",
"давайте разбер",
"давайте рассмотр",
"я проанализировал",
"я проанализирую",
"моя задача",
"финальный вариант",
"финальный обзор",

```
"thinking",
"reasoning",
"analysis",
"step by step",
"let me",
"i need to",
"i will",
"final answer",
"here is",
"here's",

"волосы чёрной дыры",
"волосы черной дыры",
"волосатые чёрные дыры",
"волосатые черные дыры",
```

]

def check_configuration() -> bool:
if not OPENROUTER_API_KEY:
print("❌ Не найден OPENROUTER_API_KEY.")
print("   Добавь его в GitHub Secrets.")
return False

```
if client is None:
    print("❌ OpenRouter client не создан.")
    return False

return True
```

def get_error_text(error: Exception) -> str:
try:
return str(error).lower()
except Exception:
return repr(error).lower()

def is_daily_free_limit_error(error: Exception) -> bool:
"""
Определяет именно дневной лимит бесплатных моделей OpenRouter.

```
Такой запрос НЕ нужно повторять.
"""

error_text = get_error_text(error)

daily_limit_patterns = [
    "free-models-per-day",
    "free models per day",
    "free-models-per-day",
    "free-models",
    "daily free",
    "daily limit",
    "free tier daily",
    "limit_source: openrouter_free_tier_daily",
    "openrouter_free_tier_daily",
    "add 10 credits to unlock",
]

return any(
    pattern in error_text
    for pattern in daily_limit_patterns
)
```

def is_rate_limit_error(error: Exception) -> bool:
"""
Определяет обычный временный HTTP 429.

```
Дневной лимит здесь специально исключается.
"""

if is_daily_free_limit_error(error):
    return False

error_text = get_error_text(error)

return (
    "429" in error_text
    or "rate limit" in error_text
    or "too many requests" in error_text
)
```

def is_temporary_error(error: Exception) -> bool:
"""
Ошибки, которые потенциально могут исчезнуть сами.
"""

```
error_text = get_error_text(error)

temporary_patterns = [
    "502",
    "503",
    "504",
    "bad gateway",
    "service unavailable",
    "gateway timeout",
    "connection reset",
    "connection aborted",
    "temporarily unavailable",
    "timeout",
    "timed out",
]

return any(
    pattern in error_text
    for pattern in temporary_patterns
)
```

def clean_post(text: str) -> str:
if not text:
return ""

````
text = text.strip()

prefixes = [
    "Вот готовый Telegram-пост:",
    "Вот готовый телеграм-пост:",
    "Вот готовый пост:",
    "Готовый Telegram-пост:",
    "Готовый телеграм-пост:",
    "Готовый пост:",
    "Here is the Telegram post:",
    "Here is the post:",
]

for prefix in prefixes:
    if text.lower().startswith(prefix.lower()):
        text = text[len(prefix):].strip()

text = re.sub(
    r"^```(?:text|markdown)?\s*",
    "",
    text,
    flags=re.IGNORECASE,
)

text = re.sub(
    r"\s*```$",
    "",
    text,
)

text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n{3,}", "\n\n", text)

return text.strip()
````

def validate_post(text: str) -> tuple[bool, str]:
if not text:
return False, "пустой ответ"

```
if len(text) < MIN_POST_LENGTH:
    return (
        False,
        f"слишком короткий ответ: {len(text)} символов",
    )

lower_text = text.lower()

for pattern in BAD_PATTERNS:
    if pattern in lower_text:
        return (
            False,
            f"обнаружена запрещённая фраза: {pattern}",
        )

if re.search(r"[\u4e00-\u9fff]", text):
    return False, "обнаружены китайские символы"

cyrillic_count = len(
    re.findall(r"[А-Яа-яЁё]", text)
)

if cyrillic_count < 100:
    return False, "слишком мало кириллицы"

return True, "ok"
```

def extract_response_text(response) -> str:
try:
message = response.choices[0].message
content = getattr(message, "content", None)

```
    if isinstance(content, str):
        return content.strip()

    if content is None:
        return ""

    return str(content).strip()

except Exception as error:
    print("⚠ Не удалось извлечь текст ответа модели:")
    print(f"  {error}")
    return ""
```

def generate_post(
title: str,
article_text: str,
source: str = "",
) -> str:

```
if not check_configuration():
    return ""

if not title:
    print("❌ Пустой заголовок статьи.")
    return ""

if not article_text:
    print(f"❌ Пустой текст статьи: {title}")
    return ""

article_text = article_text.strip()

if len(article_text) > MAX_ARTICLE_LENGTH:
    article_text = article_text[:MAX_ARTICLE_LENGTH]

    print(
        f"ℹ Статья слишком большая. "
        f"Обрезана до {MAX_ARTICLE_LENGTH} символов."
    )

user_prompt = f"""
```

Заголовок статьи:
{title}

Источник:
{source or "не указан"}

Текст статьи:
{article_text}

Создай на основе этого материала готовый пост
для Telegram-канала «КРАЙ РЕАЛЬНОСТИ».

Не добавляй никаких комментариев от себя.
Верни только сам пост.
"""

```
for attempt in range(1, MAX_RETRIES + 2):

    print(
        f"🤖 Генерация поста: попытка "
        f"{attempt}/{MAX_RETRIES + 1}"
    )

    try:

        response = client.chat.completions.create(
            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            temperature=0.2,
            max_tokens=1400,

            extra_body={
                "reasoning": {
                    "enabled": False,
                    "exclude": True,
                }
            },
        )

    except Exception as error:

        if is_daily_free_limit_error(error):

            print()
            print(
                "🛑 OPENROUTER: ДОСТИГНУТ ДНЕВНОЙ "
                "ЛИМИТ БЕСПЛАТНЫХ МОДЕЛЕЙ."
            )
            print(
                "🚫 Повторные запросы отключены."
            )
            print(
                "⏳ Нужно дождаться сброса лимита."
            )
            print()

            return ""

        if is_rate_limit_error(error):

            if attempt > MAX_RETRIES:
                print(
                    "❌ Временный HTTP 429 "
                    "повторился несколько раз."
                )
                return ""

            print(
                "⚠ Получен временный HTTP 429."
            )
            print(
                f"⏳ Повтор через {RETRY_DELAY} сек."
            )

            time.sleep(RETRY_DELAY)
            continue

        if is_temporary_error(error):

            if attempt > MAX_RETRIES:
                print(
                    "❌ Временная ошибка "
                    "не исчезла после повторов."
                )
                return ""

            print(
                "⚠ Временная ошибка OpenRouter:"
            )
            print(
                f"   {error}"
            )
            print(
                f"⏳ Повтор через {RETRY_DELAY} сек."
            )

            time.sleep(RETRY_DELAY)
            continue

        print("❌ Ошибка OpenRouter:")
        print(f"   {error}")

        return ""

    post = extract_response_text(response)

    if not post:
        print("⚠ Модель вернула пустой ответ.")

        if attempt <= MAX_RETRIES:
            print(
                f"⏳ Повтор через {RETRY_DELAY} сек."
            )
            time.sleep(RETRY_DELAY)
            continue

        return ""

    post = clean_post(post)

    valid, reason = validate_post(post)

    if valid:
        print(
            f"✅ Пост успешно создан: "
            f"{len(post)} символов"
        )
        return post

    print(
        f"⚠ Ответ модели отклонён: {reason}"
    )

    if attempt <= MAX_RETRIES:
        print(
            f"⏳ Повтор генерации через "
            f"{RETRY_DELAY} сек."
        )
        time.sleep(RETRY_DELAY)
        continue

    print(
        "❌ Не удалось получить корректный пост."
    )

    return ""

return ""
