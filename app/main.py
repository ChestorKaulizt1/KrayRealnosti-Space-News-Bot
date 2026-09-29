from app.rss_parser import collect_news


def main():
    print("=" * 60)
    print("КРАЙ РЕАЛЬНОСТИ — СБОРЩИК КОСМИЧЕСКИХ НОВОСТЕЙ")
    print("=" * 60)

    articles = collect_news()

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


if __name__ == "__main__":
    main()
