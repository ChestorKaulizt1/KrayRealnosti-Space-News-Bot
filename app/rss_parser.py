import feedparser

from app.config import RSS_FEEDS, MAX_ARTICLES_PER_SOURCE
from app.database import article_exists, save_article


# ============================================================
# КОСМИЧЕСКИЕ КЛЮЧЕВЫЕ СЛОВА
# ============================================================

SPACE_KEYWORDS = [
    # Общие космические термины
    "space",
    "spaceflight",
    "spacecraft",
    "cosmos",
    "cosmic",
    "universe",
    "astronomy",
    "astronomical",
    "astrophysics",
    "celestial",

    # Планеты
    "planet",
    "planets",
    "exoplanet",
    "exoplanets",
    "super-earth",
    "super earth",
    "hot jupiter",
    "gas giant",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "mercury",
    "venus",
    "mars",

    # Луны и спутники
    "moon",
    "lunar",
    "moons",
    "satellite",
    "enceladus",
    "europa",
    "titan",
    "ganymede",
    "callisto",
    "io",
    "triton",
    "phobos",
    "deimos",

    # Солнце
    "sun",
    "solar",
    "solar flare",
    "solar flares",
    "solar storm",
    "solar storms",
    "solar wind",
    "sunspot",
    "sunspots",
    "coronal mass ejection",
    "cme",
    "corona",

    # Звёзды
    "star",
    "stars",
    "starbirth",
    "star birth",
    "star formation",
    "stellar",
    "neutron star",
    "neutron stars",
    "pulsar",
    "pulsars",
    "magnetar",
    "magnetars",
    "supernova",
    "supernovae",
    "hypernova",
    "white dwarf",
    "white dwarfs",
    "red giant",
    "red giants",
    "stellar explosion",

    # Чёрные дыры
    "black hole",
    "black holes",
    "event horizon",
    "gravitational singularity",
    "singularity",
    "accretion disk",
    "accretion disc",
    "hawking radiation",
    "black hole merger",
    "black hole mergers",

    # Галактики
    "galaxy",
    "galaxies",
    "milky way",
    "andromeda",
    "galactic",
    "galactic center",
    "galactic centre",

    # Квазары и активные ядра
    "quasar",
    "quasars",
    "blazar",
    "blazars",
    "active galaxy",
    "active galactic nucleus",
    "agn",

    # Туманности
    "nebula",
    "nebulae",
    "supernova remnant",
    "planetary nebula",

    # Космические объекты
    "asteroid",
    "asteroids",
    "comet",
    "comets",
    "meteor",
    "meteors",
    "meteorite",
    "meteorites",
    "interstellar",
    "interstellar object",
    "interstellar objects",
    "oumuamua",
    "ʻoumuamua",
    "sedna",
    "kuiper belt",
    "oort cloud",

    # Космические миссии
    "nasa",
    "esa",
    "james webb",
    "jwst",
    "webb telescope",
    "hubble",
    "hubble telescope",
    "chandra",
    "spitzer",
    "kepler telescope",
    "tess",
    "euclid telescope",
    "roman telescope",

    # Космические аппараты
    "spacecraft",
    "probe",
    "probes",
    "rover",
    "rovers",
    "orbiter",
    "lander",
    "landings",
    "space station",
    "iss",
    "international space station",

    # Ракеты и запуски
    "rocket",
    "rockets",
    "rocket launch",
    "launch",
    "launches",
    "launching",
    "spacex",
    "starship",
    "falcon 9",
    "falcon heavy",
    "artemis",
    "apollo",
    "blue origin",
    "new glenn",

    # Люди в космосе
    "astronaut",
    "astronauts",
    "cosmonaut",
    "cosmonauts",
    "human spaceflight",
    "crewed mission",
    "crewed missions",

    # Гравитация и физика космоса
    "gravity",
    "gravitational",
    "gravitational wave",
    "gravitational waves",
    "gravitational wave signal",
    "gravitational lensing",
    "dark matter",
    "dark energy",
    "wormhole",
    "wormholes",
    "boson star",
    "boson stars",
    "scalar field",
    "scalar fields",
    "quantum gravity",

    # Сигналы и возможная жизнь
    "alien",
    "aliens",
    "extraterrestrial",
    "extraterrestrial life",
    "alien life",
    "alien world",
    "alien worlds",
    "life beyond earth",
    "life beyond earth",
    "habitable",
    "habitability",
    "habitable planet",
    "habitable planets",
    "biosignature",
    "biosignatures",
    "technosignature",
    "technosignatures",
    "radio signal",
    "radio signals",
    "fast radio burst",
    "fast radio bursts",
    "frb",
    "strange signal",
    "strange signals",

    # Космические явления
    "gamma ray burst",
    "gamma-ray burst",
    "gamma ray bursts",
    "gamma-ray bursts",
    "grb",
    "cosmic ray",
    "cosmic rays",
    "cosmic background",
    "cosmic microwave background",
    "cmb",
    "reionization",
    "early universe",
    "ancient universe",
    "big bang",

    # Атмосферы планет
    "planetary atmosphere",
    "planet atmosphere",
    "atmosphere of mars",
    "atmosphere of venus",
    "atmosphere of exoplanet",

    # Космическая пыль / диски
    "protoplanetary disk",
    "protoplanetary disc",
    "planet-forming disk",
    "planet-forming disc",
    "circumstellar disk",
    "circumstellar disc",
    "cosmic dust",
    "stellar nursery",

    # Необычные космические объекты
    "strange object",
    "strange objects",
    "mysterious object",
    "mysterious objects",
    "mysterious signal",
    "mysterious signals",
    "cosmic mystery",
    "cosmic mysteries",
    "unusual object",
    "unusual objects",
    "unusual star",
    "unusual stars",
    "dark object",
    "dark objects",
]


# ============================================================
# КЛЮЧЕВЫЕ СЛОВА, КОТОРЫЕ ПОВЫШАЮТ ИНТЕРЕС
# ============================================================

HIGH_INTEREST_KEYWORDS = [
    # Чёрные дыры
    "black hole",
    "black holes",
    "event horizon",
    "hawking radiation",
    "black hole merger",

    # Возможная жизнь
    "alien",
    "aliens",
    "extraterrestrial",
    "extraterrestrial life",
    "alien life",
    "life beyond earth",
    "habitable planet",
    "biosignature",
    "biosignatures",
    "technosignature",
    "radio signal",
    "strange signal",

    # Необычные открытия
    "mysterious",
    "mystery",
    "strange",
    "unusual",
    "unexpected",
    "surprising",
    "enigmatic",
    "anomaly",
    "anomalous",

    # Новые открытия
    "discovery",
    "discover",
    "discovered",
    "reveals",
    "revealed",
    "new research",
    "new study",
    "new observations",
    "new evidence",

    # Планеты
    "exoplanet",
    "exoplanets",
    "earth-like",
    "earthlike",
    "super-earth",
    "super earth",
    "hot jupiter",

    # Космические сигналы
    "fast radio burst",
    "fast radio bursts",
    "radio signal",
    "radio signals",
    "gravitational wave",
    "gravitational waves",

    # Астероиды и кометы
    "asteroid",
    "asteroids",
    "comet",
    "comets",
    "interstellar object",

    # Древняя Вселенная
    "early universe",
    "ancient universe",
    "first stars",
    "first galaxies",
    "early galaxy",
    "early galaxies",

    # Экстремальные объекты
    "neutron star",
    "neutron stars",
    "pulsar",
    "magnetar",
    "supernova",
    "quasar",
    "quasars",

    # Особые космические явления
    "gamma ray burst",
    "gamma-ray burst",
    "gravitational lensing",
    "dark matter",
    "dark energy",
    "wormhole",
    "boson star",
]


# ============================================================
# СЛОВА, КОТОРЫЕ СИЛЬНО СНИЖАЮТ РЕЛЕВАНТНОСТЬ
# ============================================================

EXCLUDE_KEYWORDS = [
    # Здоровье / медицина
    "cancer",
    "disease",
    "health",
    "medical",
    "medicine",
    "hospital",
    "patient",
    "therapy",
    "drug",
    "nutrition",
    "diet",
    "heart health",
    "cognitive decline",
    "mental health",

    # Политика
    "politics",
    "political",
    "election",
    "president",
    "government",
    "senate",
    "congress",

    # Земные катастрофы / природа
    "earthquake",
    "earthquakes",
    "volcano",
    "volcanic eruption",
    "wildfire",
    "forest fire",
    "hurricane",
    "tornado",
    "flood",
    "flooding",

    # Погода
    "weather forecast",
    "weather warning",
    "storms continue",
    "powerful storms",
    "storm system",

    # Океаны
    "ocean",
    "oceans",
    "marine biology",
    "sea level",

    # Земной климат
    "climate policy",
    "climate change",
    "global warming",
    "carbon emissions",

    # Технологии, не связанные напрямую с космосом
    "smartphone",
    "iphone",
    "android",
    "computer chip",
    "social media",

    # Бытовые темы
    "food",
    "fruit",
    "coffee",
    "recipe",
    "fashion",
    "sports",
    "football",
    "soccer",
    "celebrity",
]


# ============================================================
# СЛОВА, КОТОРЫЕ СНИЖАЮТ ИНТЕРЕС
# ============================================================

BORING_KEYWORDS = [
    "contract",
    "contracts",
    "procurement",
    "agreement",
    "partnership",
    "press release",
    "conference",
    "symposium",
    "statement",
    "office",
    "administrative",
    "services",
    "support services",
    "event",
    "meeting",
    "webinar",
    "announcement",
    "application deadline",
]


# ============================================================
# ОПРЕДЕЛЕНИЕ КОСМИЧЕСКОЙ НОВОСТИ
# ============================================================

def calculate_relevance_score(title: str, source: str = "") -> int:
    """
    Рассчитывает базовую релевантность новости космосу.
    """

    text = title.lower()

    score = 0

    # --------------------------------------------------------
    # Базовые космические ключевые слова
    # --------------------------------------------------------

    matched_space_keywords = set()

    for keyword in SPACE_KEYWORDS:
        if keyword in text:
            matched_space_keywords.add(keyword)

    # Каждое уникальное космическое совпадение
    score += len(matched_space_keywords) * 3

    # --------------------------------------------------------
    # Высокоинтересные темы
    # --------------------------------------------------------

    matched_interest_keywords = set()

    for keyword in HIGH_INTEREST_KEYWORDS:
        if keyword in text:
            matched_interest_keywords.add(keyword)

    score += len(matched_interest_keywords) * 4

    # --------------------------------------------------------
    # Штрафы
    # --------------------------------------------------------

    for keyword in EXCLUDE_KEYWORDS:
        if keyword in text:
            score -= 5

    # --------------------------------------------------------
    # Скучные административные новости
    # --------------------------------------------------------

    for keyword in BORING_KEYWORDS:
        if keyword in text:
            score -= 2

    # --------------------------------------------------------
    # Дополнительные бонусы
    # --------------------------------------------------------

    # Если явно говорится о новом исследовании
    if "new research" in text:
        score += 2

    if "new study" in text:
        score += 2

    if "new discovery" in text:
        score += 3

    if "discovery" in text:
        score += 2

    if "discovered" in text:
        score += 2

    # Если речь идёт о необычном космическом объекте
    if "strange" in text:
        score += 3

    if "mysterious" in text:
        score += 3

    if "mystery" in text:
        score += 3

    if "unexpected" in text:
        score += 3

    if "anomaly" in text:
        score += 4

    # --------------------------------------------------------
    # Источник
    # --------------------------------------------------------

    # NASA само по себе не означает интересную новость,
    # поэтому отдельный бонус не даём.
    #
    # Universe Today и ScienceAlert часто публикуют
    # научные материалы, но также не получат автоматический
    # бонус только за название источника.

    return score


def is_space_article(title: str, source: str = "") -> bool:
    """
    Проверяет, является ли заголовок космической новостью.
    """

    text = title.lower()

    score = calculate_relevance_score(title, source)

    # --------------------------------------------------------
    # Сильные стоп-слова
    # --------------------------------------------------------

    for keyword in EXCLUDE_KEYWORDS:
        if keyword in text:
            # Исключение:
            # если одновременно есть очень сильный
            # космический термин, не удаляем автоматически.
            strong_space_terms = [
                "black hole",
                "exoplanet",
                "planet",
                "moon",
                "mars",
                "jupiter",
                "saturn",
                "neutron star",
                "pulsar",
                "magnetar",
                "supernova",
                "quasar",
                "asteroid",
                "comet",
                "galaxy",
                "gravitational wave",
                "dark matter",
                "dark energy",
                "alien",
                "extraterrestrial",
                "spacecraft",
                "nasa",
                "esa",
            ]

            has_strong_space_term = any(
                term in text
                for term in strong_space_terms
            )

            if not has_strong_space_term:
                return False

    # --------------------------------------------------------
    # Специальная защита для планет
    # --------------------------------------------------------

    # Любой заголовок, где явно есть planet,
    # считаем космическим, если нет сильного стоп-слова.
    if "planet" in text and score >= 3:
        return True

    # --------------------------------------------------------
    # Специальная защита для лун
    # --------------------------------------------------------

    moon_terms = [
        "moon",
        "lunar",
        "enceladus",
        "europa",
        "titan",
        "ganymede",
        "callisto",
        "io",
        "triton",
        "phobos",
        "deimos",
    ]

    if any(term in text for term in moon_terms) and score >= 3:
        return True

    # --------------------------------------------------------
    # Обычная проверка
    # --------------------------------------------------------

    if score < 3:
        return False

    # --------------------------------------------------------
    # Дополнительная защита от земных новостей
    # --------------------------------------------------------

    earth_only_terms = [
        "pacific",
        "river",
        "rivers",
        "forest",
        "permafrost",
        "soil",
        "wildlife",
        "earth's climate",
        "earth climate",
    ]

    for keyword in earth_only_terms:
        if keyword in text:
            strong_space_terms = [
                "black hole",
                "exoplanet",
                "planet",
                "moon",
                "mars",
                "jupiter",
                "saturn",
                "neutron star",
                "pulsar",
                "magnetar",
                "supernova",
                "quasar",
                "asteroid",
                "comet",
                "galaxy",
                "gravitational wave",
                "dark matter",
                "dark energy",
                "alien",
                "extraterrestrial",
                "spacecraft",
                "nasa",
                "esa",
            ]

            if not any(term in text for term in strong_space_terms):
                return False

    return True


# ============================================================
# ПОЛУЧЕНИЕ НОВОСТЕЙ ИЗ RSS
# ============================================================

def collect_news():
    """
    Собирает новые космические новости из всех RSS-источников.
    """

    all_articles = []

    for source, rss_url in RSS_FEEDS.items():

        print()
        print("=" * 60)
        print(f"Проверяем: {source}")
        print(f"RSS: {rss_url}")

        try:
            feed = feedparser.parse(rss_url)

        except Exception as error:
            print(f"⚠ Ошибка RSS: {error}")
            continue

        if getattr(feed, "bozo", False):
            print("⚠ RSS вернул предупреждение")

        entries = getattr(feed, "entries", [])

        if not entries:
            print("Новостей не найдено.")
            continue

        accepted_from_source = 0

        for entry in entries[:MAX_ARTICLES_PER_SOURCE]:

            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            published = entry.get(
                "published",
                entry.get("updated", ""),
            )

            if not title or not url:
                continue

            score = calculate_relevance_score(
                title,
                source,
            )

            if is_space_article(title, source):

                print(
                    f"  ✓ Космос (score={score}): {title}"
                )

                if article_exists(url):

                    print(
                        "  ↪ Уже есть в базе"
                    )

                    continue

                save_article(
                    source=source,
                    title=title,
                    url=url,
                    published=published,
                )

                article = {
                    "source": source,
                    "title": title,
                    "url": url,
                    "published": published,
                    "score": score,
                }

                all_articles.append(article)

                accepted_from_source += 1

                print(
                    f"  + НОВАЯ КОСМИЧЕСКАЯ НОВОСТЬ: {title}"
                )

            else:

                print(
                    f"  ✕ Пропущено (score={score}): {title}"
                )

        if accepted_from_source == 0:
            # Ничего дополнительно не выводим,
            # чтобы лог оставался компактным.
            pass

    return all_articles


# ============================================================
# ТЕСТ ЗАПУСКА ФАЙЛА
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("ТЕСТ RSS-ПАРСЕРА")
    print("=" * 60)

    articles = collect_news()

    print()
    print("=" * 60)
    print(f"Найдено новых космических материалов: {len(articles)}")
    print("=" * 60)

    for index, article in enumerate(articles, start=1):

        print()
        print(f"[{index}] {article['source']}")
        print(f"Название: {article['title']}")
        print(f"Score: {article['score']}")
        print(f"URL: {article['url']}")
