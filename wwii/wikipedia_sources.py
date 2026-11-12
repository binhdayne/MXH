"""Load pinned Wikipedia pages and parse election result tables."""
import hashlib
import re
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


def us_contests(rows, table_index):
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


def commonwealth_contests(table, rows, table_index, country):
    caption = clean(table.xpath("./caption")[0]) if table.xpath("./caption") else ""
    headings = table.xpath("preceding::*[self::h2 or self::h3 or self::h4 or self::h5][1]")
    district = caption.strip(": ") if country == "UK" else (clean(headings[0]) if headings else "")
    if not district:
        return
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


def elections(document, country):
    """Yield contests in source order with their original table locators."""
    for table_index, table in enumerate(document.xpath('//table[contains(@class,"wikitable")]')):
        rows = table.xpath("./tr|./tbody/tr|./thead/tr")
        if not rows:
            continue
        header = [clean(cell) for cell in rows[0].xpath("./th|./td")]
        if country == "US" and header[:1] == ["District"] and "This race" in header:
            yield from us_contests(rows, table_index)
        elif country != "US" and header[:3] == ["Party", "Candidate", "Votes"]:
            yield from commonwealth_contests(table, rows, table_index, country)
