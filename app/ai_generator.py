import os
import re
import time
from typing import Optional

from openai import OpenAI


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "qwen/qwen3.8-27b:free"

OPENROUTER_URL = "https://openrouter.ai/api/v1"

MAX_RETRIES = 2

RETRY_DELAYS = [
    5,
    15,
]

MIN_POST_LENGTH = 300
MAX_ARTICLE_LENGTH = 18000


client: Optional[OpenAI] = None


# ============================================================
# КЛИЕНТ OPENROUTER
# ============================================================

if OPENROUTER_API_KEY:

    client = OpenAI(
        base_url=OPENROUTER_URL,
        api_key=OPENROUTER_API_KEY,
        timeout=60.0,
        max_retries=0,
    )


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
Ты — редактор Telegram-канала «КРАЙ РЕАЛЬНОСТИ».

Тематика канала:
космос, Вселенная, планеты, чёрные дыры,
экзопланеты, астероиды, космические миссии,
телескопы, загадочные космические явления,
поиск внеземной жизни и необычные открытия.

Твоя задача — превращать научные статьи
в интересные оригинальные Telegram-посты
на русском языке.

ТРЕБОВАНИЯ:

1. Пиши только на русском языке.

2. Не копируй статью дословно.

3. Не придумывай факты.

4. Не добавляй информацию, которой нет
   в исходной статье, если она не является
   очевидным научным контекстом.

5. Заголовок должен вызывать интерес,
   но не быть кликбейтом без основания.

6. Текст должен быть понятен обычному человеку,
   даже если исходная статья научная.

7. Используй короткие абзацы.

8. Важные факты выделяй визуально умеренно.

9. Не начинай пост с:
   «Учёные сделали открытие»,
   если можно написать интереснее.

10. Не используй фразы:
    «Это невероятно!»
    «Учёные в шоке!»
    «Вы не поверите!»

11. Если в статье есть числа, даты,
    расстояния, температуры или другие
    конкретные данные — сохраняй их точно.

12. Если информация предварительная,
    спорная или основана на модели,
    обязательно укажи это.

13. В конце добавь короткий вопрос
    или мысль для обсуждения.

14. Заверши пост:

🚀 Подписывайтесь на «КРАЙ РЕАЛЬНОСТИ»,
чтобы не пропустить новые открытия Вселенной.

Формат:

ЗАГОЛОВОК

Основной текст.

Финальная мысль / вопрос.

🚀 Подписывайтесь на «КРАЙ РЕАЛЬНОСТИ»,
чтобы не пропустить новые открытия Вселенной.
"""


# ============================================================
# ПЛОХИЕ ФРАЗЫ
# ============================================================

BAD_PATTERNS = [
    "как искусственный интеллект",
    "я не могу",
    "я не способен",
    "вот пост",
    "конечно, вот",
    "в качестве ии",
    "как ии",
]


# ============================================================
# ПРОВЕРКА КОНФИГУРАЦИИ
# ============================================================

def check_configuration() -> bool:

    if not OPENROUTER_API_KEY:
        print(
            "❌ OPENROUTER_API_KEY не найден."
        )
        return False

    if client is None:
        print(
            "❌ OpenRouter client не создан."
        )
        return False

    return True


# ============================================================
# ТЕКСТ ОШИБКИ
# ============================================================

def get_error_text(error: Exception) -> str:

    try:
        return str(error)
    except Exception:
        return repr(error)


# ============================================================
# ПРОВЕРКА DAILY LIMIT
# ============================================================

def is_daily_free_limit_error(
    error: Exception,
) -> bool:

    text = get_error_text(error).lower()

    patterns = [
        "free-models-per-day",
        "free model requests per day",
        "openrouter_free_tier_daily",
        "daily free limit",
        "limit_source: openrouter_free_tier_daily",
        "add 10 credits",
    ]

    return any(
        pattern in text
        for pattern in patterns
    )


# ============================================================
# ПРОВЕРКА 429
# ============================================================

def is_rate_limit_error(
    error: Exception,
) -> bool:

    text = get_error_text(error).lower()

    return (
        "429" in text
        or "rate limit" in text
        or "too many requests" in text
        or "temporarily unavailable" in text
    )


# ============================================================
# ВРЕМЕННАЯ ОШИБКА
# ============================================================

def is_temporary_error(
    error: Exception,
) -> bool:

    text = get_error_text(error).lower()

    temporary_patterns = [
        "429",
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "connection reset",
        "connection aborted",
        "upstream",
    ]

    return any(
        pattern in text
        for pattern in temporary_patterns
    )


# ============================================================
# RETRY-AFTER
# ============================================================

def get_retry_after(
    error: Exception,
) -> Optional[int]:

    try:

        response = getattr(
            error,
            "response",
            None,
        )

        if response is None:
            return None

        headers = getattr(
            response,
            "headers",
            {},
        ) or {}

        value = (
            headers.get("retry-after")
            or headers.get("Retry-After")
        )

        if not value:
            return None

        seconds = int(float(value))

        return max(
            1,
            min(seconds, 60),
        )

    except Exception:
        return None


# ============================================================
# ОЧИСТКА ПОСТА
# ============================================================

def clean_post(text: str) -> str:

    if not text:
        return ""

    text = text.strip()

    # Убираем Markdown fences
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

    # Убираем служебные фразы
    for pattern in BAD_PATTERNS:
        text = re.sub(
            re.escape(pattern),
            "",
            text,
            flags=re.IGNORECASE,
        )

    # Убираем слишком много пустых строк
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# ПРОВЕРКА ПОСТА
# ============================================================

def validate_post(
    text: str,
) -> bool:

    if not text:
        return False

    if len(text) < MIN_POST_LENGTH:
        print(
            f"⚠ Пост слишком короткий: "
            f"{len(text)} символов"
        )
        return False

    if len(text) > 5000:
        print(
            f"⚠ Пост слишком длинный: "
            f"{len(text)} символов"
        )
        return False

    lower_text = text.lower()

    for pattern in BAD_PATTERNS:

        if pattern in lower_text:

            print(
                f"⚠ Найдена запрещённая фраза: "
                f"{pattern}"
            )

            return False

    return True


# ============================================================
# ИЗВЛЕЧЕНИЕ ТЕКСТА ИЗ RESPONSE
# ============================================================

def extract_response_text(
    response,
) -> str:

    try:

        choices = getattr(
            response,
            "choices",
            None,
        )

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
            return content.strip()

        return str(content).strip()

    except Exception as error:

        print(
            "⚠ Ошибка извлечения ответа: "
            f"{error}"
        )

        return ""


# ============================================================
# ГЕНЕРАЦИЯ ПОСТА
# ============================================================

def generate_post(
    title: str,
    article_text: str,
    source: str = "",
) -> str:

    if not check_configuration():
        return ""

    if not article_text:
        print(
            "⚠ Текст статьи пустой."
        )
        return ""

    article_text = article_text[
        :MAX_ARTICLE_LENGTH
    ]

    user_prompt = f"""
Создай оригинальный Telegram-пост
для канала «КРАЙ РЕАЛЬНОСТИ».

Источник: {source}

Заголовок исходной статьи:
{title}

Текст статьи:
{article_text}

Не упоминай, что ты ИИ.
Не пиши служебных комментариев.
Верни сразу готовый пост.
"""

    total_attempts = MAX_RETRIES + 1

    for attempt in range(
        1,
        total_attempts + 1,
    ):

        print(
            f"🤖 Генерация поста: "
            f"попытка {attempt}/{total_attempts}"
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

                temperature=0.7,

                max_tokens=1800,

                extra_body={
                    "reasoning": {
                        "enabled": False,
                        "exclude": True,
                    }
                },
            )

            post = extract_response_text(
                response
            )

            post = clean_post(post)

            if not post:
                print(
                    "⚠ Модель вернула пустой ответ."
                )

                if attempt < total_attempts:
                    wait_time = RETRY_DELAYS[
                        min(
                            attempt - 1,
                            len(RETRY_DELAYS) - 1,
                        )
                    ]

                    print(
                        f"⏳ Повтор через "
                        f"{wait_time} секунд."
                    )

                    time.sleep(wait_time)
                    continue

                return ""

            if not validate_post(post):

                if attempt < total_attempts:

                    wait_time = RETRY_DELAYS[
                        min(
                            attempt - 1,
                            len(RETRY_DELAYS) - 1,
                        )
                    ]

                    print(
                        f"⏳ Повтор через "
                        f"{wait_time} секунд."
                    )

                    time.sleep(wait_time)
                    continue

                return ""

            print(
                f"✅ Пост успешно создан: "
                f"{len(post)} символов"
            )

            return post

        except Exception as error:

            error_text = get_error_text(
                error
            )

            # ------------------------------------------------
            # DAILY LIMIT
            # ------------------------------------------------

            if is_daily_free_limit_error(error):

                print(
                    "❌ Достигнут дневной лимит "
                    "бесплатных моделей OpenRouter."
                )

                print(
                    "ℹ Повторять запросы сейчас "
                    "бессмысленно."
                )

                return ""

            # ------------------------------------------------
            # RATE LIMIT 429
            # ------------------------------------------------

            if is_rate_limit_error(error):

                print(
                    "⚠ Получен временный HTTP 429."
                )

                if attempt >= total_attempts:

                    print(
                        "❌ 429 не исчез после "
                        "повторных попыток."
                    )

                    return ""

                retry_after = get_retry_after(
                    error
                )

                if retry_after is not None:

                    wait_time = retry_after

                    print(
                        f"⏳ OpenRouter рекомендует "
                        f"подождать {wait_time} сек."
                    )

                else:

                    wait_time = RETRY_DELAYS[
                        min(
                            attempt - 1,
                            len(RETRY_DELAYS) - 1,
                        )
                    ]

                    print(
                        f"⏳ Повтор через "
                        f"{wait_time} секунд."
                    )

                time.sleep(wait_time)

                continue

            # ------------------------------------------------
            # ДРУГИЕ ВРЕМЕННЫЕ ОШИБКИ
            # ------------------------------------------------

            if is_temporary_error(error):

                print(
                    "⚠ Временная ошибка:"
                )

                print(
                    f"  {error_text[:500]}"
                )

                if attempt >= total_attempts:

                    print(
                        "❌ Временная ошибка "
                        "не исчезла."
                    )

                    return ""

                wait_time = RETRY_DELAYS[
                    min(
                        attempt - 1,
                        len(RETRY_DELAYS) - 1,
                    )
                ]

                print(
                    f"⏳ Повтор через "
                    f"{wait_time} секунд."
                )

                time.sleep(wait_time)

                continue

            # ------------------------------------------------
            # НЕИЗВЕСТНАЯ ОШИБКА
            # ------------------------------------------------

            print(
                "❌ Ошибка OpenRouter:"
            )

            print(
                error_text[:1000]
            )

            return ""

    return ""
