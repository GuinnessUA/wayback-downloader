import os
import glob
import re
from bs4 import BeautifulSoup, Comment

directory = "./my_site"  # ← зміни, якщо потрібно

print("🔥 Починаю ОСТАТОЧНЕ очищення сайту від Wayback Machine...\n")

# Розширена регулярка — ловить ВСІ можливі Wayback-префікси
WAYBACK_PATTERN = re.compile(
    r"https?://web\.archive\.org/web/\d{14}(?:im_|js_|cs_|if_)?/?"
    r"|/?web/\d{14}(?:im_|js_|cs_|if_)?/?"
    r"|/?(?:cs_|js_|if_)_"   # ← НОВЕ: короткі префікси типу cs_/ js_/
)

html_files = glob.glob(os.path.join(directory, "**/*.html"), recursive=True)

cleaned = 0
fixed_urls = 0

for file_path in html_files:
    rel_path = os.path.relpath(file_path, directory)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if not content.strip():
            continue

        soup = BeautifulSoup(content, "html.parser")
        modified = False

        # 1. Видаляємо тільки шкідливе Wayback-сміття
        for tag in soup.find_all(["script", "link", "meta", "noscript"]):
            # Видаляємо wombat, playback, ruffle скрипти
            if tag.name == "script" and tag.get("src"):
                src = tag.get("src", "")
                if any(bad in src for bad in ["wombat.js", "bundle-playback.js", "ruffle", "__wm"]):
                    tag.decompose()
                    modified = True
            # Видаляємо банерні стилі Wayback
            if tag.name == "link" and tag.get("href") and "banner-styles.css" in tag.get("href", ""):
                tag.decompose()
                modified = True

        # 2. Видаляємо коментарі та елементи Wayback
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if any(kw in str(comment).lower() for kw in ["wayback", "archive", "playback timings", "file archived on", "wombat"]):
                comment.extract()
                modified = True

        for elem in soup.find_all(id=re.compile(r"wm-.*", re.I)):
            elem.decompose()
            modified = True

        # 3. ВИПРАВЛЯЄМО ВСІ URL (включаючи cs_/, js_/)
        for tag in soup.find_all(True):
            attrs = ["href", "src", "srcset", "xlink:href", "data-src", "content"]
            for attr in attrs:
                if tag.has_attr(attr):
                    old_value = tag[attr]

                    if attr == "srcset":
                        sources = [s.strip() for s in old_value.split(",") if s.strip()]
                        cleaned_sources = []
                        for source in sources:
                            parts = source.split()
                            url = parts[0]
                            rest = " ".join(parts[1:]) if len(parts) > 1 else ""
                            cleaned_url = WAYBACK_PATTERN.sub("", url)
                            if cleaned_url != url:
                                modified = True
                                fixed_urls += 1
                            cleaned_sources.append(f"{cleaned_url} {rest}".strip())
                        new_value = ", ".join(cleaned_sources)
                    else:
                        new_value = WAYBACK_PATTERN.sub("", old_value)

                    if new_value != old_value:
                        tag[attr] = new_value
                        fixed_urls += 1
                        modified = True

        # 4. Виправляємо дубльовані теги
        for tag_name in ["html", "head", "body"]:
            tags = soup.find_all(tag_name)
            if len(tags) > 1:
                main_tag = tags[0]
                for extra in tags[1:]:
                    while extra.contents:
                        main_tag.append(extra.contents[0])
                    extra.decompose()
                modified = True

        # 5. Зберігаємо тільки при змінах
        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(soup))  # без prettify, щоб не ламати формат (або з prettify, якщо хочеш)
            cleaned += 1
            print(f"✓ Очищено: {rel_path}")

    except Exception as e:
        print(f"✗ Помилка в {rel_path}: {e}")

print("\n" + "="*70)
print(f"ГОТОВО! Оброблено файлів: {cleaned}")
print(f"Виправлено URL: {fixed_urls}")
print("="*70)
print("Тепер стилі (styles.css, client.css) мають завантажуватись правильно!")
print("• Перевір після очищення кешу браузера (Ctrl+Shift+R)")
print("• Якщо щось ще не так — скинь новий шматок <head>")
print("="*70)