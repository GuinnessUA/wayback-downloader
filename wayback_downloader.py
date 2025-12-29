import subprocess
import argparse
import os
import re
import glob

def extract_timestamp(wayback_url):
    """Витягує timestamp з Wayback URL"""
    match = re.search(r"/web/(\d{14})", wayback_url)
    if not match:
        raise ValueError("Не вдалося знайти timestamp у URL. Перевірте формат (наприклад, 20251015055055).")
    return match.group(1)

def download_with_wget(wayback_url, output_dir):
    """Рекурсивно завантажує весь сайт з Wayback за допомогою wget"""
    cmd = [
        "wget",
        "--mirror",                     # Повний міррор: recursive + page-requisites
        "--page-requisites",            # Завантажує CSS, JS, images, fonts
        "--convert-links",              # Переписує посилання для офлайн
        "--adjust-extension",           # .html, .css тощо
        "--span-hosts",                 # Дозволяє CDN Wayback
        "--domains=web.archive.org,webstatic.archive.org",
        "--no-parent",
        "--wait=2",
        "--random-wait",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "-e", "robots=off",
        "-nH",
        "--cut-dirs=5",
        "--directory-prefix=" + output_dir,
        "--no-clobber",
        "--timeout=30",
        wayback_url
    ]

    print("Починаю рекурсивне завантаження ВСЬОГО сайту...")
    print(f"Папка: {output_dir}")
    print("Для великого магазину це займе години, але завантажить все доступне.\n")

    try:
        subprocess.run(cmd, check=True)
        print("Завантаження завершено!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Помилка wget: {e}")
        return False
    except FileNotFoundError:
        print("wget не знайдено. Встановіть та додайте до PATH.")
        return False

def clean_wayback_prefixes(output_dir, timestamp):
    """Очищає префікси Wayback у всіх HTML"""
    print("Очищаємо префікси Wayback...")

    prefixes = ["js_", "cs_", "im_", "if_", "id_", ""]
    html_files = glob.glob(os.path.join(output_dir, "**/*.html"), recursive=True)

    cleaned_count = 0
    for file_path in html_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            original = content
            for prefix in prefixes:
                pattern = f"/web/{timestamp}{prefix}_/"
                content = content.replace(pattern, "/")

            if content != original:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                cleaned_count += 1
        except Exception as e:
            print(f"Помилка в {file_path}: {e}")

    print(f"Очищено префікси у {cleaned_count} з {len(html_files)} файлів.\n")

def main(wayback_url, output_dir=None):
    if output_dir is None:
        output_dir = "wayback_site"

    os.makedirs(output_dir, exist_ok=True)

    print(f"Wayback URL: {wayback_url}\n")

    try:
        timestamp = extract_timestamp(wayback_url)
        print(f"Timestamp: {timestamp}\n")
    except ValueError as e:
        print(e)
        return

    if not download_with_wget(wayback_url, output_dir):
        return

    clean_wayback_prefixes(output_dir, timestamp)

    print("ГОТОВО!")
    print(f"Сайт у папці: {os.path.abspath(output_dir)}")
    print("Відкрийте index.html — все (стилі, зображення, скрипти) має працювати офлайн.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Універсальний завантажувач Wayback на Python (весь сайт + чисті URL)")
    parser.add_argument("wayback_url", help="Повне Wayback URL снапшота")
    parser.add_argument("-o", "--output", help="Папка збереження", default=None)

    args = parser.parse_args()
    main(args.wayback_url, args.output)