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

MAX_RETRIES_PER_MODEL = 2

RETRY_DELAYS = [10, 30]

MIN_POST_LENGTH = 300
MAX_ARTICLE_LENGTH = 18000

SYSTEM_PROMPT = """
Ты — редактор Telegram-канала «КРАЙ РЕАЛЬНОСТИ».

Тематика канала:
космос, астрономия, планеты, звёзды, чёрные дыры,
экзопланеты, космические миссии, астероиды, галактики,
телескопы, космические открытия и необычные явления Вселенной.

Твоя задача — превратить научную статью в интересный Telegram-пост
на русском языке.

ОБЯЗАТЕЛЬНО:

1. Не выдумывай факты.
2. Используй только информацию из переданной статьи.
3. Сохраняй научный смысл.
4. Если в статье есть числа, расстояния, даты, температуры,
   размеры или другие конкретные значения — не изменяй их.
5. Не используй кликбейт вроде «учёные в шоке» или
   «это перевернуло науку».
6. Не начинай каждый пост одинаково.
7. Текст должен быть живым и понятным обычному читателю.
8. Сложные научные термины объясняй простыми словами.
9. Не добавляй информацию, которой нет в статье.
10. Не упоминай, что текст создан ИИ.
11. Не используй Markdown-заголовки с #.

СТРУКТУРА:

Начни с сильной первой фразы.

Затем объясни:
— что обнаружили или произошло;
— где это находится;
— почему это интересно;
— что именно выяснили учёные;
— что это может означать, если статья действительно это обсуждает.

Используй короткие абзацы.

В конце добавь:

🚀 Подписывайтесь на «КРАЙ РЕАЛЬНОСТИ», чтобы не пропускать
самые интересные открытия Вселенной.

Длина:
примерно 1200–2200 символов.

Не пиши:
«Вот готовый пост».
«Вот пост для Telegram».
«По вашему запросу».

Сразу начинай с готового текста.
"""

BAD_PATTERNS = [
"как искусственный интеллект",
"как ии",
"я не могу",
"я не могу помочь",
"вот готовый пост",
"вот пост",
"по вашему запросу",
"источник:",
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

result = " | ".join(parts)

if len(result) > 3000:
    result = result[:3000]

return result
```

def get_retry_after(error) -> Optional[int]:
response = getattr(error, "response", None)

```
if response is None:
    return None

try:
    headers = response.headers

    value = headers.get("retry-after")

    if value is None:
        value = headers.get("Retry-After")

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

def is_daily_free_limit_error(error) -> bool:
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
    "free model limit",
]

return any(pattern in text for pattern in patterns)
```

def is_temporary_error(error) -> bool:
status_code = get_status_code(error)

```
if status_code in (408, 409, 425, 500, 502, 503, 504):
    return True

text = get_error_text(error).lower()

patterns = [
    "timeout",
    "timed out",
    "temporarily unavailable",
    "overloaded",
    "upstream",
    "connection reset",
    "connection aborted",
]

return any(pattern in text for pattern in patterns)
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

text = re.sub(r"\s*```$", "", text)

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
        f"⚠ Пост слишком короткий: "
        f"{len(text)} символов."
    )
    return False

if len(text) > 6000:
    print(
        f"⚠ Пост слишком длинный: "
        f"{len(text)} символов."
    )
    return False

lower_text = text.lower()

for bad_pattern in BAD_PATTERNS:
    if bad_pattern in lower_text:
        print(
            f"⚠ Обнаружена нежелательная фраза: "
            f"{bad_pattern}"
        )
        return False

return True
```

def extract_response_text(response) -> str:
try:
choices = getattr(response, "choices", None)

```
    if not choices:
        return ""

    message = getattr(
        choices[0],
        "message",
        None,
    )

    if message is None:
        return ""

    content = getattr(
        message,
        "content",
        None,
    )

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    return str(content)

except Exception:
    return ""
```

def build_user_prompt(
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

Напиши готовый пост для Telegram-канала
«КРАЙ РЕАЛЬНОСТИ».

Пост должен быть самостоятельным,
интересным и понятным.

Не добавляй факты,
которых нет в статье.
"""

def generate_with_model(
client: OpenAI,
model: str,
article_title: str,
article_text: str,
) -> Optional[str]:

```
user_prompt = build_user_prompt(
    article_title,
    article_text,
)

for attempt in range(MAX_RETRIES_PER_MODEL + 1):

    attempt_number = attempt + 1

    print(
        f"🤖 Модель: {model}"
    )

    print(
        f"   Попытка "
        f"{attempt_number}/"
        f"{MAX_RETRIES_PER_MODEL + 1}"
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
                    "content": user_prompt,
                },
            ],
            temperature=0.7,
            max_tokens=2200,
            extra_body={
                "reasoning": {
                    "enabled": False,
                    "exclude": True,
                }
            },
        )

        text = extract_response_text(
            response
        )

        if not text:
            print(
                "⚠ Модель вернула "
                "пустой ответ."
            )
            return None

        text = clean_post(text)

        if not validate_post(text):
            print(
                "⚠ Ответ не прошёл "
                "проверку."
            )
            return None

        print(
            f"✓ Пост создан: "
            f"{len(text)} символов."
        )

        return text

    except Exception as error:

        status_code = get_status_code(
            error
        )

        error_text = get_error_text(
            error
        )

        print(
            f"⚠ Ошибка модели "
            f"{model}: "
            f"HTTP {status_code or '?'}"
        )

        print(
            error_text[:1000]
        )

        if is_daily_free_limit_error(
            error
        ):

            print(
                "⚠ Достигнут дневной "
                "лимит бесплатной модели."
            )

            return None

        if is_rate_limit_error(
            error
        ):

            retry_after = get_retry_after(
                error
            )

            if retry_after is not None:
                delay = min(
                    retry_after,
                    120,
                )
            elif attempt < len(
                RETRY_DELAYS
            ):
                delay = RETRY_DELAYS[
                    attempt
                ]
            else:
                delay = 60

            if attempt < MAX_RETRIES_PER_MODEL:

                print(
                    f"⏳ Rate limit. "
                    f"Повтор через "
                    f"{delay} сек."
                )

                time.sleep(delay)

                continue

            print(
                "➡ Модель временно "
                "недоступна."
            )

            return None

        if is_temporary_error(
            error
        ):

            if attempt < MAX_RETRIES_PER_MODEL:

                delay = RETRY_DELAYS[
                    attempt
                ]

                print(
                    f"⏳ Временная ошибка. "
                    f"Повтор через "
                    f"{delay} сек."
                )

                time.sleep(delay)

                continue

            print(
                "➡ Сервер не восстановился."
            )

            return None

        print(
            "➡ Неизвестная ошибка. "
            "Переходим к следующей модели."
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
    print(
        "❌ Пустой заголовок статьи."
    )
    return None

if not article_text:
    print(
        "❌ Пустой текст статьи."
    )
    return None

client = get_client()

print(
    f"🔄 Доступно моделей: "
    f"{len(MODELS)}"
)

for model_index, model in enumerate(
    MODELS,
    start=1,
):

    print()
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        f"🔹 Модель "
        f"{model_index}/"
        f"{len(MODELS)}: "
        f"{model}"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    post = generate_with_model(
        client=client,
        model=model,
        article_title=article_title,
        article_text=article_text,
    )

    if post:

        print(
            f"✅ Пост успешно создан "
            f"через {model}"
        )

        return post

    print(
        f"⚠ Модель {model} "
        f"не создала пост."
    )

    if model_index < len(MODELS):

        print(
            "➡ Переключаемся "
            "на следующую модель..."
        )

        time.sleep(3)

print()

print(
    "❌ Все доступные модели "
    "не смогли создать пост."
)

return None
```

if **name** == "**main**":

```
print(
    "Проверка конфигурации "
    "AI Generator"
)

if check_configuration():

    print(
        "✓ OPENROUTER_API_KEY найден."
    )

    print(
        "✓ Доступные модели:"
    )

    for model in MODELS:
        print(
            f"  - {model}"
        )

else:

    print(
        "❌ OPENROUTER_API_KEY отсутствует."
    )
