import re
import feedparser
from typing import List, Dict

from app.database import article_exists, save_article


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

    # Космические миссии
    "nasa",
    "esa",
    "spacex",
    "artemis",
    "mission",
    "space mission",

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
]


# ============================================================
# СИЛЬНЫЕ КОСМИЧЕСКИЕ ТЕМЫ
# ============================================================

HIGH_INTEREST_KEYWORDS = [
    "black hole",
    "supernova",
    "neutron star",
    "exoplanet",
    "alien",
    "extraterrestrial",
    "life on mars",
    "habitable planet",
    "gravitational wave",
    "gravitational waves",
    "dark matter",
    "dark energy",
    "asteroid",
    "comet",
    "solar storm",
    "solar flare",
    "coronal mass ejection",
    "james webb",
    "jwst",
    "hubble",
    "supermassive",
    "early universe",
    "ancient light",
    "cosmic microwave background",
    "lunar occultation",
]


# ============================================================
# ТОЧНЫЕ ИСКЛЮЧЕНИЯ
# ============================================================

EXCLUDE_KEYWORDS = [
    # Медицина
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

    # Биология / человек
    "human brain",
    "mini-brains",
    "primate",
    "primate communication",
    "human communication",
    "psychology",

    # Еда
    "eating alone",
    "food",
    "diet",
    "nutrition",

    # Явно земные технологии
    "smartphone",
    "iphone",
    "android",
    "computer",
    "laptop",

    # Ядерная / термоядерная энергетика
    "fusion reactor",
    "fusion plasma",
    "nuclear reactor",
    "nuclear power plant",
    "tokamak",
    "stellarator",
    "reactor",

    # Прочая земная физика
    "laboratory experiment",
    "lab experiment",
]


# ============================================================
# НЕЖЕЛАТЕЛЬНЫЕ СЛОВА
# ============================================================

BORING_KEYWORDS = [
    "politics",
    "election",
    "business",
    "advertisement",
    "shopping",
    "product review",
    "phone review",
]


# ============================================================
# ПОИСК СЛОВА БЕЗ ЛОЖНЫХ СОВПАДЕНИЙ
# ============================================================

def keyword_in_text(keyword: str, text: str) -> bool:
    """
    Проверяет ключевое слово как отдельное слово/фразу.

    Например:
    star -> найдёт "star"
    но не найдёт "starting"
    """
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
# ОЦЕНКА РЕЛЕВАНТНОСТИ
# ============================================================

def calculate_relevance_score(
    title: str,
    summary: str = "",
) -> int:

    text = f"{title} {summary}".lower()

    score = 0

    # Сильные темы
    for keyword in HIGH_INTEREST_KEYWORDS:
        if keyword_in_text(keyword, text):
            score += 5

    # Общие космические слова
    for keyword in SPACE_KEYWORDS:
        if keyword_in_text(keyword, text):
            score += 2

    # Исключения
    for keyword in EXCLUDE_KEYWORDS:
        if keyword_in_text(keyword, text):
            score -= 8

    # Скучные темы
    for keyword in BORING_KEYWORDS:
        if keyword_in_text(keyword, text):
            score -= 5

    return score


# ============================================================
# ПРОВЕРКА: КОСМОС ЛИ ЭТО?
# ============================================================

def is_space_article(
    title: str,
    summary: str = "",
) -> bool:

    text = f"{title} {summary}".lower()

    matched_space = [
        keyword
        for keyword in SPACE_KEYWORDS
        if keyword_in_text(keyword, text)
    ]

    matched_exclude = [
        keyword
        for keyword in EXCLUDE_KEYWORDS
        if keyword_in_text(keyword, text)
    ]

    score = calculate_relevance_score(title, summary)

    # --------------------------------------------------------
    # Если найдено явно земное исключение,
    # отбрасываем новость, если одновременно нет
    # сильного космического контекста.
    # --------------------------------------------------------

    if matched_exclude:
        strong_space = any(
            keyword_in_text(keyword, text)
            for keyword in HIGH_INTEREST_KEYWORDS
        )

        # Например:
        # "Fusion Reactor" + "plasma"
        # => не космос
        if not strong_space:
            print(
                f"      ❌ Исключение: {matched_exclude}"
            )
            return False

    # Без единого космического слова новость не принимаем.
    if not matched_space:
        return False

    # Слишком низкий результат
    if score < 2:
        return False

    print(
        f"      ✓ Космос: score={score}, "
        f"keywords={matched_space[:8]}"
    )

    return True


# ============================================================
# ПОЛУЧЕНИЕ RSS
# ============================================================

def parse_feed(source: str, url: str) -> List[Dict]:

    print()
    print("=" * 70)
    print(f"🛰️ Источник: {source}")
    print("=" * 70)

    try:
        feed = feedparser.parse(url)
    except Exception as error:
        print(f"❌ Ошибка RSS: {error}")
        return []

    if getattr(feed, "bozo", False):
        print("⚠ RSS вернул предупреждение.")

    entries = getattr(feed, "entries", [])

    if not entries:
        print("⚠ Новостей не найдено.")
        return []

    results = []

    for entry in entries[:20]:

        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        summary = (
            entry.get("summary")
            or entry.get("description")
            or ""
        )

        published = (
            entry.get("published")
            or entry.get("updated")
            or ""
        )

        if not title or not link:
            continue

        # Проверяем БД
        if article_exists(link):
            print(f"  ⏭ Уже есть: {title}")
            continue

        score = calculate_relevance_score(
            title,
            summary,
        )

        print()
        print(f"  📰 {title}")
        print(f"     score={score}")

        if not is_space_article(title, summary):
            print("     ❌ Отклонено")
            continue

        print("     ✅ Принято")

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
    print(f"📊 Принято: {len(results)}")

    return results


# ============================================================
# СБОР НОВОСТЕЙ ИЗ ВСЕХ ИСТОЧНИКОВ
# ============================================================

def collect_news(
    feeds: Dict[str, str],
    max_articles_per_source: int = 5,
) -> List[Dict]:

    all_articles = []

    for source, url in feeds.items():

        articles = parse_feed(
            source,
            url,
        )

        articles = articles[:max_articles_per_source]

        all_articles.extend(articles)

    # Сначала самые интересные
    all_articles.sort(
        key=lambda article: article.get("score", 0),
        reverse=True,
    )

    print()
    print("=" * 70)
    print("🏆 ИТОГОВЫЙ РЕЙТИНГ НОВОСТЕЙ")
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
    print(f"Всего найдено: {len(articles)}")
