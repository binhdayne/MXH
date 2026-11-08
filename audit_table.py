"""Check sampled election edges against the pinned candidate table."""
import argparse
import csv
import json
import math
from pathlib import Path
from unicodedata import normalize

from lxml import html

from build_graph import ELECTION, PARTIES


def wilson_lower(correct, total):
    z = 1.959963984540054
    p = correct / total
    return (p + z*z/(2*total) - z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))) / (1+z*z/total)


def text(cell):
    content = cell.xpath('.//text()[not(ancestor::sup[contains(@class,"reference")])]')
    return " ".join(normalize("NFC", "".join(content)).replace("\u00ad", "").split())


def check(row, doc):
    matches = doc.xpath("//tr[@id=$id]", id=row["locator"])
    if len(matches) != 1:
        return False
    candidate_row = matches[0]
    cells = candidate_row.xpath("./td|./th")
    if not cells or text(cells[0]) != row["section"]:
        return False
    headings = [text(cell) for cell in candidate_row.xpath("ancestor::table[1]//tr[1]/th")]
    by_candidate = {}
    for cell in candidate_row.xpath("./td[position()>1]"):
        position = sum(int(c.get("colspan", 1)) for c in cell.xpath("preceding-sibling::*"))
        if position >= headings.index("Others"):
            break
        if cell.get("colspan") is None and cell.get("rowspan") is None:
            party = PARTIES.get(headings[position], headings[position])
            by_candidate.setdefault(text(cell), set()).add(party)
    source, target = row["source_name"], row["target_name"]
    if row["relation"] == "NOMINATES_CANDIDATE":
        return (source in by_candidate.get(target, set()) and row["sign"] == "1"
                and row["symmetric"] == "False" and row["group"] == "support")
    if row["relation"] == "ELECTORAL_RIVAL":
        return (source != target and source in by_candidate and target in by_candidate
                and row["sign"] == "-1" and row["symmetric"] == "True" and row["group"] == "opposition")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("cache"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    doc = html.parse(str(args.cache / (ELECTION + ".html")))
    with (args.data / "audit_sample.csv").open(encoding="utf8", newline="") as file:
        rows = [row for row in csv.DictReader(file) if row["method"] == "table"]
    for row in rows:
        row["correct"] = int(check(row, doc))
        row["reviewer"] = "automatic source concordance"
        row["note"] = "Compared both endpoints, constituency and relation semantics against the pinned table"
    with (args.data / "audit_table_checked.csv").open("w", encoding="utf8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    correct = sum(r["correct"] for r in rows)
    summary = {"table_correct": correct, "table_sample": len(rows),
               "table_source_concordance": correct / len(rows),
               "table_wilson_lower_95": wilson_lower(correct, len(rows))}
    (args.data / "audit_stats.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf8")
    print(summary)


if __name__ == "__main__":
    main()
