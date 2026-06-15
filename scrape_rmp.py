"""
Scrapes Rate My Professors reviews for UH Organic Chemistry professors
using RMP's internal GraphQL API.

Run once to populate the documents/ folder, then run ingest.py.
"""

import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

DOCUMENTS_DIR = Path("documents")

RMP_URL = "https://www.ratemyprofessors.com/graphql"
RMP_HEADERS = {
    "Authorization": "Basic dGVzdDp0ZXN0",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Referer": "https://www.ratemyprofessors.com/",
}

QUERY = """
query($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      firstName
      lastName
      department
      numRatings
      avgRating
      avgDifficulty
      wouldTakeAgainPercent
      ratings(first: 20, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        edges {
          node {
            date
            class
            comment
            helpfulRating
            clarityRating
            difficultyRating
            wouldTakeAgain
            attendanceMandatory
            grade
          }
        }
      }
    }
  }
}
"""

# Professor ID → (filename, rmp_url, course)
PROFESSORS = {
    528047:  ("rmp_olaf_daugulis.txt",  "https://www.ratemyprofessors.com/professor/528047",  "CHEM 2323 / Organic Chemistry I"),
    2880547: ("rmp_crystal_young.txt",  "https://www.ratemyprofessors.com/professor/2880547", "CHEM 2323 / Organic Chemistry I"),
    1156106: ("rmp_mary_bean.txt",      "https://www.ratemyprofessors.com/professor/1156106", "CHEM 2323 / Organic Chemistry I"),
    2593590: ("rmp_robert_comito.txt",  "https://www.ratemyprofessors.com/professor/2593590", "CHEM 2325 / Organic Chemistry II"),
    2691934: ("rmp_bradley_carrow.txt", "https://www.ratemyprofessors.com/professor/2691934", "CHEM 2325 / Organic Chemistry II"),
    1916567: ("rmp_loi_do.txt",         "https://www.ratemyprofessors.com/professor/1916567", "CHEM 2325 / Organic Chemistry II"),
}


def encode_rmp_id(numeric_id: int) -> str:
    return base64.b64encode(f"Teacher-{numeric_id}".encode()).decode()


def fetch_all_ratings(numeric_id: int) -> tuple[dict, list[dict]]:
    encoded = encode_rmp_id(numeric_id)
    cursor = None
    professor_info = {}
    all_ratings = []

    while True:
        resp = requests.post(
            RMP_URL,
            headers=RMP_HEADERS,
            json={"query": QUERY, "variables": {"id": encoded, "cursor": cursor}},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        node = data["data"]["node"]
        if not professor_info:
            professor_info = {
                "firstName":            node["firstName"],
                "lastName":             node["lastName"],
                "department":           node.get("department", "Chemistry"),
                "numRatings":           node["numRatings"],
                "avgRating":            node["avgRating"],
                "avgDifficulty":        node["avgDifficulty"],
                "wouldTakeAgainPercent": node["wouldTakeAgainPercent"],
            }

        ratings_data = node["ratings"]
        for edge in ratings_data["edges"]:
            all_ratings.append(edge["node"])

        page_info = ratings_data["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
        time.sleep(0.5)  # polite delay between paginated requests

    return professor_info, all_ratings


def format_document(info: dict, ratings: list[dict], rmp_url: str, course: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    wtag_pct = info["wouldTakeAgainPercent"]
    wtag_str = f"{wtag_pct:.0f}%" if wtag_pct is not None and wtag_pct >= 0 else "N/A"

    lines = [
        "SOURCE: Rate My Professors",
        f"URL: {rmp_url}",
        f"PROFESSOR: {info['firstName']} {info['lastName']}",
        f"COURSE: {course}",
        f"DEPARTMENT: {info.get('department', 'Chemistry')}",
        "UNIVERSITY: University of Houston",
        f"SCRAPED: {today}",
        "",
        f"Overall Rating: {info['avgRating']:.1f} / 5",
        f"Difficulty: {info['avgDifficulty']:.1f} / 5",
        f"Would Take Again: {wtag_str}",
        f"Total Ratings: {info['numRatings']}",
        "",
        "=" * 60,
        "",
    ]

    for r in ratings:
        comment = (r.get("comment") or "").strip()
        if not comment:
            continue  # skip empty reviews

        date_raw = r.get("date", "")
        date_str = date_raw[:10] if date_raw else "unknown"

        wtag = r.get("wouldTakeAgain")
        wtag_label = {1: "Yes", 0: "No"}.get(wtag, "N/A")

        attendance = r.get("attendanceMandatory") or "not specified"

        lines += [
            "REVIEW",
            f"Date: {date_str}",
            f"Course: {r.get('class', 'N/A')}",
            f"Rating (helpfulness): {r.get('helpfulRating', 'N/A')} / 5",
            f"Clarity: {r.get('clarityRating', 'N/A')} / 5",
            f"Difficulty: {r.get('difficultyRating', 'N/A')} / 5",
            f"Grade: {r.get('grade') or 'N/A'}",
            f"Would take again: {wtag_label}",
            f"Attendance: {attendance}",
            "",
            comment,
            "",
            "---",
            "",
        ]

    return "\n".join(lines)


def main() -> None:
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    for numeric_id, (filename, rmp_url, course) in PROFESSORS.items():
        print(f"Fetching {filename} (professor ID {numeric_id})...")
        try:
            info, ratings = fetch_all_ratings(numeric_id)
            print(f"  {info['firstName']} {info['lastName']}: {len(ratings)} reviews")
            content = format_document(info, ratings, rmp_url, course)
            (DOCUMENTS_DIR / filename).write_text(content, encoding="utf-8")
            print(f"  Saved to documents/{filename}")
        except Exception as exc:
            print(f"  ERROR: {exc}")
        time.sleep(1)

    print("\nDone. Run ingest.py to verify chunk output.")


if __name__ == "__main__":
    main()
