import os
import re
import time

from openai import OpenAI


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError("Не найден секрет OPENROUTER_API_KEY")


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
]

TEMPERATURE = 0.2

def extract_response_text(response) -> str:
    """
    Безопасно извлекает текст из ответа OpenRouter.
    """

    try:
        choices = getattr(response, "choices", None)

        if not choices:
            print("⚠ OpenRouter вернул ответ без choices.")
            return ""

        choice = choices[0]

        if choice is None:
            print("⚠ OpenRouter вернул пустой choice.")
            return ""

        message = getattr(choice, "message", None)

        if message is None:
            print("⚠ OpenRouter вернул пустой message.")
            return ""

        content = getattr(message, "content", None)

        if content:
            return str(content).strip()

        # Некоторые reasoning-модели могут вернуть текст
        # в другом поле.
        reasoning = getattr(message, "reasoning", None)

        if reasoning:
            print(
                "⚠ Модель вернула reasoning вместо обычного текста."
            )

        print(
            "⚠ В ответе OpenRouter отсутствует текст content."
        )

        return ""

    except Exception as error:
        print(
            f"⚠ Ошибка извлечения ответа OpenRouter: {error}"
        )
        return ""

SYSTEM_PROMPT = """
Ты — профессиональный научный редактор Telegram-канала
«КРАЙ РЕАЛЬНОСТИ».

Твоя задача — превращать англоязычные научные статьи о космосе
в качественные русскоязычные Telegram-посты.

ГЛАВНОЕ ПРАВИЛО:

НЕЛЬЗЯ ПРИДУМЫВАТЬ НИ ОДНОГО ФАКТА.

Используй только информацию, которая есть в переданном тексте статьи.

Если в статье говорится о гипотезе, модели, предположении,
возможном сценарии или теоретическом механизме —
обязательно сохраняй эту неопределённость.

Не превращай:
"could", "may", "might", "suggests", "hypothetical",
"theoretical", "possible"

в утверждение о доказанном факте.

РУССКИЙ ЯЗЫК:

Пиши естественным современным русским языком.

Никакого дословного машинного перевода.

Не используй странные кальки с английского.

Не переводи механически научные термины и метафоры.

Если английское выражение имеет специальное научное значение,
передай его смысл естественным русским языком.

НАУЧНЫЕ ТЕРМИНЫ:

Не придумывай перевод названий организаций,
программ, миссий, лабораторий и проектов.

Если правильный русский вариант официального названия
не очевиден — оставь оригинальное название на английском.

Не превращай научный термин в бытовую метафору.

Особенно внимательно относись к:

black hole hair
boson star
scalar field
event horizon
gravitational waves
compactness
instability
scalar cloud

"black hole hair" нельзя автоматически переводить
как "волосы чёрной дыры" или "борода чёрной дыры".

Сначала определи физический смысл термина,
затем передай этот смысл естественным русским языком.

ЗАПРЕЩЕНО:

Не добавляй:
- новые факты;
- новые цифры;
- новые даты;
- новые имена;
- новые организации;
- новые космические миссии;
- собственные гипотезы;
- ссылки;
- источники;
- хэштеги;
- рекламные призывы.

Не используй случайные английские слова внутри русского текста.

Не используй слова:
"review"
"final review"
"Moon Base"
"habitat"
"landéров"
"Program"
"Challenge"
"Statement"
"Coverage"

если это не часть точного официального названия,
которое необходимо сохранить.

СТРУКТУРА:

Создай пост примерно на 4–6 абзацев.

Первый абзац должен содержать короткий цепляющий заголовок.

Можно использовать 1 подходящий эмодзи.

Заголовок должен отражать реальную тему статьи,
а не придуманную сенсацию.

Далее объясни:

1. Что произошло.
2. Что обнаружили или предложили исследователи.
3. Как это объясняется.
4. Что это может означать.
5. Какие ограничения или неопределённости есть.

Пиши понятно человеку, который интересуется космосом,
но не является профессиональным физиком.

Не преувеличивай значение исследования.

ФОРМАТ:

Верни ТОЛЬКО готовый русский текст поста.

Без:
"Вот пост:"
"Готовый пост:"
служебных комментариев
списка источников
ссылок
хэштегов
"""


BAD_PATTERNS = [
    r"[\u4e00-\u9fff]",
    r"[\u3040-\u30ff]",
    r"[\uac00-\ud7af]",

    r"\bnet[- ]?\w+",
    r"\btoy model\b",
    r"\bprogram\b",
    r"\bchallenge\b",
    r"\breview\b",
    r"\bstatement\b",
    r"\bcoverage\b",

    r"финальн\w*\s+ревью",
    r"финальн\w*\s+обзор",

    r"может выстрелить самой",
    r"выстрелить из своей бороды",
    r"выстрелить из собственной бороды",
    r"выстрелить из собственных волос",

    r"волос\w*\s+чёрной дыры",
    r"волос\w*\s+черной дыры",
    r"бород\w*\s+чёрной дыры",
    r"бород\w*\s+черной дыры",

    r"словно пробка",

    r"landé",
    r"ландé",

    r"склеиваться в облако",
    r"склеивается в облако",
    r"поглощают материи",

    r"стала лысыми",
    r"ставшей лысыми",
    r"ожидают носить",

    r"разрушительная симметрия",
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


def fix_generated_post(
    original_post: str,
    article_text: str,
) -> str:

    prompt = f"""
Ниже находится русский текст научного Telegram-поста.

Он был автоматически переведён с английского и содержит
возможные неестественные или ошибочные формулировки.

Выполни только языковую и терминологическую редактуру.

КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО:

- добавлять новые факты;
- добавлять новые цифры;
- добавлять новые даты;
- добавлять новые имена;
- добавлять новые организации;
- добавлять новые научные выводы;
- менять смысл;
- усиливать утверждения;
- превращать гипотезу в факт.

Исправляй только:

- плохой русский;
- машинные кальки;
- неправильные переводы терминов;
- бессмысленные метафоры;
- случайные английские слова;
- грамматические ошибки;
- очевидные ошибки транслитерации.

Если официальный термин или название невозможно уверенно
перевести на русский — оставь оригинальный английский термин.

Особенно внимательно проверь физические термины.

Не переводи "black hole hair" буквально как
"волосы чёрной дыры" или "борода чёрной дыры".

Сохрани научный смысл термина.

Верни только исправленный текст.

ИСХОДНЫЙ ТЕКСТ СТАТЬИ:

{article_text[:30000]}

ПОСТ ДЛЯ РЕДАКТУРЫ:

{original_post}
"""

    try:
        response = client.chat.completions.create(
            model=MODELS[0],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты профессиональный научный "
                        "редактор русского языка."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_tokens=1800,
        )

        result = response.choices[0].message.content

        if result:
            result = result.strip()

        if result and not has_bad_language(result):
            return result

    except Exception as error:
        print(
            f"⚠ Ошибка при редактуре: {error}"
        )

    return original_post


def generate_with_model(
    model: str,
    title: str,
    article_text: str,
) -> str:

    prompt = f"""
Создай русский Telegram-пост для канала
«КРАЙ РЕАЛЬНОСТИ».

ОРИГИНАЛЬНЫЙ ЗАГОЛОВОК:

{title}

ТЕКСТ СТАТЬИ:

{article_text[:30000]}

Сначала внимательно определи для себя:

1. Что является установленным фактом.
2. Что является гипотезой или теоретической моделью.
3. Что является предположением авторов.
4. Какие ограничения исследования указаны в статье.

После этого напиши готовый пост.

Не показывай этот анализ пользователю.

ОЧЕНЬ ВАЖНО:

Не переводи английские слова буквально,
если буквальный перевод звучит бессмысленно.

Не придумывай русские термины.

Если термин имеет специальное физическое значение,
передай именно его смысл.

Пост должен быть полностью на русском языке,
за исключением необходимых официальных названий.

Не добавляй информацию, которой нет в статье.

Верни только готовый пост.
"""

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
        temperature=TEMPERATURE,
        max_tokens=1800,
    )

    result = extract_response_text(response)

if not result:
    return ""

return result


def generate_post(
    title: str,
    article_text: str,
) -> str:

    last_error = None

    for attempt, model in enumerate(
        MODELS,
        start=1,
    ):
        print()
        print(
            f"AI модель {attempt}/{len(MODELS)}: "
            f"{model}"
        )

        for retry in range(2):

            try:
                post = generate_with_model(
                    model=model,
                    title=title,
                    article_text=article_text,
                )

                if not post:
                    print(
                        "⚠ Модель вернула пустой ответ."
                    )
                    continue

                print(
                    f"✓ Ответ получен от {model}"
                )

                if has_bad_language(post):
                    print(
                        "⚠ Обнаружены подозрительные "
                        "формулировки."
                    )

                    fixed = fix_generated_post(
                        original_post=post,
                        article_text=article_text,
                    )

                    if fixed and not has_bad_language(
                        fixed
                    ):
                        print(
                            "✓ Текст успешно "
                            "отредактирован."
                        )
                        return fixed

                    print(
                        "⚠ Редактура не смогла "
                        "исправить текст."
                    )

                    continue

                return post

            except Exception as error:
                last_error = error

                error_text = str(error)

                print(
                    f"⚠ Ошибка модели: {error_text}"
                )

                if (
                    "429" in error_text
                    or "rate" in error_text.lower()
                    or "temporarily" in error_text.lower()
                ):
                    if retry == 0:
                        print(
                            "⏳ Модель временно "
                            "перегружена. "
                            "Ждём 5 секунд..."
                        )

                        time.sleep(5)
                        continue

                break

    print()
    print(
        "❌ Все AI-модели не смогли создать пост."
    )

    if last_error:
        print(
            f"Последняя ошибка: {last_error}"
        )

    return ""


if __name__ == "__main__":
    print("AI generator loaded successfully.")
