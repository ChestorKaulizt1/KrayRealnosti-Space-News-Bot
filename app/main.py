from app.rss_parser import collect_news
from app.article_parser import get_article_text
from app.ai_generator import generate_post


def main():
    print("=" * 60)
    print("КРАЙ РЕАЛЬНОСТИ — СБОРЩИК КОСМИЧЕСКИХ НОВОСТЕЙ")
    print("=" * 60)

    articles = collect_news()

    interesting_keywords = [
        "black hole",
        "black holes",
        "boson star",
        "neutron star",
        "pulsar",
        "magnetar",
        "supernova",
        "exoplanet",
        "exoplanets",
        "alien",
        "mystery",
        "mysterious",
        "strange",
        "unexpected",
        "discovery",
        "discover",
        "revealed",
        "found",
        "ancient",
        "quasar",
        "galaxy",
        "galaxies",
        "asteroid",
        "comet",
        "interstellar",
        "mars",
        "moon",
        "lunar",
        "jupiter",
        "saturn",
        "starbirth",
        "star formation",
        "gravitational wave",
        "gamma ray",
    ]

    boring_keywords = [
        "contract",
        "conference",
        "press release",
        "coverage",
        "services",
        "agreement",
        "partnership",
        "statement",
        "office",
        "event",
    ]

    def calculate_interest(article):
        title = article["title"].lower()

        interest = article["score"]

        for keyword in interesting_keywords:
            if keyword in title:
                interest += 5

        for keyword in boring_keywords:
            if keyword in title:
                interest -= 4

        return interest

    articles = sorted(
        articles,
        key=calculate_interest,
        reverse=True
    )[:2]

    print()
    print(f"Выбрано для генерации постов: {len(articles)}")

    print()
    print("=" * 60)
    print(f"Новых космических материалов: {len(articles)}")
    print("=" * 60)

    if not articles:
        print("Новых космических новостей нет.")
        return

    for number, article in enumerate(
        articles,
        start=1
    ):
        print()
        print(f"[{number}] {article['source']}")
        print(f"Название: {article['title']}")
        print(f"Score: {article['score']}")
        print(f"Дата: {article['published']}")
        print(f"Ссылка: {article['url']}")

        print()
        print("Получаем текст статьи...")

        text = get_article_text(
            article["url"]
        )

        if not text:
            print("⚠ Текст статьи получить не удалось.")
            continue

        print(
            f"✓ Текст получен: "
            f"{len(text)} символов"
        )

        print()
        print("Отправляем статью в OpenRouter...")

        post = generate_post(
            title=article["title"],
            article_text=text
        )

        if not post:
            print("⚠ Не удалось создать пост.")
            continue

        print()
        print("=" * 60)
        print("ГОТОВЫЙ ПОСТ")
        print("=" * 60)
        print(post)
        print("=" * 60)


if __name__ == "__main__":
    main()
