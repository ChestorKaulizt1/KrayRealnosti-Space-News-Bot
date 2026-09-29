import feedparser

from app.config import RSS_FEEDS, MAX_ARTICLES_PER_SOURCE
from app.database import article_exists, save_article


SPACE_KEYWORDS = [
    # Планеты и объекты
    "mars",
    "moon",
    "lunar",
    "venus",
    "mercury",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",

    # Космос
    "space",
    "cosmos",
    "astronomy",
    "astronomical",
    "astrophysics",
    "astrophysical",
    "universe",
    "cosmic",

    # Звёзды
    "star",
    "stars",
    "stellar",
    "neutron star",
    "pulsar",
    "magnetar",
    "supernova",
    "supernovae",

    # Чёрные дыры
    "black hole",
    "black holes",
    "supermassive black hole",
    "event horizon",

    # Галактики
    "galaxy",
    "galaxies",
    "galactic",

    # Экзопланеты
    "exoplanet",
    "exoplanets",
    "habitable planet",
    "habitable world",

    # Малые тела
    "asteroid",
    "asteroids",
    "comet",
    "comets",
    "meteor",
    "meteors",
    "meteorite",
    "interstellar object",

    # Телескопы
    "jwst",
    "james webb",
    "webb telescope",
    "hubble",
    "space telescope",

    # Космические аппараты
    "spacecraft",
    "spaceship",
    "space station",
    "iss",
    "starliner",
    "artemis",
    "apollo mission",
    "rover",
    "probe",
    "orbiter",

    # Ракеты и запуски
    "rocket",
    "rockets",
    "launch",
    "launches",
    "liftoff",
    "spacex",
    "starship",

    # Солнце
    "solar flare",
    "solar storm",
    "solar wind",
    "sunspot",
    "coronal mass ejection",

    # Космические явления
    "gamma ray burst",
    "gamma-ray burst",
    "gravitational wave",
    "dark matter",
    "dark energy",
    "wormhole",
    "quasar",
    "nebula",

    # Люди и наблюдения
    "astronaut",
    "astronauts",
    "cosmonaut",
    "cosmonauts",
    "night sky",
    "stargazing",
    "skywatching",

    # Организации
    "nasa",
    "esa",
]


EXCLUDE_KEYWORDS = [
    # Медицина
    "cancer",
    "infection",
    "infections",
    "disease",
    "medicine",
    "medical",
    "health",
    "brain health",
    "menopause",
    "drug",
    "drugs",

    # Психология
    "anger",
    "anxiety",
    "depression",
    "psychology",
    "mental health",

    # Питание
    "nutrition",
    "diet",
    "food",
    "calories",

    # Политика
    "politics",
    "political",
    "election",
    "government",

    # Земные темы
    "ocean",
    "oceans",
    "climate",
    "earthquake",
    "volcano",
    "weather",

    # Технологии, не связанные напрямую с космосом
    "quantum computer",
    "quantum computing",
    "artificial intelligence",
    "ai model",
    "smartphone",
]


def calculate_relevance_score(
    title: str,
    source: str = ""
) -> int:
    text = title.lower()

    score = 0

    for keyword in SPACE_KEYWORDS:
        if keyword in text:
            score += 3

    for keyword in EXCLUDE_KEYWORDS:
        if keyword in text:
            score -= 5

    return score


def is_space_article(
    title: str,
    source: str = ""
) -> bool:
    title_lower = title.lower()

    score = calculate_relevance_score(
        title=title,
        source=source
    )

    if score < 3:
        return False

    earth_keywords = [
        "earth",
        "earth observatory",
        "weather",
        "climate",
        "wildfire",
        "fire cloud",
        "hurricane",
        "storm",
        "ocean",
        "forest",
        "atmosphere",
    ]

    for keyword in earth_keywords:
        if keyword in title_lower:
            return False

    return True

    return score >= 3


def collect_news():
    new_articles = []

    for source, feed_url in RSS_FEEDS.items():

        print()
        print("=" * 60)
        print(f"Проверяем: {source}")
        print(f"RSS: {feed_url}")

        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print("⚠ RSS вернул предупреждение")

            entries = feed.entries[:MAX_ARTICLES_PER_SOURCE]

            if not entries:
                print("Новостей не найдено.")
                continue

            for entry in entries:

                title = entry.get(
                    "title",
                    "Без названия"
                ).strip()

                url = entry.get(
                    "link",
                    ""
                ).strip()

                published = entry.get(
                    "published",
                    entry.get(
                        "updated",
                        ""
                    )
                )

                if not url:
                    continue

                score = calculate_relevance_score(
                    title=title,
                    source=source
                )

                if not is_space_article(
                    title=title,
                    source=source
                ):
                    print(
                        f"  ✕ Пропущено "
                        f"(score={score}): "
                        f"{title}"
                    )
                    continue

                print(
                    f"  ✓ Космос "
                    f"(score={score}): "
                    f"{title}"
                )

                if article_exists(url):
                    print(
                        f"  ↳ Уже есть в базе: "
                        f"{title}"
                    )
                    continue

                save_article(
                    source=source,
                    title=title,
                    url=url,
                    published=published
                )

                article = {
                    "source": source,
                    "title": title,
                    "url": url,
                    "published": published,
                    "score": score,
                }

                new_articles.append(article)

                print(
                    f"  + НОВАЯ "
                    f"КОСМИЧЕСКАЯ НОВОСТЬ: "
                    f"{title}"
                )

        except Exception as error:
            print(
                f"  ОШИБКА {source}: "
                f"{error}"
            )

    return new_articles
