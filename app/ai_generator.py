import os
import re
import time
from typing import Optional

from openai import OpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1"

MODELS = [
"qwen/qwen3.8-27b:free",
"nvidia/nemotron-3-nano-30b-a3b:free",
"openrouter/free",
]

MAX_RETRIES = 2
RETRY_DELAYS = [10, 30]

MIN_POST_LENGTH = 300
MAX_ARTICLE_LENGTH = 18000

SYSTEM_PROMPT = """
Ты редактор Telegram-канала «КРАЙ РЕАЛЬНОСТИ».

Создай интересный Telegram-пост на русском языке
по переданной научной статье.

Используй только факты из статьи.
Не выдумывай информацию.
Не используй кликбейт.
Не упоминай искусственный интеллект.
Пиши простым и понятным языком.
Используй короткие абзацы.

Начни сразу с готового текста.

В конце добавь:

🚀 Подписывайтесь на «КРАЙ РЕАЛЬНОСТИ», чтобы не пропускать
самые интересные открытия Вселенной.

Длина поста: примерно 1200–2200 символов.
"""

BAD_PATTERNS = [
"как искусственный интеллект",
"как ии",
"я не могу",
"вот готовый пост",
"вот пост для telegram",
]

def check_configuration() -> bool:
if not OPENROUTER_API_KEY:
print("❌ OPENROUTER_API_KEY не найден.")
return False

```
return True
```

def get_client() -> OpenAI:
return OpenAI(
api_key=OPENROUTER_API_KEY,
base_url=OPENROUTER_URL,
timeout=90.0,
max_retries=0,
)

def get_status_code(error) -> Optional[int]:
status_code = getattr(error, "status_code", None)

```
if status_code:
    try:
        return int(status_code)
    except Exception:
        pass

response = getattr(error, "response", None)

if response is not None:
    status_code = getattr(response, "status_code", None)

    if status_code:
        try:
            return int(status_code)
        except Exception:
            pass

return None
```

def get_error_text(error) -> str:
parts = []

```
status_code = get_status_code(error)

if status_code:
    parts.append(f"HTTP {status_code}")

body = getattr(error, "body", None)

if body:
    parts.append(str(body))

response = getattr(error, "response", None)

if response is not None:
    try:
        response_text = response.text

        if response_text:
            parts.append(response_text)
    except Exception:
        pass

message = str(error)

if message:
    parts.append(message)

return " | ".join(parts)[:3000]
```

def get_retry_after(error) -> Optional[int]:
response = getattr(error, "response", None)

```
if response is None:
    return None

try:
    value = response.headers.get("retry-after")

    if value is None:
        value = response.headers.get("Retry-After")

    if value is not None:
        seconds = int(float(value))

        if seconds > 0:
            return seconds

except Exception:
    pass

return None
```

def is_rate_limit_error(error) -> bool:
status_code = get_status_code(error)

```
if status_code == 429:
    return True

text = get_error_text(error).lower()

return (
    "429" in text
    or "rate limit" in text
    or "rate_limit" in text
    or "too many requests" in text
)
```

def is_daily_limit_error(error) -> bool:
text = get_error_text(error).lower()

```
patterns = [
    "free-models-per-day",
    "free_models_per_day",
    "openrouter_free_tier_daily",
    "free tier daily",
    "daily limit",
    "daily quota",
    "quota exceeded",
]

for pattern in patterns:
    if pattern in text:
        return True

return False
```

def clean_post(text: str) -> str:
if not text:
return ""

````
text = text.strip()

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

prefixes = [
    "Вот готовый пост:",
    "Вот пост:",
    "Готовый пост:",
    "Telegram-пост:",
    "Пост:",
]

for prefix in prefixes:
    if text.lower().startswith(prefix.lower()):
        text = text[len(prefix):].strip()

text = re.sub(r"[ \t]+", " ", text)

text = re.sub(r"\n{3,}", "\n\n", text)

return text.strip()
````

def validate_post(text: str) -> bool:
if not text:
return False

```
if len(text) < MIN_POST_LENGTH:
    print(
        f"⚠ Пост слишком короткий: {len(text)} символов."
    )
    return False

if len(text) > 6000:
    print(
        f"⚠ Пост слишком длинный: {len(text)} символов."
    )
    return False

lower_text = text.lower()

for pattern in BAD_PATTERNS:
    if pattern in lower_text:
        print(
            f"⚠ Найдена запрещённая фраза: {pattern}"
        )
        return False

return True
```

def extract_text(response) -> str:
try:
if not response.choices:
return ""

```
    message = response.choices[0].message
    content = message.content

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    return str(content)

except Exception:
    return ""
```

def build_prompt(
article_title: str,
article_text: str,
) -> str:

```
if len(article_text) > MAX_ARTICLE_LENGTH:
    article_text = article_text[:MAX_ARTICLE_LENGTH]

return f"""
```

Заголовок статьи:

{article_title}

Текст статьи:

{article_text}

Создай готовый пост для Telegram-канала
«КРАЙ РЕАЛЬНОСТИ».

Используй только информацию из статьи.
Не добавляй выдуманные факты.
"""

def try_model(
client: OpenAI,
model: str,
article_title: str,
article_text: str,
) -> Optional[str]:

```
prompt = build_prompt(
    article_title,
    article_text,
)

for attempt in range(MAX_RETRIES + 1):

    print(f"🤖 Модель: {model}")

    print(
        f"   Попытка "
        f"{attempt + 1}/"
        f"{MAX_RETRIES + 1}"
    )

    try:

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=2200,
        )

        text = extract_text(response)

        text = clean_post(text)

        if not text:
            print("⚠ Получен пустой ответ.")
            return None

        if not validate_post(text):
            print("⚠ Пост не прошёл проверку.")
            return None

        print(
            f"✓ Пост создан: {len(text)} символов."
        )

        return text

    except Exception as error:

        status = get_status_code(error)

        print(
            f"⚠ Ошибка: HTTP {status or '?'}"
        )

        print(
            get_error_text(error)[:1000]
        )

        if is_daily_limit_error(error):

            print(
                "➡ Достигнут дневной лимит модели."
            )

            return None

        if is_rate_limit_error(error):

            if attempt < MAX_RETRIES:

                retry_after = get_retry_after(error)

                if retry_after:
                    delay = min(retry_after, 120)
                else:
                    delay = RETRY_DELAYS[attempt]

                print(
                    f"⏳ Повтор через {delay} сек."
                )

                time.sleep(delay)

                continue

            print(
                "➡ 429 сохраняется. "
                "Переходим к следующей модели."
            )

            return None

        print(
            "➡ Переходим к следующей модели."
        )

        return None

return None
```

def generate_post(
article_title: str,
article_text: str,
) -> Optional[str]:

```
if not check_configuration():
    return None

if not article_title:
    print("❌ Пустой заголовок.")
    return None

if not article_text:
    print("❌ Пустой текст статьи.")
    return None

client = get_client()

print(
    f"🔄 Доступно моделей: {len(MODELS)}"
)

for index, model in enumerate(
    MODELS,
    start=1,
):

    print()
    print(
        "========================================"
    )

    print(
        f"🔹 Модель {index}/{len(MODELS)}: {model}"
    )

    print(
        "========================================"
    )

    post = try_model(
        client=client,
        model=model,
        article_title=article_title,
        article_text=article_text,
    )

    if post:

        print(
            f"✅ Успешно создано через {model}"
        )

        return post

    if index < len(MODELS):

        print(
            "➡ Переключение на следующую модель..."
        )

        time.sleep(3)

print()

print("❌ Все модели недоступны.")

return None
```

if **name** == "**main**":

```
print("Проверка AI Generator")

if check_configuration():

    print("✓ OPENROUTER_API_KEY найден")

    print("✓ Модели:")

    for model in MODELS:
        print(f"  - {model}")

else:

    print("❌ OPENROUTER_API_KEY отсутствует")
```
