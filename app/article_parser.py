import requests
from bs4 import BeautifulSoup


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def get_article_text(url: str) -> str:
    """
    Загружает страницу статьи и пытается извлечь основной текст.
    """

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT
            },
            timeout=20
        )

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"⚠ Не удалось открыть статью: {url}")
        print(f"  Ошибка: {error}")
        return ""

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Удаляем элементы, которые не являются текстом статьи.
    for element in soup([
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        "form",
        "noscript",
    ]):
        element.decompose()

    # Сначала пытаемся найти типичные контейнеры статьи.
    article = soup.find("article")

    if article is None:
        article = soup.find(
            "main"
        )

    if article is None:
        article = soup.body

    if article is None:
        return ""

    paragraphs = article.find_all("p")

    texts = []

    for paragraph in paragraphs:
        text = paragraph.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        if len(text) < 40:
            continue

        texts.append(text)

    result = "\n\n".join(texts)

    return result.strip()
