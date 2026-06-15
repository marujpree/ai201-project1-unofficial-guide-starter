"""
Scrapes r/UniversityOfHouston for Organic Chemistry posts and comments
using old.reddit.com HTML — no API key or authentication required.

Run once to populate documents/reddit_uh_ochem.txt, then run ingest.py.
"""

import time
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DOCUMENTS_DIR = Path("documents")
OUTPUT_FILE = DOCUMENTS_DIR / "reddit_uh_ochem.txt"

BASE = "https://old.reddit.com"
SUBREDDIT = "UniversityOfHouston"

SEARCH_QUERIES = [
    "organic chemistry",
    "ochem",
    "CHEM 2323",
    "CHEM 2325",
    "Daugulis",
    "Carrow ochem",
    "Comito chemistry",
    "Crystal Young",
    "Mary Bean chem",
    "Loi Do chem",
]

MAX_DEPTH = 1   # only top-level comments (depth 0) and their direct replies (depth 1)
MIN_COMMENT_LEN = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get(url: str, params: dict = None) -> BeautifulSoup:
    time.sleep(2)   # polite delay — old Reddit allows scraping at low rate
    r = requests.get(url, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def search_posts(query: str) -> list[dict]:
    soup = get(f"{BASE}/r/{SUBREDDIT}/search/", params={
        "q": query,
        "restrict_sr": "on",
        "sort": "relevance",
        "limit": "25",
    })
    posts = []
    for div in soup.select("div.search-result-link"):
        a = div.select_one("a.search-title")
        if not a:
            continue
        href = a.get("href", "")
        # Normalise to old.reddit URL
        if href.startswith("https://www.reddit.com"):
            href = href.replace("https://www.reddit.com", BASE)
        elif not href.startswith("http"):
            href = BASE + href
        post_id = re.search(r"/comments/([a-z0-9]+)/", href)
        posts.append({
            "id": post_id.group(1) if post_id else href,
            "title": a.text.strip(),
            "url": href.split("?")[0],
        })
    return posts


def fetch_post(url: str) -> dict | None:
    soup = get(url)

    # Title
    title_tag = soup.select_one("a.title")
    title = title_tag.text.strip() if title_tag else "Unknown"

    # Post selftext (the link-type thing at the top)
    post_thing = soup.select_one("div.thing.link")
    selftext = ""
    if post_thing:
        body_div = post_thing.select_one("div.usertext-body")
        if body_div:
            raw = body_div.get_text(" ", strip=True)
            # Skip if it's just the title echoed back or sidebar boilerplate
            if len(raw) > len(title) + 10:
                selftext = raw

    # Score / metadata from the thing div
    score = post_thing.get("data-score", "?") if post_thing else "?"
    author = post_thing.get("data-author", "?") if post_thing else "?"

    # Timestamp — old Reddit puts it in a <time> tag
    time_tag = soup.select_one("div.thing.link time")
    date_str = time_tag.get("datetime", "")[:10] if time_tag else ""

    # Comments — only keep shallow depth
    comments = []
    for ct in soup.select("div.thing.comment"):
        depth = int(ct.get("data-depth", "99"))
        if depth > MAX_DEPTH:
            continue
        body_div = ct.select_one("div.usertext-body")
        if not body_div:
            continue
        text = body_div.get_text(" ", strip=True)
        if len(text) < MIN_COMMENT_LEN or text in ("[deleted]", "[removed]"):
            continue
        c_score = ct.get("data-score", "?")
        c_author = ct.get("data-author", "?")
        comments.append({"depth": depth, "score": c_score, "author": c_author, "text": text})

    return {
        "title": title,
        "url": url.replace(BASE, "https://www.reddit.com"),
        "date": date_str,
        "score": score,
        "author": author,
        "selftext": selftext,
        "comments": comments,
    }


def format_post(post: dict) -> str:
    lines = [
        "POST",
        f"Title: {post['title']}",
        f"Date: {post['date']}",
        f"Score: {post['score']}",
        f"URL: {post['url']}",
        "",
    ]
    if post["selftext"]:
        lines.append(post["selftext"])
        lines.append("")

    if post["comments"]:
        lines.append("Comments:")
        for c in post["comments"]:
            indent = "  " if c["depth"] == 0 else "    "
            lines.append(f"{indent}[score: {c['score']}] {c['text']}")
            lines.append("")

    lines += ["---", ""]
    return "\n".join(lines)


def main() -> None:
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    seen_ids: set[str] = set()
    collected: list[dict] = []

    for query in SEARCH_QUERIES:
        print(f"Searching: '{query}'...")
        try:
            posts = search_posts(query)
            new = [p for p in posts if p["id"] not in seen_ids]
            print(f"  {len(posts)} results, {len(new)} new posts to fetch")
            for meta in new:
                seen_ids.add(meta["id"])
                print(f"  Fetching: {meta['title'][:65]}")
                try:
                    post = fetch_post(meta["url"])
                    if post:
                        collected.append(post)
                except Exception as exc:
                    print(f"    ERROR: {exc}")
        except Exception as exc:
            print(f"  ERROR on search '{query}': {exc}")

    print(f"\nTotal posts collected: {len(collected)}")

    lines = [
        "SOURCE: Reddit - r/UniversityOfHouston",
        "URL: https://www.reddit.com/r/UniversityOfHouston/",
        "SCRAPED: " + time.strftime("%Y-%m-%d"),
        "DESCRIPTION: Posts and comments from UH students discussing Organic Chemistry",
        "(CHEM 2323 / Organic Chemistry I and CHEM 2325 / Organic Chemistry II).",
        "Search terms: " + ", ".join(SEARCH_QUERIES),
        "",
        "=" * 60,
        "",
    ]
    for post in collected:
        lines.append(format_post(post))

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved to {OUTPUT_FILE}")
    print("Run ingest.py to verify chunk output.")


if __name__ == "__main__":
    main()
