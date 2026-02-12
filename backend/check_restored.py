import json
docs = json.load(open('tally_docs.json', 'r', encoding='utf-8'))
print(f'✅ Restored {len(docs)} documents')
print('Sample titles:')
for i, doc in enumerate(docs[:5]):
    print(f'  {i+1}. {doc["title"][:80]}...')
