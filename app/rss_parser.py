```python
import re
import feedparser
from typing import List, Dict, Optional

from app.database import article_exists


# ============================================================
# КЛЮЧЕВЫЕ СЛОВА КОСМОСА
# ============================================================

SPACE_KEYWORDS = [
    # Общий космос
    "space",
    "outer space",
    "cosmos",
    "cosmic",
    "universe",
    "astronomy",
    "astronomical",
    "astrophysics",
    "astrophysical",

    # Планеты
    "planet",
    "planets",
    "protoplanet",
    "protoplanetary",
    "exoplanet",
    "exoplanets",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "mercury",
    "venus",
    "earth",

    # Луна
    "moon",
    "lunar",
    "lunar eclipse",
    "lunar occultation",

    # Солнце
    "sun",
    "solar",
    "solar flare",
    "solar storm",
    "coronal mass ejection",
    "cme",
    "sunspot",

    # Звёзды
    "star",
    "stars",
    "stellar",
    "supernova",
    "neutron star",
    "white dwarf",
    "red giant",
    "stellar explosion",

    # Чёрные дыры
    "black hole",
    "black holes",
    "event horizon",
    "accretion disk",
    "supermassive black hole",

    # Галактики
    "galaxy",
    "galaxies",
    "milky way",
    "andromeda",

    # Космические объекты
    "asteroid",
    "asteroids",
    "comet",
    "comets",
    "meteor",
    "meteors",
    "meteorite",
    "meteorites",
    "nebula",
    "nebulae",
    "quasar",
    "quasars",
    "pulsar",
    "pulsars",

    # Космические аппараты
    "spacecraft",
    "space probe",
    "rover",
    "rovers",
    "satellite",
    "satellites",
    "telescope",
    "telescopes",
    "jwst",
    "james webb",
    "hubble",

    # Космонавтика
    "astronaut",
    "astronauts",
    "cosmonaut",
    "cosmonauts",
    "space station",
    "iss",
    "international space station",
    "rocket",
    "rockets",
    "launch",
    "space launch",

    # Космические миссии / организации
    "nasa",
    "esa",
    "spacex",
    "artemis",
    "space mission",
    "mission",

    # Космическая физика
    "gravitational wave",
    "gravitational waves",
    "dark matter",
    "dark energy",
    "cosmic radiation",
    "cosmic ray",
    "cosmic rays",
    "cosmic microwave background",
    "microwave background",
    "ancient light",
    "early universe",

    # Поиск жизни
    "alien",
    "aliens",
    "extraterrestrial",
    "extraterrestrials",
    "life on mars",
    "life beyond earth",
    "habitable",
    "habitable planet",
    "biosignature",
    "biosignatures",
    "technosignature",

    # Другие астрономические понятия
    "light-year",
    "light years",
    "light-year",
    "orbit",
    "orbital",
    "constellation",
    "eclipse",
    "occultation",
    "tidal locking",
    "tidally locked",
]


# ============================================================
# ОСОБО ИНТЕРЕСНЫЕ ТЕМЫ
# ============================================================

HIGH_INTEREST_KEYWORDS = [
    "black hole",
    "black holes",
    "supernova",
    "neutron star",
    "exoplanet",
    "exoplanets",
    "protoplanet",
    "alien",
    "aliens",
    "extraterrestrial",
    "life on mars",
    "habitable planet",
    "gravitational wave",
    "gravitational waves",
    "dark matter",
    "dark energy",
    "asteroid",
    "asteroids",
    "comet",
    "comets",
    "solar storm",
    "solar flare",
    "coronal mass ejection",
    "james webb",
    "jwst",
    "hubble",
    "supermassive black hole",
    "early universe",
    "ancient light",
    "cosmic microwave background",
    "lunar occultation",
    "eclipse",
]


# ============================================================
# ИСКЛЮЧЕНИЯ
#
# ВАЖНО:
# Эти слова теперь НЕ используются одинаково
# для title и description.
#
# Сильное исключение в TITLE = статья отклоняется.
# Исключение только в DESCRIPTION = статья не
# отклоняется автоматически.
# ============================================================

STRONG_TITLE_EXCLUSIONS = [
    "fusion reactor",
    "fusion plasma",
    "nuclear reactor",
    "nuclear power plant",
    "tokamak",
    "stellarator",
    "plasma reactor",
    "reactor experiment",
]


# Обычные нежелательные темы.
# Они учитываются только как небольшой штраф.
DESCRIPTION_EXCLUSIONS = [
    "dementia",
    "diabetes",
    "cancer",
    "heart disease",
    "obesity",
    "glucose",
    "metabolism",
    "drug",
    "drugs",
    "medicine",
    "medical",
    "hospital",
    "patient",
    "disease",
    "human brain",
    "mini-brains",
    "primate communication",
    "psychology",
    "eating alone",
    "food",
    "diet",
    "nutrition",
    "smartphone",
    "iphone",
    "android",
    "computer",
    "laptop",
    "politics",
    "election",
    "business",
    "advertisement",
    "shopping",
    "product review",
]


# ============================================================
# ПОИСК КЛЮЧЕВОГО СЛОВА
# ============================================================

def keyword_in_text(
    keyword: str,
    text: str,
) -> bool:

    keyword = keyword.lower().strip()
    text = text.lower()

    if not keyword:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(keyword)
        + r"(?![a-z0-9])"
    )

    return re.search(pattern, text) is not None


# ============================================================
# НАЙТИ СОВПАДЕНИЯ
# ============================================================

def find_keywords(
    keywords: List[str],
    text: str,
) -> List[str]:

    return [
        keyword
        for keyword in keywords
        if keyword_in_text(keyword, text)
    ]


# ============================================================
# ОЦЕНКА ЗАГОЛОВКА
#
# ЗАГОЛОВОК ИМЕЕТ ОСНОВНОЙ ВЕС
# ============================================================

def calculate_title_score(
    title: str,
) -> int:

    score = 0

    matched_space = find_keywords(
        SPACE_KEYWORDS,
        title,
    )

    matched_high = find_keywords(
        HIGH_INTEREST_KEYWORDS,
        title,
    )

    # Каждое космическое слово в заголовке
    # имеет хороший вес.
    score += len(matched_space) * 3

    # Сильные темы получают дополнительный вес.
    score += len(matched_high) * 5

    return score


# ============================================================
# ОЦЕНКА ОПИСАНИЯ
#
# DESCRIPTION — ТОЛЬКО ДОПОЛНИТЕЛЬНЫЙ СИГНАЛ
# ============================================================

def calculate_description_score(
    summary: str,
) -> int:

    if not summary:
        return 0

    matched_space = find_keywords(
        SPACE_KEYWORDS,
        summary,
    )

    matched_high = find_keywords(
        HIGH_INTEREST_KEYWORDS,
        summary,
    )

    matched_exclusions = find_keywords(
        DESCRIPTION_EXCLUSIONS,
        summary,
    )

    # Космические слова в описании имеют
    # значительно меньший вес.
    score = len(matched_space)

    # Сильная космическая тема немного повышает рейтинг.
    score += len(matched_high) * 2

    # Обычные медицинские/земные слова дают
    # небольшой штраф, но НЕ убивают статью.
    score -= len(matched_exclusions)

    return score


# ============================================================
# ОБЩАЯ ОЦЕНКА
# ============================================================

def calculate_relevance_score(
    title: str,
    summary: str = "",
) -> int:

    title_score = calculate_title_score(
        title
    )

    description_score = calculate_description_score(
        summary
    )

    return title_score + description_score


# ============================================================
# ПРОВЕРКА КОСМИЧЕСКОЙ НОВОСТИ
# ============================================================

def is_space_article(
    title: str,
    summary: str = "",
) -> bool:

    title = title.strip()
    summary = summary.strip()

    # --------------------------------------------------------
    # 1. СНАЧАЛА ПРОВЕРЯЕМ ЗАГОЛОВОК
    # --------------------------------------------------------

    title_space = find_keywords(
        SPACE_KEYWORDS,
        title,
    )

    title_high = find_keywords(
        HIGH_INTEREST_KEYWORDS,
        title,
    )

    title_exclusions = find_keywords(
        STRONG_TITLE_EXCLUSIONS,
        title,
    )

    title_score = calculate_title_score(
        title
    )

    # --------------------------------------------------------
    # 2. СИЛЬНОЕ ИСКЛЮЧЕНИЕ В САМОМ ЗАГОЛОВКЕ
    #
    # Например:
    # "Fusion Reactor..."
    #
    # Такое отклоняем сразу.
    # --------------------------------------------------------

    if title_exclusions:

        print(
            f"      ❌ Исключение в заголовке: "
            f"{title_exclusions}"
        )

        return False

    # --------------------------------------------------------
    # 3. ЕСЛИ ЗАГОЛОВОК ЯВНО КОСМИЧЕСКИЙ
    #
    # Описание больше не может его случайно убить.
    # --------------------------------------------------------

    if title_high:

        print(
            f"      ✓ Космический заголовок: "
            f"score={title_score}, "
            f"keywords={title_space}"
        )

        return True

    if title_space:

        print(
            f"      ✓ Космос в заголовке: "
            f"score={title_score}, "
            f"keywords={title_space}"
        )

        return True

    # --------------------------------------------------------
    # 4. ЕСЛИ В ЗАГОЛОВКЕ НЕТ КОСМОСА,
    # СМОТРИМ ОПИСАНИЕ.
    #
    # Но здесь требования строже.
    # --------------------------------------------------------

    description_space = find_keywords(
        SPACE_KEYWORDS,
        summary,
    )

    description_high = find_keywords(
        HIGH_INTEREST_KEYWORDS,
        summary,
    )

    description_exclusions = find_keywords(
        DESCRIPTION_EXCLUSIONS,
        summary,
    )

    description_score = calculate_description_score(
        summary
    )

    # Если в описании есть сильная космическая тема,
    # допускаем статью.
    if description_high:

        print(
            f"      ✓ Космический контекст "
            f"в описании: "
            f"score={description_score}, "
            f"keywords={description_high}"
        )

        return True

    # Несколько обычных космических слов
    # тоже могут подтвердить статью.
    if len(description_space) >= 2:

        print(
            f"      ✓ Космос найден в описании: "
            f"score={description_score}, "
            f"keywords={description_space[:8]}"
        )

        return True

    # Иначе отклоняем.
    return False


# ============================================================
# PARSE RSS
# ============================================================

def parse_feed(
    source: str,
    url: str,
) -> List[Dict]:

    print()
    print("=" * 70)
    print(f"🛰️ Источник: {source}")
    print("=" * 70)

    try:

        feed = feedparser.parse(
            url
        )

    except Exception as error:

        print(
            f"❌ Ошибка RSS: {error}"
        )

        return []

    if getattr(
        feed,
        "bozo",
        False,
    ):

        print(
            "⚠ RSS вернул предупреждение."
        )

    entries = getattr(
        feed,
        "entries",
        [],
    )

    if not entries:

        print(
            "⚠ Новостей не найдено."
        )

        return []

    results = []

    for entry in entries[:20]:

        title = (
            entry.get(
                "title",
                "",
            )
            .strip()
        )

        link = (
            entry.get(
                "link",
                "",
            )
            .strip()
        )

        summary = (
            entry.get(
                "summary"
            )
            or entry.get(
                "description"
            )
            or ""
        )

        published = (
            entry.get(
                "published"
            )
            or entry.get(
                "updated"
            )
            or ""
        )

        if not title or not link:
            continue

        # ----------------------------------------------------
        # Проверяем БД
        # ----------------------------------------------------

        if article_exists(link):

            print(
                f"  ⏭ Уже есть: {title}"
            )

            continue

        # ----------------------------------------------------
        # Считаем рейтинг
        # ----------------------------------------------------

        score = calculate_relevance_score(
            title,
            summary,
        )

        print()
        print(
            f"  📰 {title}"
        )

        print(
            f"     score={score}"
        )

        # ----------------------------------------------------
        # Проверяем релевантность
        # ----------------------------------------------------

        if not is_space_article(
            title,
            summary,
        ):

            print(
                "     ❌ Отклонено"
            )

            continue

        print(
            "     ✅ Принято"
        )

        results.append(
            {
                "source": source,
                "title": title,
                "url": link,
                "published": published,
                "summary": summary,
                "score": score,
            }
        )

        if len(results) >= 5:
            break

    print()
    print(
        f"📊 Принято: {len(results)}"
    )

    return results


# ============================================================
# СБОР НОВОСТЕЙ
# ============================================================

def collect_news(
    feeds: Optional[Dict[str, str]] = None,
    max_articles_per_source: int = 5,
) -> List[Dict]:

    if feeds is None:

        from app.config import RSS_FEEDS

        feeds = RSS_FEEDS

    all_articles = []

    for source, url in feeds.items():

        articles = parse_feed(
            source,
            url,
        )

        articles = articles[
            :max_articles_per_source
        ]

        all_articles.extend(
            articles
        )

    # --------------------------------------------------------
    # Сортировка по интересности
    # --------------------------------------------------------

    all_articles.sort(
        key=lambda article: article.get(
            "score",
            0,
        ),
        reverse=True,
    )

    print()
    print("=" * 70)
    print(
        "🏆 ИТОГОВЫЙ РЕЙТИНГ НОВОСТЕЙ"
    )
    print("=" * 70)

    for index, article in enumerate(
        all_articles,
        start=1,
    ):

        print(
            f"{index}. "
            f"[{article['score']}] "
            f"{article['title']}"
        )

    return all_articles


# ============================================================
# ТЕСТ
# ============================================================

if __name__ == "__main__":

    from app.config import RSS_FEEDS

    articles = collect_news(
        RSS_FEEDS,
        max_articles_per_source=5,
    )

    print()
    print(
        f"Всего найдено: {len(articles)}"
    )
```
