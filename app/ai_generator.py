import os

from openai import OpenAI


MODEL = "openrouter/free"

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)


SYSTEM_PROMPT = """
Ты — редактор Telegram-канала «КРАЙ РЕАЛЬНОСТИ».

Тематика канала:
космос, Вселенная, чёрные дыры, планеты, звёзды,
экзопланеты, космические миссии, астероиды,
необычные астрономические открытия и загадочные явления.

Твоя задача — превращать научные новости в интересные
и понятные посты на русском языке.

Правила:

1. Не выдумывай факты.
2. Используй только информацию из переданного текста.
3. Не добавляй неподтверждённые версии как факты.
4. Сохраняй научную точность.
5. Пиши живым человеческим языком.
6. Не начинай пост со слов «Учёные обнаружили».
7. Сделай первый абзац максимально интересным.
8. Не используй чрезмерный кликбейт.
9. Не повторяй одну и ту же мысль разными словами.
10. Используй короткие абзацы, удобные для Telegram.
11. Можно использовать 1–3 подходящих эмодзи.
12. Не добавляй хэштеги.
13. Не добавляй ссылку на источник.
14. В конце добавь короткую мысль или вопрос читателю.

Формат:

ЗАГОЛОВОК

Основной текст поста.

Финальная мысль или вопрос читателю.
"""


def generate_post(
    title: str,
    article_text: str
) -> str:

    if not article_text.strip():
        return ""

    article_text = article_text[:18000]

    prompt = f"""
Название оригинальной статьи:

{title}

Текст статьи:

{article_text}

Создай на основе этой информации готовый пост
для Telegram-канала «КРАЙ РЕАЛЬНОСТИ».
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
        )

        result = response.choices[0].message.content

        if not result:
            return ""

        return result.strip()

    except Exception as error:
        print("⚠ Ошибка OpenRouter API:")
        print(error)
        return ""
