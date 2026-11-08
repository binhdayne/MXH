"""Build a provenance-aware signed graph from English Wikipedia."""
import argparse
import csv
import hashlib
import itertools
import json
import random
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen

from lxml import html

ELECTION = "Candidates_of_the_2024_United_Kingdom_general_election_by_constituency"
PAGES = {
    ELECTION: 1384310509,
    "Christian_Wakeford": 1378241693,
    "Boris_Johnson": 1383452931,
    "Conservative–DUP_agreement": 1359130405,
    "Conservative–Liberal_Democrat_coalition_agreement": 1382141901,
    "2019_Conservative_Party_leadership_election": 1374974501,
}
BASE = "https://en.wikipedia.org"
PARTIES = {
    "Conservative": "Conservative Party",
    "Labour": "Labour Party",
    "DUP": "Democratic Unionist Party",
    "Alliance": "Alliance Party of Northern Ireland",
    "UUP": "Ulster Unionist Party",
    "SDLP": "Social Democratic and Labour Party",
    "TUV": "Traditional Unionist Voice",
    "Green": "Green Party Northern Ireland",
    "Green Party": "Green Party of England and Wales",
    "Scottish Greens": "Scottish Green Party",
    "SNP": "Scottish National Party",
    "Yorkshire": "Yorkshire Party",
    "SDP": "Social Democratic Party (UK, 1990)",
    "Workers": "Workers Party of Britain",
}
TYPES = {
    "NOMINATES_CANDIDATE": ("support", 1, False),
    "ELECTORAL_RIVAL": ("opposition", -1, True),
    "LEADERSHIP_RIVAL": ("opposition", -1, True),
    "COALITION_WITH": ("support", 1, True),
    "CONFIDENCE_SUPPORT": ("support", 1, False),
    "PLEDGES_MILITARY_AID": ("support", 1, False),
    "IMPOSES_SANCTIONS": ("opposition", -1, False),
    "SUBMITS_NO_CONFIDENCE": ("opposition", -1, False),
    "LEAVES_PARTY": ("switch", -1, False),
    "JOINS_PARTY_AFTER_SWITCH": ("switch", 1, False),
}
NLP_RULES = [
    ("Christian_Wakeford", "Political career", "SUBMITS_NO_CONFIDENCE",
     r"Wakeford publicly confirmed that he had submitted a letter of no confidence in Johnson",
     ("Person", "Christian Wakeford"), ("Person", "Boris Johnson"), "2022-01-19", "wakeford-confidence"),
    ("Christian_Wakeford", "Political career", "LEAVES_PARTY",
     r"Wakeford had joined the Labour Party.*?first sitting Conservative MP to defect to Labour",
     ("Person", "Christian Wakeford"), ("Party", "Conservative Party"), "2022-01-19", "wakeford-switch"),
    ("Christian_Wakeford", "Political career", "JOINS_PARTY_AFTER_SWITCH",
     r"Wakeford had joined the Labour Party.*?first sitting Conservative MP to defect to Labour",
     ("Person", "Christian Wakeford"), ("Party", "Labour Party"), "2022-01-19", "wakeford-switch"),
    ("Boris_Johnson", "Foreign policy", "PLEDGES_MILITARY_AID",
     r"He pledged an extra £300m in military aid to Ukraine",
     ("Government", "Boris Johnson ministry"), ("Government", "Government of Ukraine (2022)"), "2022-05-03", "ukraine-aid"),
    ("Boris_Johnson", "Lead", "IMPOSES_SANCTIONS",
     r"Russian invasion of Ukraine by imposing sanctions on Russia",
     ("Government", "Boris Johnson ministry"), ("Government", "Government of Russia (2022)"), "2022", "russia-sanctions"),
    ("Conservative–DUP_agreement", "Lead", "CONFIDENCE_SUPPORT",
     r"secured DUP Confidence and supply support for a Conservative minority government led by Theresa May",
     ("Party", "Democratic Unionist Party"), ("Government", "Second May ministry"), "2017-06-26", "dup-agreement"),
    ("Conservative–Liberal_Democrat_coalition_agreement", "Lead", "COALITION_WITH",
     r"coalition government comprising MPs from the Conservative Party and the Liberal Democrats",
     ("Party", "Conservative Party"), ("Party", "Liberal Democrats"), "2010-05-11", "cameron-clegg"),
    ("2019_Conservative_Party_leadership_election", "Lead", "LEADERSHIP_RIVAL",
     r"Boris Johnson being elected with more than twice as many votes as his opponent Jeremy Hunt",
     ("Person", "Boris Johnson"), ("Person", "Jeremy Hunt"), "2019-07-23", "con-leadership-final"),
]


def clean(text):
    return " ".join(unicodedata.normalize("NFC", text).replace("\u00ad", "").split())


def clean_page(document):
    for element in document.xpath('//style|//script|//sup[contains(@class,"reference")]'):
        element.drop_tree()


def identifier(*parts):
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]


def load_page(title, cache):
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / (title + ".html")
    pinned = PAGES[title]
    if not target.exists():
        api = "https://en.wikipedia.org/w/rest.php/v1"
        routes = ([f"{api}/revision/{pinned}/html"] if pinned else []) + [
            f"{BASE}/api/rest_v1/page/html/{quote(title)}"]
        for url in routes:
            request = Request(url, headers={"User-Agent": "WikiPoliticalGraphCourse/1.0 (academic project)"})
            try:
                with urlopen(request, timeout=45) as response:
                    data = response.read()
                break
            except HTTPError as error:
                if error.code == 429:
                    time.sleep(3)
                if url == routes[-1]:
                    raise
        target.write_bytes(data)
        time.sleep(1)
    raw = target.read_bytes()
    document = html.fromstring(raw)
    revision = re.search(r"/revision/(\d+)$", document.get("about", ""))
    if not revision:
        raise ValueError(f"No revision metadata for {title}")
    number = int(revision[1])
    if pinned and number != pinned:
        raise ValueError(f"Expected revision {pinned} for {title}, got {number}")
    clean_page(document)
    return document, {"title": title, "revision": number, "url": f"{BASE}/wiki/Special:PermanentLink/{number}",
                      "sha256_html": hashlib.sha256(raw).hexdigest()}


def article_link(element):
    for link in element.xpath(".//a[@href]"):
        href = link.get("href")
        if href.startswith("./"):
            path = unquote(urlsplit(href).path[2:])
            if ":" not in path and path:
                return path.replace(" ", "_")
    return ""


class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def node(self, kind, name, key=None, wiki="", constituency=""):
        uid = kind.lower() + ":" + identifier(key or name.casefold())
        if uid not in self.nodes:
            self.nodes[uid] = dict(id=uid, kind=kind, name=name, wiki_title=wiki, constituency=constituency)
        return uid

    def relation(self, a, b, relation, event, date, source, section, locator, evidence, method):
        group, sign, symmetric = TYPES[relation]
        if a == b:
            raise ValueError(f"Self-edge in {event}")
        if symmetric:
            a, b = sorted((a, b))
        uid = identifier(a, b, relation, event)
        if uid not in self.edges:
            self.edges[uid] = dict(id=uid, source=a, target=b, relation=relation, group=group, sign=sign,
                                   symmetric=symmetric, event_id=event, date=date, method=method,
                                   revision=source["revision"], wiki_url=source["url"], section=section,
                                   locator=locator, evidence=evidence)


def election_edges(graph, document, source):
    seen = set()
    excluded = Counter()
    for table in document.xpath("//table"):
        rows = table.xpath("./tr|./thead/tr|./tbody/tr")
        if not rows:
            continue
        headings = [clean(cell.text_content()) for cell in rows[0].xpath("./th")]
        if not headings or not headings[0].startswith("Constituency") or "Others" not in headings:
            continue
        for row in rows[1:]:
            cells = row.xpath("./td|./th")
            if not row.xpath("./td") or not cells:
                continue
            constituency = clean(cells[0].text_content())
            if not constituency and len(cells) == 3:
                continue
            if not constituency or constituency in seen:
                raise ValueError(f"Missing or repeated constituency: {constituency!r}")
            seen.add(constituency)
            event = "uk-ge-2024:" + identifier(constituency)
            candidates = {}
            column = 0
            for cell in cells:
                width = int(cell.get("colspan", 1))
                if 0 < column < headings.index("Others"):
                    name = clean(cell.text_content())
                    if width != 1 or cell.get("rowspan"):
                        excluded["spanning cell"] += 1
                    elif name and name.casefold() not in {"not contesting", "-", "–", "—", "n/a"}:
                        if cell.xpath(".//li|.//br") or len(name.split()) < 2:
                            excluded["ambiguous candidate cell"] += 1
                        else:
                            party = PARTIES.get(headings[column], headings[column])
                            wiki = article_link(cell)
                            key = wiki or f"{event}:{name}"
                            uid = graph.node("Person", name, key=key, wiki=wiki, constituency=constituency)
                            if uid in candidates:
                                raise ValueError(f"Duplicate candidate in {constituency}: {name}")
                            candidates[uid] = (name, party)
                            pid = graph.node("Party", party)
                            graph.relation(pid, uid, "NOMINATES_CANDIDATE", event, "2024-07-04",
                                           source, constituency, row.get("id", ""), f"{party} | {name}", "table")
                column += width
            for (a, (first, _)), (b, (second, _)) in itertools.combinations(candidates.items(), 2):
                graph.relation(a, b, "ELECTORAL_RIVAL", event, "2024-07-04",
                               source, constituency, row.get("id", ""), f"{first} | {second}", "table")
    return len(seen), dict(excluded)


def section_name(paragraph):
    headings = paragraph.xpath("ancestor::section/*[self::h2 or self::h3 or self::h4 or self::h5]")
    return " / ".join(clean(h.text_content()) for h in headings) or "Lead"


def nlp_edges(graph, sources):
    for title, scope, relation, pattern, start, end, date, event in NLP_RULES:
        document, source = sources[title]
        for paragraph in document.xpath("//section/p"):
            section = section_name(paragraph)
            if scope not in section.split(" / "):
                continue
            match = re.search(pattern, clean(paragraph.text_content()), re.I)
            if not match:
                continue
            def resolve(entity):
                kind, name = entity
                wiki = name.replace(" ", "_") if kind == "Person" else ""
                return graph.node(kind, name, key=wiki or None, wiki=wiki)
            graph.relation(resolve(start), resolve(end), relation, event, date, source, section,
                           paragraph.get("id", ""), match[0], "nlp")
            break
        else:
            raise ValueError(f"Unmatched text rule: {title}, {relation}")


def write_rows(path, rows, names=None):
    rows = list(rows)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=names or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(graph, constituency_count, exclusions):
    adjacent = defaultdict(set)
    signed_degree = defaultdict(Counter)
    for edge in graph.edges.values():
        a, b = edge["source"], edge["target"]
        adjacent[a].add(b)
        adjacent[b].add(a)
        signed_degree[a][edge["sign"]] += 1
        signed_degree[b][edge["sign"]] += 1
    remaining = set(graph.nodes)
    sizes = []
    while remaining:
        queue = [remaining.pop()]
        size = 0
        while queue:
            node = queue.pop()
            size += 1
            for neighbor in adjacent[node] & remaining:
                remaining.remove(neighbor)
                queue.append(neighbor)
        sizes.append(size)
    return {
        "nodes": len(graph.nodes), "edges": len(graph.edges), "constituencies_seen": constituency_count,
        "node_types": dict(Counter(n["kind"] for n in graph.nodes.values())),
        "edge_types": dict(Counter(e["relation"] for e in graph.edges.values())),
        "signs": dict(Counter(e["sign"] for e in graph.edges.values())),
        "methods": dict(Counter(e["method"] for e in graph.edges.values())),
        "groups": dict(Counter(e["group"] for e in graph.edges.values())),
        "exclusions": exclusions, "wcc_sizes": sorted(sizes, reverse=True),
        "top_degree": [{"name": graph.nodes[n]["name"], "positive": d[1], "negative": d[-1]}
                       for n, d in sorted(signed_degree.items(), key=lambda pair: (-pair[1].total(), pair[0]))[:10]],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path("cache"))
    parser.add_argument("--output", type=Path, default=Path("data"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sources = {title: load_page(title, args.cache) for title in PAGES}
    graph = Graph()
    count, exclusions = election_edges(graph, *sources[ELECTION])
    nlp_edges(graph, sources)
    stats = summarize(graph, count, exclusions)
    write_rows(args.output / "nodes.csv", graph.nodes.values())
    write_rows(args.output / "edges.csv", graph.edges.values())
    rng = random.Random(20241108)
    by_method = {method: sorted((e for e in graph.edges.values() if e["method"] == method),
                                key=lambda e: e["id"]) for method in ("nlp", "table")}
    sample = by_method["nlp"] + rng.sample(by_method["table"], min(150, len(by_method["table"])))
    write_rows(args.output / "audit_sample.csv", [
        dict(e, source_name=graph.nodes[e["source"]]["name"], target_name=graph.nodes[e["target"]]["name"],
             correct="", reviewer="", note="") for e in sample])
    for filename, value in (("stats.json", stats), ("sources.json", [s[1] for s in sources.values()])):
        (args.output / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


