import os
import re
import time

from openai import OpenAI


# ============================================================
# CONFIG
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "qwen/qwen3.8-27b:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1"

MAX_RETRIES = 2
RETRY_DELAY = 5

MIN_POST_LENGTH = 300
MAX_ARTICLE_LENGTH = 18000


# ============================================================
# CLIENT
# ============================================================

client = None

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
Ты — профессиональный редактор русскоязычного Telegram-канала
«КРАЙ РЕАЛЬНОСТИ» о космосе, астрономии и необычных научных открытиях.

Твоя задача — превратить предоставленную научную статью
в интересный готовый пост для Telegram.

СТРОГО СОБЛЮДАЙ ПРАВИЛА:

1. Пиши только на русском языке.

2. Не показывай рассуждения, внутренний анализ,
цепочку мыслей или процесс генерации.

3. Не используй служебные фразы:
«Вот готовый пост»,
«Готовый Telegram-пост»,
«Давайте разберём»,
«Я проанализировал»,
«Моя задача»,
«Финальный вариант»,
«Reasoning»,
«Thinking»,
«Analysis»,
«Step by step».

4. Не придумывай факты, цифры, даты, названия объектов,
результаты исследований или выводы, которых нет в статье.

5. Если статья описывает гипотезу, предположение или возможное
объяснение — сохраняй эту неопределённость.

6. Не превращай гипотезу в доказанный факт.

7. Не используй сенсационные утверждения,
если статья их не подтверждает.

8. Не добавляй ссылки.

9. Не добавляй список источников.

10. Не добавляй хэштеги.

11. Не добавляй рекламу.

12. Начни с короткого интересного заголовка.

13. После заголовка сделай 4–6 содержательных абзацев.

14. Используй конкретные факты из статьи.

15. Не повторяй одну и ту же мысль несколько раз.

16. Не начинай с банальной фразы:
«Учёные сделали новое открытие в космосе».

17. Если материал необычный, объясни,
что именно делает его необычным.

18. Не добавляй информацию из собственных знаний,
если её нет в предоставленной статье.

19. Если речь идёт о чёрной дыре, не переводи
"black hole hair" буквально как «волосы чёрной дыры».

20. Верни только готовый текст Telegram-поста.
"""


# ============================================================
# BAD PATTERNS
# ============================================================

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
]


# ============================================================
# CONFIG CHECK
# ============================================================

def check_configuration():
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY не найден.")
        print("   Проверь GitHub Secrets.")
        return False

    if client is None:
        print("❌ OpenRouter client не создан.")
        return False

    return True


# ============================================================
# ERROR TEXT
# ============================================================

def get_error_text(error):
    try:
        return str(error).lower()
    except Exception:
        return repr(error).lower()


# ============================================================
# DAILY FREE LIMIT
# ============================================================

def is_daily_free_limit_error(error):
    """
    Определяет именно дневной лимит бесплатных моделей OpenRouter.

    Если этот лимит достигнут, повторять запрос бессмысленно.
    """

    error_text = get_error_text(error)

    patterns = [
        "free-models-per-day",
        "free models per day",
        "free-models",
        "daily free",
        "daily limit",
        "free tier daily",
        "limit_source: openrouter_free_tier_daily",
        "openrouter_free_tier_daily",
        "add 10 credits to unlock",
    ]

    for pattern in patterns:
        if pattern in error_text:
            return True

    return False


# ============================================================
# NORMAL 429
# ============================================================

def is_rate_limit_error(error):
    """
    Определяет временный HTTP 429.

    Дневной free-limit здесь исключается.
    """

    if is_daily_free_limit_error(error):
        return False

    error_text = get_error_text(error)

    patterns = [
        "429",
        "rate limit",
        "too many requests",
    ]

    for pattern in patterns:
        if pattern in error_text:
            return True

    return False


# ============================================================
# TEMPORARY ERRORS
# ============================================================

def is_temporary_error(error):
    error_text = get_error_text(error)

    patterns = [
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

    for pattern in patterns:
        if pattern in error_text:
            return True

    return False


# ============================================================
# CLEAN POST
# ============================================================

def clean_post(text):
    if not text:
        return ""

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


# ============================================================
# VALIDATE POST
# ============================================================

def validate_post(text):
    if not text:
        return False, "пустой ответ"

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


# ============================================================
# EXTRACT RESPONSE
# ============================================================

def extract_response_text(response):
    try:
        message = response.choices[0].message

        content = getattr(
            message,
            "content",
            None,
        )

        if isinstance(content, str):
            return content.strip()

        if content is None:
            return ""

        return str(content).strip()

    except Exception as error:
        print("⚠ Не удалось извлечь ответ модели:")
        print(f"   {error}")
        return ""


# ============================================================
# GENERATE POST
# ============================================================

def generate_post(
    title,
    article_text,
    source="",
):
    """
    Генерирует готовый Telegram-пост.

    Возвращает:
        готовый текст поста
        или пустую строку при ошибке
    """

    if not check_configuration():
        return ""

    if not title:
        print("❌ Пустой заголовок статьи.")
        return ""

    if not article_text:
        print(
            f"❌ Пустой текст статьи: {title}"
        )
        return ""

    article_text = article_text.strip()

    if len(article_text) > MAX_ARTICLE_LENGTH:
        article_text = article_text[:MAX_ARTICLE_LENGTH]

        print(
            f"ℹ Статья обрезана до "
            f"{MAX_ARTICLE_LENGTH} символов."
        )

    user_prompt = f"""
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

    total_attempts = MAX_RETRIES + 1

    for attempt in range(1, total_attempts + 1):

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

            # ------------------------------------------------
            # DAILY FREE LIMIT
            # ------------------------------------------------

            if is_daily_free_limit_error(error):

                print()
                print(
                    "🛑 OPENROUTER: ДОСТИГНУТ "
                    "ДНЕВНОЙ ЛИМИТ БЕСПЛАТНЫХ МОДЕЛЕЙ."
                )
                print(
                    "🚫 Повторные запросы НЕ выполняются."
                )
                print(
                    "⏳ Нужно дождаться сброса лимита."
                )
                print()

                return ""

            # ------------------------------------------------
            # TEMPORARY 429
            # ------------------------------------------------

            if is_rate_limit_error(error):

                if attempt >= total_attempts:
                    print(
                        "❌ Временный HTTP 429 "
                        "не исчез после повторов."
                    )
                    return ""

                print(
                    "⚠ Получен временный HTTP 429."
                )

                print(
                    f"⏳ Повтор через "
                    f"{RETRY_DELAY} секунд."
                )

                time.sleep(RETRY_DELAY)

                continue

            # ------------------------------------------------
            # 502 / 503 / 504 / TIMEOUT
            # ------------------------------------------------

            if is_temporary_error(error):

                if attempt >= total_attempts:
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
                    f"⏳ Повтор через "
                    f"{RETRY_DELAY} секунд."
                )

                time.sleep(RETRY_DELAY)

                continue

            # ------------------------------------------------
            # OTHER ERROR
            # ------------------------------------------------

            print(
                "❌ Ошибка OpenRouter:"
            )

            print(
                f"   {error}"
            )

            return ""

        # ----------------------------------------------------
        # EXTRACT RESPONSE
        # ----------------------------------------------------

        post = extract_response_text(response)

        if not post:

            print(
                "⚠ Модель вернула пустой ответ."
            )

            if attempt < total_attempts:

                print(
                    f"⏳ Повтор через "
                    f"{RETRY_DELAY} секунд."
                )

                time.sleep(RETRY_DELAY)

                continue

            return ""

        # ----------------------------------------------------
        # CLEAN
        # ----------------------------------------------------

        post = clean_post(post)

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

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

        if attempt < total_attempts:

            print(
                f"⏳ Повтор генерации через "
                f"{RETRY_DELAY} секунд."
            )

            time.sleep(RETRY_DELAY)

            continue

        print(
            "❌ Не удалось получить "
            "корректный пост."
        )

        return ""

    return ""
