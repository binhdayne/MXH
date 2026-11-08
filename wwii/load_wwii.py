"""Load the WWII graph into Neo4j through its transactional HTTP endpoint."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

NODE_KINDS = {"WartimePolitician", "WartimeParty", "WartimeGovernment"}
RELATIONS = {"ELECTORAL_RIVAL", "NOMINATES_CANDIDATE", "JOINT_DECLARATION",
             "DEMANDS_SURRENDER", "LEAVES_PARTY", "JOINS_PARTY_AFTER_SWITCH",
             "DIRECTED_AID_TO", "CALLED_FOR_RESISTANCE_AGAINST", "EXPRESSED_SUPPORT_FOR"}
HISTORICAL_NAMES = {"Franklin D. Roosevelt", "Winston Churchill", "John Eric Loverseed"}


def read_csv(path):
    with path.open(encoding="utf8", newline="") as file:
        return list(csv.DictReader(file))


def query(url, statements):
    request = Request(url, data=json.dumps({"statements": statements}).encode(),
                      headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=90) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"Neo4j HTTP {error.code}: {error.read().decode()[:1000]}") from error
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    return result


def statement(cypher, **parameters):
    return {"statement": cypher, "parameters": parameters}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", default="http://127.0.0.1:17474")
    parser.add_argument("--database", default="neo4j")
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()
    endpoint = f"{args.http.rstrip('/')}/db/{args.database}/tx/commit"
    seed = Path(__file__).with_name("diplomacy_seed.cypher").read_text(encoding="utf8")
    statements = [statement(s.strip()) for s in seed.split(";") if s.strip() and "RETURN" not in s]
    nodes = defaultdict(list)
    edges = defaultdict(list)
    for row in read_csv(args.data/"nodes.csv"):
        kind = row.pop("kind")
        if kind not in NODE_KINDS:
            raise ValueError(kind)
        nodes[kind].append(row)
    for row in read_csv(args.data/"edges.csv"):
        relation = row.pop("relation")
        if relation not in RELATIONS:
            raise ValueError(relation)
        for column in ("sign", "year"):
            row[column] = int(row[column])
        row["symmetric"] = row["symmetric"] == "True"
        row["category"] = ("switch" if relation in {"LEAVES_PARTY", "JOINS_PARTY_AFTER_SWITCH"}
                           else "support" if row["sign"] == 1 else "opposition")
        edges[relation].append(row)
    for label, records in nodes.items():
        if label == "WartimeGovernment":
            cypher = f"UNWIND $rows AS row MERGE (n:WWII:{label} {{name:row.name}}) SET n += row"
            statements.append(statement(cypher, rows=records))
            continue
        if label == "WartimePolitician":
            historical = [r for r in records if r["name"] in HISTORICAL_NAMES]
            records = [r for r in records if r["name"] not in HISTORICAL_NAMES]
            cypher = f"UNWIND $rows AS row MERGE (n:WWII:{label} {{name:row.name}}) SET n += row"
            statements.append(statement(cypher, rows=historical))
        cypher = f"UNWIND $rows AS row MERGE (n:WWII:{label} {{id:row.id}}) SET n += row"
        statements.append(statement(cypher, rows=records))
    for relation, records in edges.items():
        cypher = f"""
        UNWIND $rows AS row
        MATCH (a:WWII {{id:row.source}}), (b:WWII {{id:row.target}})
        MERGE (a)-[r:{relation} {{id:row.id}}]->(b)
        SET r += row
        """
        statements.append(statement(cypher, rows=records))
    statements.append(statement("""
        MATCH (:WWII)-[r]->(:WWII) WHERE r.method IS NULL
        SET r.method='manual', r.category=CASE r.sign WHEN 1 THEN 'support' WHEN -1 THEN 'opposition' ELSE 'context' END
        """))
    query(endpoint, statements)
    results = query(endpoint, [
        statement("MATCH (n:WWII) RETURN elementId(n), head([l IN labels(n) WHERE l <> 'WWII'])"),
        statement("MATCH (a:WWII)-[r]->(b:WWII) RETURN elementId(a), elementId(b), type(r), r.sign, r.method, r.category"),
    ])["results"]
    vertex = [item["row"] for item in results[0]["data"]]
    links = [item["row"] for item in results[1]["data"]]
    expected_edges = sum(map(len, edges.values()))
    observed_edges = sum(e[4] != "manual" for e in links)
    if expected_edges != observed_edges:
        raise RuntimeError(f"Expected {expected_edges} generated edges, found {observed_edges}.")
    neighbors = defaultdict(set)
    for a,b,*_ in links:
        neighbors[a].add(b)
        neighbors[b].add(a)
    unseen = {uid for uid,_ in vertex}
    components = []
    while unseen:
        stack = [unseen.pop()]
        count = 0
        while stack:
            current = stack.pop()
            count += 1
            newly_seen = neighbors[current] & unseen
            unseen.difference_update(newly_seen)
            stack.extend(newly_seen)
        components.append(count)
    stats = dict(nodes=len(vertex), edges=len(links), node_types=dict(Counter(v[1] for v in vertex)),
                 edge_types=dict(Counter(e[2] for e in links)), methods=dict(Counter(e[4] for e in links)),
                 signs=dict(Counter(str(e[3]) if e[3] is not None else "neutral" for e in links)),
                 categories=dict(Counter(e[5] for e in links)),
                 signed_types=len({e[2] for e in links if e[3] is not None}),
                 components=len(components), largest_components=sorted(components, reverse=True)[:5])
    (args.data/"neo4j_stats.json").write_text(json.dumps(stats, indent=2)+"\n", encoding="utf8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
