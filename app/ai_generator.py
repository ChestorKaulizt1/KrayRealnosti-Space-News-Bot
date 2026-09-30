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


MODEL = "qwen/qwen3.8-27b:free"


SYSTEM_PROMPT = """
Ты — профессиональный научный редактор Telegram-канала
«КРАЙ РЕАЛЬНОСТИ».

Твоя задача — написать готовый Telegram-пост на русском языке
на основе переданной научной статьи.

КРИТИЧЕСКИ ВАЖНО:

Ответ должен содержать ТОЛЬКО готовый Telegram-пост.

НЕЛЬЗЯ писать:
- анализ задания;
- рассуждения;
- thinking;
- reasoning;
- пояснения о том, как ты создавал текст;
- "Вот готовый пост";
- "Давайте разберём";
- комментарии о своей работе;
- заключительные комментарии от AI.

Начинай сразу с заголовка поста.

ИСПОЛЬЗУЙ ТОЛЬКО ИНФОРМАЦИЮ ИЗ СТАТЬИ.

Нельзя придумывать:
- факты;
- цифры;
- даты;
- имена;
- организации;
- научные результаты;
- выводы.

Если в статье указана гипотеза, теория, предположение
или моделирование — обязательно сохраняй эту неопределённость.

Не превращай гипотезу в доказанный факт.

РУССКИЙ ЯЗЫК:

Пиши естественным современным русским языком.

Не делай дословный машинный перевод.

Не используй английские слова без необходимости.

Не используй странные кальки.

Особенно осторожно обращайся с научными терминами:

black hole hair
boson star
scalar field
event horizon
gravitational waves
compactness
instability
scalar cloud

Не переводи "black hole hair" буквально как
"волосы чёрной дыры".

Передавай смысл понятным русским языком.

СТРУКТУРА:

1. Короткий интересный заголовок.
2. Что произошло.
3. Что обнаружили или предложили исследователи.
4. Как это объясняется.
5. Что это может означать.
6. Какие существуют ограничения и неопределённости.

Объём: примерно 4–6 абзацев.

Пиши для обычного человека, который интересуется космосом,
но не является профессиональным физиком.

Не используй кликбейт.

Не преувеличивай значение исследования.

НЕ ДОБАВЛЯЙ:

- ссылки;
- источники;
- хэштеги;
- рекламу;
- призывы подписаться;
- служебные комментарии;
- фразу "Вот готовый Telegram-пост";
- фразу "Текст составлен на основе статьи".

Верни только готовый пост.
"""


BAD_PATTERNS = [
    r"[\u4e00-\u9fff]",
    r"[\u3040-\u30ff]",
    r"[\uac00-\ud7af]",

    r"финальн\w*\s+ревью",
    r"финальн\w*\s+обзор",

    r"вот готовый",
    r"давайте разбер",
    r"я проанализ",
    r"я должен",
    r"моя задача",
    r"thinking",
    r"reasoning",
    r"step\s*by\s*step",
    r"let me",
    r"i need to",
    r"i will",
    r"final answer",

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
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True

    return False


def clean_post(text: str) -> str:
    if not text:
        return ""

    text = text.strip()

    # Удаляем возможные служебные маркеры
    text = re.sub(
        r"^(Вот готовый Telegram-пост:?\s*)",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^Готовый пост:?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Удаляем markdown-заголовок вида ###
    text = re.sub(r"^#{1,6}\s*", "", text)

    return text.strip()


def extract_response_text(response) -> str:
    try:
        choices = getattr(response, "choices", None)

        if not choices:
            print("⚠ OpenRouter не вернул choices.")
            return ""

        choice = choices[0]

        if choice is None:
            print("⚠ OpenRouter вернул пустой choice.")
            return ""

        message = getattr(choice, "message", None)

        if message is None:
            print("⚠ OpenRouter не вернул message.")
            return ""

        content = getattr(message, "content", None)

        if isinstance(content, str):
            return content.strip()

        if content:
            return str(content).strip()

        print("⚠ Модель не вернула текстовый content.")
        return ""

    except Exception as error:
        print(f"⚠ Ошибка обработки ответа AI: {error}")
        return ""


def generate_post(title: str, article_text: str) -> str:

    prompt = f"""
Создай готовый Telegram-пост на русском языке.

ОРИГИНАЛЬНЫЙ ЗАГОЛОВОК:
{title}

ТЕКСТ НАУЧНОЙ СТАТЬИ:
{article_text[:28000]}

ЕЩЁ РАЗ ПРОВЕРЬ ПЕРЕД ОТВЕТОМ:

- используй только факты из статьи;
- не придумывай факты;
- не придумывай цифры;
- не придумывай имена;
- гипотезы оставляй гипотезами;
- пиши естественным русским языком;
- не используй машинный перевод;
- не добавляй ссылки;
- не добавляй хэштеги;
- не добавляй источники;
- не добавляй комментарии от AI;
- не объясняй процесс написания.

ОТВЕТ ДОЛЖЕН НАЧИНАТЬСЯ С ЗАГОЛОВКА ПОСТА.

Верни только готовый Telegram-пост.
"""

    for attempt in range(1, 4):

        print()
        print(f"Попытка генерации {attempt}/3")

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

                max_tokens=1400,

                extra_body={
                    "reasoning": {
                        "enabled": False,
                        "exclude": True,
                    }
                },
            )

            post = extract_response_text(response)

            if not post:

                print("⚠ Пустой ответ от модели.")

                if attempt < 3:
                    print("⏳ Повторяем через 5 секунд...")
                    time.sleep(5)

                continue

            post = clean_post(post)

            print(f"✓ Ответ получен от {MODEL}")

            if has_bad_language(post):

                print("⚠ Обнаружены подозрительные формулировки.")
                print("⚠ Этот вариант отклонён.")

                if attempt < 3:
                    print("⏳ Повторяем генерацию...")
                    time.sleep(3)

                continue

            # Минимальная проверка длины
            if len(post) < 300:

                print("⚠ Ответ слишком короткий.")
                print("⚠ Этот вариант отклонён.")

                if attempt < 3:
                    print("⏳ Повторяем генерацию...")
                    time.sleep(3)

                continue

            return post

        except Exception as error:

            error_text = str(error)

            print(f"⚠ Ошибка модели: {error_text}")

            if "429" in error_text:
                print("⏳ Модель временно перегружена.")

            if "timeout" in error_text.lower():
                print("⏱ AI-запрос превысил лимит 60 секунд.")

            if attempt < 3:
                print("⏳ Ждём 5 секунд перед повтором...")
                time.sleep(5)

    print()
    print("❌ Не удалось получить корректный пост от AI.")

    return ""


if __name__ == "__main__":
    print("AI generator loaded successfully.")
