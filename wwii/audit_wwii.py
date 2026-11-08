"""Audit a stratified sample against the original Wikipedia HTML."""
import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from lxml import html


def read_rows(path):
    with path.open(encoding="utf8", newline="") as file:
        return list(csv.DictReader(file))


def text(element):
    parts = element.xpath('.//text()[not(ancestor::sup[contains(@class,"reference")]) and not(ancestor::span[contains(@style,"display:none")]) and not(ancestor::style)]')
    return " ".join("".join(parts).replace("\u00ad", "").split())


def normalized(value):
    return re.sub(r"[\W_]+", "", value.casefold())


def candidate_evidence(row, doc):
    parts = [int(value) for value in row["locator"].split(":")]
    table = doc.xpath('//table[contains(@class,"wikitable")]')[parts[0]]
    rows = table.xpath("./tr|./tbody/tr|./thead/tr")
    if len(parts) == 2:
        cells = rows[parts[1]].xpath("./td|./th")
        lines = [text(li).lstrip("▌ ").strip() for li in cells[-1].xpath(".//li")]
        district = text(cells[0])
        eligible = sum(bool(li.xpath('.//img[@alt="Green tick"]')) for li in cells[-1].xpath(".//li")) == 1
    else:
        lines = []
        caption = table.xpath("./caption")
        headings = table.xpath("preceding::*[self::h2 or self::h3 or self::h4 or self::h5][1]")
        district = text(caption[0]).strip(": ") if row["event"].startswith("UK ") and caption else text(headings[0])
        for tr in rows[1:]:
            cells = tr.xpath("./td|./th")
            if cells and text(cells[0]).casefold().startswith(("majority", "total formal votes", "two-party-preferred", "two-candidate-preferred")):
                break
            if len(cells) == 6 and not text(cells[0]) and re.fullmatch(r"[\d,]+", text(cells[3])):
                lines.append(" | ".join(text(c) for c in cells[1:4]))
        eligible = True
    if district != row["event"].split(" / ", 1)[1]:
        return False
    if row["relation"] == "NOMINATES_CANDIDATE":
        evidence = row["evidence"]
        if evidence not in lines or row["sign"] != "1" or row["symmetric"] != "False":
            return False
        if len(parts) == 2:
            extracted = re.fullmatch(r"(.+)\s*\(([^()]+)\)\s*[\d.]+\s*%", evidence)
            if not extracted:
                return False
            name, party = extracted.groups()
        else:
            party, name, _ = evidence.split(" | ")
        party_aliases = {"commonwealthparty": "commonwealth"}
        party_id = normalized(party)
        return (party_aliases.get(party_id, party_id) == normalized(row["source_name"])
                and normalized(name) == normalized(row["target_name"]))
    if row["sign"] != "-1" or row["symmetric"] != "True" or not eligible:
        return False
    if len(parts) == 2:
        values = [row["evidence"].split(" | ")[i] for i in (0, 1)]
        names = [re.sub(r"\s*\([^()]+\)\s*[\d.]+\s*%$", "", value) for value in values]
    else:
        pieces = row["evidence"].split(" | ")
        values = [" | ".join(pieces[:3]), " | ".join(pieces[3:])]
        names = [pieces[1], pieces[4]]
    return (all(v in lines for v in values)
            and set(map(normalized, names)) == {normalized(row["source_name"]), normalized(row["target_name"])})


def wilson_lower(correct, total):
    p, z = correct / total, 1.959963984540054
    return (p + z*z/(2*total) - z*math.sqrt(p*(1-p)/total + z*z/(4*total*total))) / (1 + z*z/total)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("cache"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    sources = json.loads((args.data/"sources.json").read_text(encoding="utf8"))
    docs = {s["url"]: html.fromstring((args.cache/(s["title"]+".html")).read_bytes()) for s in sources}
    rows = read_rows(args.data/"audit_sample.csv")
    counts = {}
    for row in rows:
        doc = docs[row["wiki_url"]]
        if row["method"] == "table":
            ok = candidate_evidence(row, doc)
            row["review"] = "source_match" if ok else "review_required"
            tally = counts.setdefault(row["relation"], Counter())
            tally["sample"] += 1
            tally["matched"] += int(ok)
        else:
            p = doc.xpath("//p[@id=$id]", id=row["locator"])
            ok = bool(p and row["evidence"] in text(p[0]))
            row["review"] = "evidence_located" if ok else "review_required"
    for tally in counts.values():
        tally["wilson_lower_95"] = wilson_lower(tally["matched"], tally["sample"])
    with (args.data/"audit_checked.csv").open("w", encoding="utf8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.data/"audit_stats.json").write_text(json.dumps(counts, indent=2)+"\n", encoding="utf8")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
