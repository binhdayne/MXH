"""Extract wartime electoral and diplomatic relations from English Wikipedia."""
import argparse
import csv
import hashlib
import itertools
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from lxml import html

BASE = "https://en.wikipedia.org"
PAGES = {
    **{f"{y}_United_States_House_of_Representatives_elections": ("US", y, revision)
       for y, revision in [(1940, 1373666290), (1942, 1374778891), (1944, 1378338999)]},
    "Constituency_election_results_in_the_1945_United_Kingdom_general_election": ("UK", 1945, 1358245139),
    "Results_of_the_1943_Australian_federal_election_(House_of_Representatives)": ("AU", 1943, 1295898814),
    "Results_of_the_1940_Australian_federal_election_(House_of_Representatives)": ("AU", 1940, 1375066816),
    "Atlantic_Charter": ("text", 1941, 1378671559),
    "Potsdam_Declaration": ("text", 1945, 1376260084),
    "Common_Wealth_Party": ("text", 1944, 1376653420),
    "Franklin_D._Roosevelt": ("text", 1941, 1384177333),
    "Charles_de_Gaulle": ("text", 1940, 1384394550),
    "Pierre_Laval": ("text", 1942, 1384345971),
}
CANDIDATE = re.compile(r"^(?P<name>.+?)\s*\((?P<party>[^()]+)\)\s*(?P<share>[\d.]+)\s*%$")
NON_PERSON = re.compile(r"^(?:all others|others?|write[- ]ins?|scattering|unknown|no candidate|blank votes?)\b", re.I)


def clean(element):
    return " ".join(element.text_content().replace("\u00ad", "").split())


def key(text):
    return re.sub(r"[\W_]+", "", text.casefold())


def digest(*values):
    return hashlib.sha256("\x1f".join(map(str, values)).encode()).hexdigest()[:24]


def load_page(title, revision, cache):
    path = cache / f"{title}.html"
    if not path.exists():
        endpoint = f"/w/rest.php/v1/revision/{revision}/html" if revision else f"/api/rest_v1/page/html/{title}"
        request = Request(BASE + endpoint, headers={"User-Agent": "WartimePoliticsGraph/1.0 (course research)"})
        with urlopen(request, timeout=45) as response:
            path.write_bytes(response.read())
    raw = path.read_bytes()
    document = html.fromstring(raw)
    match = re.search(r"/revision/(\d+)$", document.get("about", ""))
    if not match:
        match = re.search(rb'"wgRevisionId":\s*(\d+)', raw)
    if revision and (not match or int(match[1]) != revision):
        raise ValueError(f"Unexpected revision for {title}")
    for element in document.xpath('//script|//style|//sup[contains(@class,"reference")]|//span[contains(@style,"display:none")]'):
        element.drop_tree()
    source = f"{BASE}/wiki/Special:PermanentLink/{int(match[1])}" if match else f"{BASE}/wiki/{title}"
    return document, dict(title=title, url=source, sha256=hashlib.sha256(raw).hexdigest())


def link(element, name):
    for a in element.xpath(".//a[@href]"):
        href = unquote(urlsplit(a.get("href")).path)
        if not href.startswith(("./", "/wiki/")) or ":" in href:
            continue
        if key(clean(a)) == key(name):
            return href.removeprefix("./").removeprefix("/wiki/")
    return ""


def elections(doc, country):
    for table_index, table in enumerate(doc.xpath('//table[contains(@class,"wikitable")]')):
        rows = table.xpath("./tr|./tbody/tr|./thead/tr")
        if not rows:
            continue
        header = [clean(c) for c in rows[0].xpath("./th|./td")]
        if country == "US":
            if header[:1] != ["District"] or "This race" not in header:
                continue
            for row_index, row in enumerate(rows[2:], 2):
                cells = row.xpath("./th|./td")
                if len(cells) < 5 or cells[0].get("rowspan") or not cells[-1].xpath(".//li"):
                    continue
                district = clean(cells[0])
                if not district:
                    continue
                candidates = []
                entries = cells[-1].xpath(".//li")
                for entry in entries:
                    value = clean(entry).lstrip("▌ ").strip()
                    m = CANDIDATE.fullmatch(value)
                    if m and not NON_PERSON.match(m["name"]):
                        candidates.append((m["name"], m["party"], link(entry, m["name"]), value))
                winners = sum(bool(e.xpath('.//img[@alt="Green tick"]')) for e in entries)
                yield district, f"{table_index}:{row_index}", candidates, winners == 1 and "at-large" not in district.casefold()
        elif header[:3] == ["Party", "Candidate", "Votes"]:
            caption = clean(table.xpath("./caption")[0]) if table.xpath("./caption") else ""
            headings = table.xpath("preceding::*[self::h2 or self::h3 or self::h4 or self::h5][1]")
            district = caption.strip(": ") if country == "UK" else (clean(headings[0]) if headings else "")
            if not district:
                continue
            candidates = []
            for row in rows[1:]:
                cells = row.xpath("./td|./th")
                if cells and clean(cells[0]).casefold().startswith(("majority", "total formal votes", "two-party-preferred", "two-candidate-preferred")):
                    break
                if len(cells) != 6 or clean(cells[0]) or not re.fullmatch(r"[\d,]+", clean(cells[3])):
                    continue
                party, name = map(clean, cells[1:3])
                if name and party and not NON_PERSON.match(name):
                    candidates.append((name, party, link(cells[2], name), f"{party} | {name} | {clean(cells[3])}"))
            # Restrict British rival edges to territorial, single-seat tables.
            multi = any("university" in clean(h).casefold() for h in
                        table.xpath("ancestor::section/*[self::h2 or self::h3 or self::h4]"))
            multi |= any("first seat" in clean(r).casefold() or "second seat" in clean(r).casefold() for r in rows)
            yield district, str(table_index), candidates, not multi


PARTY_ALIAS = {
    ("UK", "commonwealth"): "Common Wealth",
    ("UK", "commonwealthparty"): "Common Wealth",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("cache"))
    parser.add_argument("--output", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.cache.mkdir(exist_ok=True, parents=True)
    args.output.mkdir(exist_ok=True, parents=True)
    nodes, edges, sources = {}, {}, {}
    contests = Counter()
    pending = []
    seen = set()
    titles_for_name = defaultdict(set)

    for title, (country, year, revision) in PAGES.items():
        doc, source = load_page(title, revision, args.cache)
        sources[title] = (doc, source)
        if country == "text":
            continue
        for district, locator, candidates, single in elections(doc, country):
            race = (country, year, key(district))
            if not candidates or race in seen:
                continue
            seen.add(race)
            contests[f"{country}-{year}"] += 1
            pending.append((race, district, locator, candidates, single, source))
            for name, _, article, _ in candidates:
                if article:
                    titles_for_name[country, key(name)].add(article)

    def node(kind, identity, name, country="", article=""):
        uid = digest(kind, *identity)
        nodes.setdefault(uid, dict(id=uid, kind=kind, name=name, country=country, wiki_title=article))
        return uid

    def party(country, name):
        name = PARTY_ALIAS.get((country, key(name)), name)
        return node("WartimeParty", (country, key(name)), name, country)

    def person(country, name, article="", district="", affiliation=""):
        aliases = titles_for_name[country, key(name)]
        article = article or (next(iter(aliases)) if len(aliases) == 1 else "")
        identity = (country, article) if article else (country, key(name), key(district), key(affiliation))
        return node("WartimePolitician", identity, name, country, article)

    def edge(kind, a, b, sign, year, event, source, locator, evidence, method, symmetric=False, section=""):
        if symmetric:
            a, b = sorted((a, b))
        if a == b:
            return
        uid = digest(kind, a, b, event)
        edges.setdefault(uid, dict(id=uid, source=a, target=b, relation=kind, sign=sign, year=year, event=event,
                                   wiki_url=source["url"], locator=locator, evidence=evidence, method=method,
                                   symmetric=symmetric, section=section))

    for (country, year, _), district, locator, candidates, single, source in pending:
        event = f"{country} {year} / {district}"
        slate = {}
        for name, affiliation, article, evidence in candidates:
            uid = person(country, name, article, district, affiliation)
            slate.setdefault(uid, evidence)
            if not affiliation.casefold().startswith(("independent", "nonpartisan", "no party", "write-in")):
                edge("NOMINATES_CANDIDATE", party(country, affiliation), uid, 1, year, event,
                     source, locator, evidence, "table")
        if single:
            for (a, ae), (b, be) in itertools.combinations(slate.items(), 2):
                edge("ELECTORAL_RIVAL", a, b, -1, year, event, source, locator, ae + " | " + be, "table", True)

    rules = [
        ("Atlantic_Charter", r"Roosevelt and British prime minister Winston Churchill discussed what would become the Atlantic Charter.*?joint declaration on 14 August 1941", [
            ("JOINT_DECLARATION", ("US","Franklin D. Roosevelt"), ("UK","Winston Churchill"), 1, 1941, True)]),
        ("Potsdam_Declaration", r"On July 26, 1945, United States president Harry S\. Truman.*?terms of surrender for the Empire of Japan", [
            ("DEMANDS_SURRENDER", ("US","United States"), ("JP","Empire of Japan"), -1, 1945, False),
            ("DEMANDS_SURRENDER", ("UK","United Kingdom"), ("JP","Empire of Japan"), -1, 1945, False),
            ("DEMANDS_SURRENDER", ("CN","Republic of China (Nationalist government)"), ("JP","Empire of Japan"), -1, 1945, False)]),
        ("Common_Wealth_Party", r"In April, John Eric Loverseed.*?In November 1944, he left the party and joined Labour in May of the next year", [
            ("LEAVES_PARTY", ("UK","John Eric Loverseed"), ("UK","Common Wealth"), -1, 1944, False),
            ("JOINS_PARTY_AFTER_SWITCH", ("UK","John Eric Loverseed"), ("UK","Labour"), 1, 1945, False)]),
        ("Franklin_D._Roosevelt", r"Roosevelt won Congressional approval of the Lend-Lease program, which directed massive military and economic aid to Britain and China", [
            ("DIRECTED_AID_TO", ("US","United States"), ("UK","United Kingdom"), 1, 1941, False),
            ("DIRECTED_AID_TO", ("US","United States"), ("CN","Republic of China (Nationalist government)"), 1, 1941, False)]),
        ("Charles_de_Gaulle", r"De Gaulle.s Appeal of 18 June exhorted the French people not to be demoralized and to continue to resist occupation", [
            ("CALLED_FOR_RESISTANCE_AGAINST", ("FR","Charles de Gaulle"), ("DE","Nazi Germany"), -1, 1940, False)]),
        ("Pierre_Laval", r"radio speech on 22 June 1942.*?wished for a German victory", [
            ("EXPRESSED_SUPPORT_FOR", ("FR","Pierre Laval"), ("DE","Nazi Germany"), 1, 1942, False)]),
    ]
    for title, pattern, relations in rules:
        doc, source = sources[title]
        match = next(((p, m) for p in doc.xpath("//p") if (m := re.search(pattern, clean(p), re.I))), None)
        if match is None:
            raise ValueError(f"No evidence matched for {title}")
        paragraph, span = match
        for relation, start, end, sign, year, symmetric in relations:
            # Stable historical names also appear in the curated diplomatic seed.
            if relation in {"DEMANDS_SURRENDER", "DIRECTED_AID_TO"}:
                a = node("WartimeGovernment", (start[1],), start[1], start[0])
            else:
                a = person(*start)
            if relation in {"LEAVES_PARTY", "JOINS_PARTY_AFTER_SWITCH"}:
                b = party(*end)
            elif symmetric:
                b = person(*end)
            else:
                b = node("WartimeGovernment", (end[1],), end[1], end[0])
            event = "John Eric Loverseed party transition" if title == "Common_Wealth_Party" else title.replace("_", " ")
            headings = paragraph.xpath("preceding::*[self::h2 or self::h3 or self::h4 or self::h5][1]")
            section = clean(headings[0]) if headings else "Lead"
            edge(relation, a, b, sign, year, event, source, paragraph.get("id", ""), span[0], "nlp", symmetric, section)

    def csv_output(name, rows):
        with (args.output / name).open("w", encoding="utf8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    csv_output("nodes.csv", list(nodes.values()))
    csv_output("edges.csv", list(edges.values()))
    rng = random.Random(19450902)
    sample = []
    for relation in ("NOMINATES_CANDIDATE", "ELECTORAL_RIVAL"):
        pool = [e for e in edges.values() if e["relation"] == relation]
        sample.extend(rng.sample(pool, min(100, len(pool))))
    sample.extend(e for e in edges.values() if e["method"] == "nlp")
    csv_output("audit_sample.csv", [dict(e, source_name=nodes[e["source"]]["name"], target_name=nodes[e["target"]]["name"],
                                             review="", notes="") for e in sample])
    stats = dict(nodes=len(nodes), edges=len(edges), node_types=dict(Counter(n["kind"] for n in nodes.values())),
                 edge_types=dict(Counter(e["relation"] for e in edges.values())), contests=dict(contests),
                 signs=dict(Counter(e["sign"] for e in edges.values())))
    (args.output / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf8")
    (args.output / "sources.json").write_text(json.dumps([s for _, s in sources.values()], indent=2) + "\n", encoding="utf8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

