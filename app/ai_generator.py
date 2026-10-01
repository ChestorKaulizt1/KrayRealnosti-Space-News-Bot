import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def check_configuration() -> bool:
if not OPENROUTER_API_KEY:
print("❌ OPENROUTER_API_KEY не найден.")
return False

```
print("✓ OPENROUTER_API_KEY найден")
return True
```

def generate_post(article_title: str, article_text: str):
print("🤖 AI Generator запущен")
print(f"Заголовок: {article_title}")

```
if not check_configuration():
    return None

return None
```
