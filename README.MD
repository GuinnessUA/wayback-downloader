## Що тут є

- `clean.py` — скрипт для очищення HTML від Wayback Machine (видаляє префікси, виправляє посилання, стилі, редіректи)
- `requirements.txt` — залежності
- Папка `my_site/` — очищений сайт (не завантажена в репозиторій через розмір)

## Як запустити

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python clean.py
```
