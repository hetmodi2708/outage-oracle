import os
import json
from collections import Counter

STRUCTURED_DIR = "data/structured"

categories = []
triggers = []
root_causes = []

for file in os.listdir(STRUCTURED_DIR):
    with open(os.path.join(STRUCTURED_DIR, file), "r", encoding="utf-8") as f:
        record = json.load(f)
    categories.append(record.get("category"))
    triggers.append(record.get("trigger"))
    root_causes.append(record.get("root_cause"))

print(f"Total postmortems: {len(categories)}\n")

print("Category counts:")
for name, count in Counter(categories).most_common():
    print(f"  {name}: {count}")

print("\nTrigger counts:")
for name, count in Counter(triggers).most_common():
    print(f"  {name}: {count}")

print("\nDistinct root causes:", len(set(r for r in root_causes)), "of", len(categories))