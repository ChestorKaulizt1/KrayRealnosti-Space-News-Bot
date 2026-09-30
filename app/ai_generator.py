import os
import re
import time

from openai import OpenAI


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "Не найден секрет OPENROUTER_API_KEY"
    )


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"


SYSTEM_PROMPT = """
Ты — профессиональный научный редактор Telegram-канала
«КРАЙ РЕАЛЬНОСТИ».

Твоя задача — написать качественный русский Telegram-пост
на основе переданной научной статьи о космосе.

СТРОГОЕ ПРАВИЛО:

Используй ТОЛЬКО информацию из статьи.

Нельзя придумывать:
- факты;
- цифры;
- даты;
- имена;
- организации;
- открытия;
- выводы;
- объяснения, которых нет в статье.

Если статья говорит:
"could", "may", "might", "possible",
"suggests", "hypothetical", "theoretical"

обязательно сохраняй неопределённость.

Не превращай гипотезу в установленный факт.

РУССКИЙ ЯЗЫК:

Пиши естественным современным русским языком.

Не делай дословный машинный перевод.

Не используй странные английские кальки.

Не придумывай русские термины.

Если научный термин лучше оставить на английском,
можно оставить оригинальное написание.

Особенно осторожно обращайся с:

black hole hair
boson star
scalar field
event horizon
gravitational waves
compactness
instability
scalar cloud

НЕ переводь "black hole hair" буквально
как "волосы чёрной дыры" или "борода чёрной дыры".

Передай научный смысл простыми русскими словами.

НЕ ИСПОЛЬЗУЙ:

review
final review
coverage
statement
challenge
program
landéров
Moon Base
habitat

если это не часть необходимого официального названия.

Не вставляй случайные английские слова
в русский текст.

СТРУКТУРА:

Напиши примерно 4–6 абзацев.

Первый абзац:

Короткий интересный заголовок.

Можно использовать один подходящий эмодзи.

Затем:

1. Что произошло.
2. Что обнаружили исследователи.
3. Как это объясняется.
4. Что это может означать.
5. Какие существуют ограничения или неопределённости.

Пиши понятно обычному человеку,
который интересуется космосом.

Не преувеличивай значение исследования.

Не используй кликбейт.

НЕ ДОБАВЛЯЙ:

- ссылки;
- источники;
- хэштеги;
- рекламу;
- призывы подписаться;
- комментарии от себя.

Верни ТОЛЬКО готовый текст поста.
"""


BAD_PATTERNS = [
    r"[\u4e00-\u9fff]",
    r"[\u3040-\u30ff]",
    r"[\uac00-\ud7af]",

    r"финальн\w*\s+ревью",
    r"финальн\w*\s+обзор",

    r"волос\w*\s+чёрной дыры",
    r"волос\w*\s+черной дыры",

    r"бород\w*\s+чёрной дыры",
    r"бород\w*\s+черной дыры",

    r"выстрелить из своей бороды",
    r"выстрелить из собственной бороды",
    r"выстрелить из собственных волос",

    r"словно пробка",

    r"landé",
    r"ландé",

    r"склеиваться в облако",
    r"склеивается в облако",

    r"поглощают материи",

    r"стала лысыми",
    r"ставшей лысыми",

    r"ожидают носить",
]


def has_bad_language(text: str) -> bool:
    if not text:
        return True

    for pattern in BAD_PATTERNS:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            return True

    return False


def extract_response_text(response) -> str:
    """
    Безопасно извлекает content из ответа OpenRouter.

    Для reasoning-моделей OpenRouter может отдельно
    передавать reasoning/reasoning_details.
    Нам нужен только итоговый content.
    """

    try:
        choices = getattr(
            response,
            "choices",
            None,
        )

        if not choices:
            print(
                "⚠ OpenRouter не вернул choices."
            )
            return ""

        choice = choices[0]

        if choice is None:
            print(
                "⚠ OpenRouter вернул пустой choice."
            )
            return ""

        message = getattr(
            choice,
            "message",
            None,
        )

        if message is None:
            print(
                "⚠ OpenRouter не вернул message."
            )
            return ""

        content = getattr(
            message,
            "content",
            None,
        )

        if isinstance(content, str):
            return content.strip()

        if content:
            return str(content).strip()

        print(
            "⚠ Модель вернула reasoning, "
            "но итоговый content отсутствует."
        )

        return ""

    except Exception as error:
        print(
            f"⚠ Ошибка обработки ответа AI: {error}"
        )
        return ""


def generate_post(
    title: str,
    article_text: str,
) -> str:

    prompt = f"""
Напиши готовый Telegram-пост на русском языке.

ОРИГИНАЛЬНЫЙ ЗАГОЛОВОК:

{title}

ТЕКСТ НАУЧНОЙ СТАТЬИ:

{article_text[:28000]}

Ещё раз проверь перед ответом:

- все факты должны быть взяты из статьи;
- гипотезы должны оставаться гипотезами;
- не добавляй собственных фактов;
- не придумывай цифры;
- не придумывай названия;
- не используй машинные кальки;
- текст должен быть естественным русским языком;
- не добавляй источники;
- не добавляй ссылки;
- не добавляй хэштеги.

Верни только готовый Telegram-пост.
"""

    for attempt in range(1, 4):

        print()
        print(
            f"Попытка генерации {attempt}/3"
        )

        try:
            response = client.with_options(
    timeout=60.0,
    max_retries=0,
).chat.completions.create(
    model=MODEL,
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
    temperature=0.2,
    max_tokens=1800,
    extra_body={
        "reasoning": {
            "exclude": True
        }
    },
)
                temperature=0.2,
                max_tokens=1800,

                # ВАЖНО:
                # просим модель не возвращать
                # отдельный reasoning вместо ответа.
                extra_body={
                    "reasoning": {
                        "exclude": True
                    }
                },
            )

            post = extract_response_text(
                response
            )

            if not post:
                print(
                    "⚠ Пустой ответ от модели."
                )

                if attempt < 3:
                    print(
                        "⏳ Повторяем через 5 секунд..."
                    )
                    time.sleep(5)

                continue

            print(
                f"✓ Ответ получен от {MODEL}"
            )

            if has_bad_language(post):
                print(
                    "⚠ Обнаружены подозрительные "
                    "формулировки."
                )

                print(
                    "⚠ Этот вариант отклонён."
                )

                if attempt < 3:
                    print(
                        "⏳ Повторяем генерацию..."
                    )
                    time.sleep(3)

                continue

            return post

        except Exception as error:

            error_text = str(error)

            print(
                f"⚠ Ошибка модели: {error_text}"
            )

            if "429" in error_text:
                print(
                    "⏳ Модель временно перегружена."
                )

            if attempt < 3:
                print(
                    "⏳ Ждём 5 секунд "
                    "перед повтором..."
                )
                time.sleep(5)

    print()
    print(
        "❌ Не удалось получить "
        "корректный пост от AI."
    )

    return ""


if __name__ == "__main__":
    print(
        "AI generator loaded successfully."
    )
