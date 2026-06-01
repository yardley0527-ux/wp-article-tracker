#!/usr/bin/env python3
"""
從 WordPress API 重新同步文章清單（保留已記錄的狀態和備註）
用法：python3 sync.py
"""
import json, ssl, urllib.request
from datetime import datetime
from pathlib import Path

WP_URL = "https://104.154.140.219"
OUT = Path(__file__).parent / "articles.json"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_all():
    posts = []
    page = 1
    while True:
        url = f"{WP_URL}/wp-json/wp/v2/posts?per_page=100&page={page}&_fields=id,title,date,modified,status,link"
        req = urllib.request.urlopen(url, context=ctx, timeout=30)
        batch = json.loads(req.read())
        if not batch:
            break
        posts.extend(batch)
        print(f"  Page {page}: {len(batch)} posts (total {len(posts)})")
        page += 1
    return posts

def main():
    print("同步文章清單...")
    posts = fetch_all()

    # 讀取現有狀態（保留 status 和 note）
    existing = {}
    if OUT.exists():
        old = json.loads(OUT.read_text(encoding='utf-8'))
        for a in old.get("articles", []):
            existing[a["id"]] = {"status": a.get("status", "pending"), "note": a.get("note", "")}

    articles = []
    for p in posts:
        prev = existing.get(p["id"], {})
        articles.append({
            "id": p["id"],
            "title": p["title"]["rendered"],
            "date": p["date"],
            "modified": p["modified"],
            "link": p["link"],
            "status": prev.get("status", "pending"),
            "note": prev.get("note", "")
        })

    articles.sort(key=lambda x: x["date"], reverse=True)
    done = sum(1 for a in articles if a["status"] == "done")

    output = {
        "meta": {
            "total": len(articles),
            "done": done,
            "pending": len(articles) - done,
            "last_sync": datetime.now().isoformat()
        },
        "articles": articles
    }

    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n完成！共 {len(articles)} 篇，已完成 {done} 篇，待處理 {len(articles)-done} 篇")
    print(f"已存至 {OUT}")

if __name__ == "__main__":
    main()
