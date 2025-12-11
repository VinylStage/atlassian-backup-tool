# parsing_tests.py

import json
import re

with open("./sample.json", "r", encoding="utf-8") as f:
    data = json.load(f)

titles = []

for page in data:
    title = page.get("title", "")
    body = page.get("body", {})
    storage = body.get("storage", {})
    value = storage.get("value", "")
    titles.append(title)

print(titles)
# print(len(titles))
print("="*50)
updated_titles = []

for title in titles:
    title = title.strip()
    title = re.sub(r'[\/\\:\*\?"<>|]', "_", title)
    title = re.sub(r"\s+", "_", title)
    updated_titles.append(title)

print(updated_titles)