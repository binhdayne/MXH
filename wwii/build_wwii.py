"""Extract wartime electoral and diplomatic relations from English Wikipedia."""
import argparse
import hashlib
import itertools
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from graph_io import write_json, write_rows
from wikipedia_sources import PAGES, clean, elections, key, load_page


def digest(*values):
    return hashlib.sha256("\x1f".join(map(str, values)).encode()).hexdigest()[:24]


PARTY_ALIAS = {
    ("UK", "commonwealth"): "Common Wealth",
    ("UK", "commonwealthparty"): "Common Wealth",
}

TEXT_RULES = [
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


def build_graph(cache):
    """Build stable node and edge records from the cached source pages."""
    nodes, edges, sources = {}, {}, {}
    contests = Counter()
    pending = []
    seen = set()
    titles_for_name = defaultdict(set)

    for title, (country, year, revision) in PAGES.items():
        doc, source = load_page(title, revision, cache)
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

    for title, pattern, relations in TEXT_RULES:
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

    return nodes, edges, sources, contests


def sample_edges(nodes, edges):
    rng = random.Random(19450902)
    sample = []
    for relation in ("NOMINATES_CANDIDATE", "ELECTORAL_RIVAL"):
        pool = [e for e in edges.values() if e["relation"] == relation]
        sample.extend(rng.sample(pool, min(100, len(pool))))
    sample.extend(e for e in edges.values() if e["method"] == "nlp")
    return [
        dict(edge, source_name=nodes[edge["source"]]["name"],
             target_name=nodes[edge["target"]]["name"], review="", notes="")
        for edge in sample
    ]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("cache"))
    parser.add_argument("--output", type=Path, default=Path("data"))
    return parser.parse_args()


def main():
    args = parse_args()
    args.cache.mkdir(exist_ok=True, parents=True)
    args.output.mkdir(exist_ok=True, parents=True)
    nodes, edges, sources, contests = build_graph(args.cache)
    write_rows(args.output / "nodes.csv", list(nodes.values()))
    write_rows(args.output / "edges.csv", list(edges.values()))
    write_rows(args.output / "audit_sample.csv", sample_edges(nodes, edges))
    stats = dict(nodes=len(nodes), edges=len(edges), node_types=dict(Counter(n["kind"] for n in nodes.values())),
                 edge_types=dict(Counter(e["relation"] for e in edges.values())), contests=dict(contests),
                 signs=dict(Counter(e["sign"] for e in edges.values())))
    write_json(args.output / "stats.json", stats)
    write_json(args.output / "sources.json", [source for _, source in sources.values()])
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
