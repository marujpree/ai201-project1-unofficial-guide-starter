"""
Scrapes UH grade distribution data for CHEM 2323 / 2325 (OChem I & II)
from the CougarGrades public data GitHub repository.

Data source: https://github.com/cougargrades/publicdata
Run once to populate documents/cougargrades_ochem.txt, then run ingest.py.
"""

import csv
import io
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import requests

DOCUMENTS_DIR = Path("documents")
OUTPUT_FILE = DOCUMENTS_DIR / "cougargrades_ochem.txt"

BASE_URL = "https://raw.githubusercontent.com/cougargrades/publicdata/master/documents/edu.uh.grade_distribution"

# Course numbers (old and new) for OChem I and II
OCHEM_I_NUMS  = {"2323", "3331"}
OCHEM_II_NUMS = {"2325", "3332"}
TARGET_NUMS   = OCHEM_I_NUMS | OCHEM_II_NUMS

# The professors we care about (last name as it appears in data)
TARGET_LAST_NAMES = {"Daugulis", "Young", "Bean", "Comito", "Carrow", "Do"}

# All semester CSV filenames (from the GitHub directory listing)
SEMESTER_FILES = [
    "Grade Distribution 2013-03 (Fall 2013).csv",
    "Grade Distribution 2014-01 (Spring 2014).csv",
    "Grade Distribution 2014-02 (Summer 2014).csv",
    "Grade Distribution 2014-03 (Fall 2014).csv",
    "Grade Distribution 2015-01 (Spring 2015).csv",
    "Grade Distribution 2015-02 (Summer 2015).csv",
    "Grade Distribution 2015-03 (Fall 2015).csv",
    "Grade Distribution 2016-01 (Spring 2016).csv",
    "Grade Distribution 2016-02 (Summer 2016).csv",
    "Grade Distribution 2016-03 (Fall 2016).csv",
    "Grade Distribution 2017-01 (Spring 2017).csv",
    "Grade Distribution 2017-02 (Summer 2017).csv",
    "Grade Distribution 2017-03 (Fall 2017).csv",
    "Grade Distribution 2018-01 (Spring 2018).csv",
    "Grade Distribution 2018-02 (Summer 2018).csv",
    "Grade Distribution 2018-03 (Fall 2018).csv",
    "Grade Distribution 2019-01 (Spring 2019).csv",
    "Grade Distribution 2019-02 (Summer 2019).csv",
    "Grade Distribution 2019-03 (Fall 2019).csv",
    "Grade Distribution 2020-01 (Spring 2020) (S).csv",
    "Grade Distribution 2020-02 (Summer 2020) (S+NCR).csv",
    "Grade Distribution 2020-03 (Fall 2020) (S+NCR).csv",
    "Grade Distribution 2021-01 (Spring 2021) (S+NCR).csv",
    "Grade Distribution 2021-02 (Summer 2021) (S+NCR).csv",
    "Grade Distribution 2021-03 (Fall 2021).csv",
    "Grade Distribution 2022-01 (Spring 2022).csv",
    "Grade Distribution 2022-02 (Summer 2022).csv",
    "Grade Distribution 2022-03 (Fall 2022).csv",
    "Grade Distribution 2023-01 (Spring 2023).csv",
    "Grade Distribution 2023-02 (Summer 2023).csv",
    "Grade Distribution 2023-03 (Fall 2023).csv",
    "Grade Distribution 2024-01 (Spring 2024).csv",
    "Grade Distribution 2024-02 (Summer 2024).csv",
    "Grade Distribution 2024-03 (Fall 2024).csv",
    "Grade Distribution 2025-01 (Spring 2025).CSV",
]


def fetch_csv(filename: str) -> list[dict]:
    url = f"{BASE_URL}/{quote(filename)}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    reader = csv.DictReader(io.StringIO(r.text))
    return list(reader)


def is_target_row(row: dict) -> bool:
    return (
        row.get("SUBJECT") == "CHEM"
        and row.get("CATALOG NBR") in TARGET_NUMS
    )


def gpa_avg(rows: list[dict]) -> float | None:
    gpas = []
    for r in rows:
        try:
            gpas.append(float(r["AVG GPA"]))
        except (ValueError, KeyError):
            pass
    return sum(gpas) / len(gpas) if gpas else None


def format_row(row: dict) -> str:
    a, b, c, d, f = row.get("A","?"), row.get("B","?"), row.get("C","?"), row.get("D","?"), row.get("F","?")
    dropped = row.get("TOTAL DROPPED", "?")
    avg = row.get("AVG GPA", "?")
    section = row.get("CLASS SECTION", "?")
    return f"  Section {section}: A={a} B={b} C={c} D={d} F={f}  Withdrew={dropped}  Avg GPA={avg}"


def main() -> None:
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    # Collect all matching rows across all semesters
    all_rows: list[dict] = []
    for filename in SEMESTER_FILES:
        print(f"  Fetching {filename[:40]}...", end=" ")
        try:
            rows = fetch_csv(filename)
            matches = [r for r in rows if is_target_row(r)]
            all_rows.extend(matches)
            print(f"{len(matches)} OChem rows")
        except Exception as exc:
            print(f"ERROR: {exc}")
        time.sleep(0.3)

    print(f"\nTotal OChem rows collected: {len(all_rows)}")

    # Group by course → professor → semester
    # Structure: courses[course_num][last_name] = [rows]
    courses: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in all_rows:
        num   = row.get("CATALOG NBR", "?")
        lname = row.get("INSTR LAST NAME", "?").strip()
        courses[num][lname].append(row)

    # Build output text
    lines = [
        "SOURCE: CougarGrades.io / UH Office of Institutional Research",
        "DATA FROM: https://github.com/cougargrades/publicdata",
        "SCRAPED: 2026-06-14",
        "DESCRIPTION: Grade distribution for CHEM 2323 (Organic Chemistry I) and",
        "CHEM 2325 (Organic Chemistry II) at the University of Houston.",
        "Course numbers CHEM 3331 and CHEM 3332 are the former names for the same courses.",
        "",
        "Columns: A/B/C/D/F = student counts in each grade band",
        "Withdrew = students who dropped the course",
        "Avg GPA = average GPA of students who completed the course",
        "",
        "=" * 60,
        "",
    ]

    course_labels = {
        "2323": "CHEM 2323 / Organic Chemistry I",
        "3331": "CHEM 3331 / Organic Chemistry I (old course number)",
        "2325": "CHEM 2325 / Organic Chemistry II",
        "3332": "CHEM 3332 / Organic Chemistry II (old course number)",
    }

    for course_num in ("2323", "3331", "2325", "3332"):
        if course_num not in courses:
            continue
        lines.append(f"COURSE: {course_labels[course_num]}")
        lines.append("")

        for lname in sorted(courses[course_num].keys()):
            prof_rows = sorted(courses[course_num][lname], key=lambda r: r.get("TERM", ""))
            first_row = prof_rows[0]
            fname = first_row.get("INSTR FIRST NAME", "").strip()
            avg = gpa_avg(prof_rows)
            avg_str = f"{avg:.3f}" if avg is not None else "N/A"

            lines.append(f"PROFESSOR: {fname} {lname}")
            lines.append(f"Overall average GPA across all sections and semesters: {avg_str}")
            lines.append(f"Semesters taught this course: {len(set(r.get('TERM') for r in prof_rows))}")
            lines.append("")

            # Group by term for per-semester detail
            by_term: dict[str, list[dict]] = defaultdict(list)
            for r in prof_rows:
                by_term[r.get("TERM", "unknown")].append(r)

            for term in sorted(by_term.keys()):
                term_rows = by_term[term]
                term_avg = gpa_avg(term_rows)
                term_avg_str = f"{term_avg:.3f}" if term_avg is not None else "N/A"
                lines.append(f"  {term}  (term avg GPA: {term_avg_str})")
                for r in term_rows:
                    lines.append(format_row(r))
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("=" * 60)
        lines.append("")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
