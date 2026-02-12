import json

with open("tally_docs.json", "r", encoding="utf-8") as f:
    docs = json.load(f)

clean_docs = []
removed = []

for doc in docs:
    url = doc.get("url", "").lower()
    content = doc.get("content", "").lower()
    title = doc.get("title", "")

    # Remove ERP9 URLs
    if "tally.erp9" in url:
        removed.append(url)
        continue

    # Remove search pages
    if "?s=" in url:
        removed.append(url)
        continue

    # Remove search page titles
    if "you searched for" in title.lower():
        removed.append(url)
        continue

    # Remove ERP9 content mentions
    if "tally.erp 9" in content:
        removed.append(url)
        continue

    if "shoper 9" in content:
        removed.append(url)
        continue

    if "shoper9" in url:
        removed.append(url)
        continue

    clean_docs.append(doc)

print("Before:", len(docs))
print("After:", len(clean_docs))
print("Removed:", len(removed))

with open("tally_docs_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean_docs, f, indent=2, ensure_ascii=False)
