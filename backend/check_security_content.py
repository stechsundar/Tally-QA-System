import json

# Check what security content we actually have
with open('tally_docs.json', 'r', encoding='utf-8') as f:
    docs = json.load(f)

print("🔍 Checking security content in knowledge base...")

security_docs = [doc for doc in docs if 'security' in doc.get('title', '').lower() or 'user' in doc.get('title', '').lower() and 'permission' in doc.get('title', '').lower()]

print(f"Found {len(security_docs)} security documents:")
for doc in security_docs:
    print(f"\n📄 {doc['title']}")
    print(f"   URL: {doc['url']}")
    print(f"   Content preview: {doc['content'][:300]}...")
    
    # Check for Alt+K
    if 'Alt+K' in doc['content']:
        print("   ✅ Contains Alt+K information")
    else:
        print("   ❌ No Alt+K found")

# Also check the specific URL we added
target_url = "https://help.tallysolutions.com/?geot_debug=IN&cat_id=23&s=Security+and+user+permissions+setup"
target_doc = next((doc for doc in docs if doc['url'] == target_url), None)

if target_doc:
    print(f"\n🎯 Target URL document found:")
    print(f"   Title: {target_doc['title']}")
    print(f"   Content length: {len(target_doc['content'])} characters")
    print(f"   First 500 chars: {target_doc['content'][:500]}...")
else:
    print(f"\n❌ Target URL document not found!")
