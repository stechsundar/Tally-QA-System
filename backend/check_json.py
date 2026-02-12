import json
from collections import Counter

with open("tally_docs.json", "r", encoding="utf-8") as f:
    docs = json.load(f)

print("Total docs:", len(docs))

sections = []
for doc in docs:
    parts = doc["url"].replace("https://help.tallysolutions.com/", "").split("/")
    if parts:
        sections.append(parts[0])

counter = Counter(sections)

for k, v in counter.most_common():
    print(k, ":", v)
